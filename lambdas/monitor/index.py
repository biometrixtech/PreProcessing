from functools import wraps
import boto3
import datetime
import itertools
import os
import re

_cloudwatch_client = boto3.client('cloudwatch')
_batch_client = boto3.client('batch')
_ec2_client = boto3.client('ec2')
_ecs_client = boto3.client('ecs')
_efs_client = boto3.client('efs')
_sfn_client = boto3.client('stepfunctions')


def ignore_errors(f):
    """
    Invoke a function, catching and ignoring all errors
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except Exception as e:
            print(e)
    return wrapper


def handler(_, __):
    do_batch_desired_cpu()
    do_batch_actual_cpu()
    do_batch_job_counts()
    do_efs_filesystem_size()
    do_sfn_execution_counts()


@ignore_errors
def do_batch_desired_cpu():
    batch_desired_vcpus = _batch_client.describe_compute_environments(computeEnvironments=[os.environ['BATCH_COMPUTE_ENVIRONMENT']])[
        'computeEnvironments'][0]['computeResources']['desiredvCpus']
    _put_metric('BatchComputeEnvironmentDesiredCpus', batch_desired_vcpus)


@ignore_errors
def do_batch_actual_cpu():
        container_instance_arns = [arn for arn in _ecs_client.list_container_instances(cluster=os.environ['BATCH_ECS_CLUSTER'])['containerInstanceArns']]

        if len(container_instance_arns):
            ec2_instances = [instance['ec2InstanceId'] for instance in
                             _ecs_client.describe_container_instances(cluster=os.environ['BATCH_ECS_CLUSTER'],
                                                                      containerInstances=container_instance_arns)[
                                 'containerInstances']]
            data = _ec2_client.describe_instances(
                InstanceIds=ec2_instances,
                Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
            )['Reservations']

            instance_type_cpus = {
                r'c4\.8xlarge': 36,
                r"m4\.10xlarge": 40,
                r'..\.32xlarge': 128,
                r'..\.16xlarge': 64,
                r'..\.8xlarge': 32,
                r'..\.4xlarge': 16,
                r'..\.2xlarge': 8,
                r'..\.xlarge': 4,
                r'..\.large': 2,
                r'..\.medium': 1,
            }

            def get_cpu(t):
                for r, v in instance_type_cpus.items():
                    if re.match(r, t):
                        return v

            batch_actual_cpus = sum([get_cpu(instance['InstanceType']) for reservation in data for instance in reservation['Instances']])
        else:
            batch_actual_cpus = 0
        _put_metric('BatchComputeEnvironmentActualCpus', batch_actual_cpus)


@ignore_errors
def do_batch_job_counts():
    for group, statuses in {'SCHEDULED': ['SUBMITTED', 'PENDING', 'RUNNABLE', 'STARTING'], 'RUNNING': ['RUNNING'],
                            'SUCCEEDED': ['SUCCEEDED'], 'FAILED': ['FAILED']}.items():
        group_jobs = []
        for status in statuses:
            jobs = _batch_jobs_by_job(status)
            _put_metric('BatchJobQueueCount', len(jobs), {'Status': status})
            group_jobs += jobs
        for job_name, jobs in itertools.groupby(sorted(group_jobs)):
            _put_metric('BatchJobQueueCount', len(list(jobs)), {'Status': group, 'Job': job_name})


@ignore_errors
def do_efs_filesystem_size():
    data = _efs_client.describe_file_systems(FileSystemId=os.environ['BATCH_EFS_ID'])['FileSystems'][0]
    _put_metric('BatchEfsSize', data['SizeInBytes']['Value'], unit='Bytes')


@ignore_errors
def do_sfn_execution_counts():
    executions = [ex['status'] for ex in _list_sfn_executions() if ex['status'] == 'RUNNING' or (
            datetime.datetime.now() - ex['stopDate'].replace(tzinfo=None)).total_seconds() < 60 * 5]
    for status in ['RUNNING', 'SUCCEEDED', 'FAILED', 'TIMED_OUT', 'ABORTED']:
        _put_metric('StepFunctionsExecutions', executions.count(status), {'Status': status})


def _batch_jobs_by_job(status, token=''):
    jobs = _batch_client.list_jobs(jobQueue=os.environ['BATCH_JOB_QUEUE'], jobStatus=status, nextToken=token)
    return [job['jobName'].split('-')[4] for job in jobs['jobSummaryList']] + (
        _batch_jobs_by_job(status, jobs['nextToken']) if 'nextToken' in jobs and jobs['nextToken'] else [])


def _list_sfn_executions(token=None):
    if token is not None:
        res = _sfn_client.list_executions(stateMachineArn=os.environ['STATE_MACHINE_ARN'], nextToken=token)
    else:
        res = _sfn_client.list_executions(stateMachineArn=os.environ['STATE_MACHINE_ARN'])
    return res['executions'] + (
        _list_sfn_executions(res['nextToken']) if 'nextToken' in res and res['nextToken'] else [])


def _put_metric(metric_name, value, dimensions={}, unit='None'):
    dimensions = {**{'Environment': os.environ['ENVIRONMENT']}, **dimensions}
    _cloudwatch_client.put_metric_data(
        Namespace='Preprocessing',
        MetricData=[{
            'MetricName': metric_name,
            'Dimensions': [{'Name': k, 'Value': v} for k, v in dimensions.items()],
            'Timestamp': datetime.datetime.utcnow(),
            'Value': value,
            'Unit': unit
        }]
    )
