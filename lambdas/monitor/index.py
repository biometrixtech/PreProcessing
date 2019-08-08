from functools import wraps
import boto3
import datetime
import itertools
import os
import re
import time

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


def handler(_, context):
    global should_run_again
    should_run_again = True

    while context.get_remaining_time_in_millis() > 12 * 1000 and should_run_again:
        print(context.get_remaining_time_in_millis())
        do_batch_desired_cpu()
        do_batch_actual_cpu()
        do_batch_job_counts()
        do_efs_filesystem_size()
        do_sfn_execution_counts()
        time.sleep((context.get_remaining_time_in_millis() % 10000 - 100) / 1000)


@ignore_errors
def do_batch_desired_cpu():
    batch_desired_vcpus = _batch_client.describe_compute_environments(computeEnvironments=[os.environ['BATCH_COMPUTE_ENVIRONMENT']])[
        'computeEnvironments'][0]['computeResources']['desiredvCpus']
    _put_metric('BatchComputeEnvironmentDesiredCpus', batch_desired_vcpus)


@ignore_errors
def do_batch_actual_cpu():
    container_instance_arns = [arn for arn in _ecs_client.list_container_instances(cluster=os.environ['BATCH_ECS_CLUSTER_ARN'])['containerInstanceArns']]

    if len(container_instance_arns):
        container_instances = _ecs_client.describe_container_instances(
            cluster=os.environ['BATCH_ECS_CLUSTER_ARN'],
            containerInstances=container_instance_arns
        )['containerInstances']

        data = _ec2_client.describe_instances(
            InstanceIds=[instance['ec2InstanceId'] for instance in container_instances],
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

        batch_actual_cpus = sum(
            [get_cpu(instance['InstanceType']) for reservation in data for instance in reservation['Instances']])
    else:
        batch_actual_cpus = 0
    _put_metric('BatchComputeEnvironmentActualCpus', batch_actual_cpus)


@ignore_errors
def do_batch_job_counts():
    status_groups = {
        'SCHEDULED': ['SUBMITTED', 'PENDING', 'RUNNABLE', 'STARTING'],
        'RUNNING': ['RUNNING'],
        'SUCCEEDED': ['SUCCEEDED'],
        'FAILED': ['FAILED'],
    }
    job_counts = {}
    for status_group, statuses in status_groups.items():
        for status in statuses:
            job_counts[(None, status_group)] = 0
            for job in _batch_jobs_by_status(status):
                if 'stoppedAt' in job and time.time() * 1000 - job['stoppedAt'] > 60 * 5 * 1000:
                    continue
                job_name = job['jobName'].split('_')[-1]
                job_counts.setdefault((job_name, status_group), 0)
                job_counts.setdefault((None, status_group), 0)
                job_counts[(job_name, status_group)] += 1
                job_counts[(None, status_group)] += 1

    for (job_name, status), count in job_counts.items():
        _put_metric('BatchJobQueueCount', count, _dict_filter_values({'Status': status, 'Job': job_name}))


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

        if status == 'RUNNING':
            global should_run_again
            should_run_again = executions.count(status) > 0


def _batch_jobs_by_status(status, token=''):
    res = _batch_client.list_jobs(jobQueue=os.environ['BATCH_JOB_QUEUE'], jobStatus=status, nextToken=token)
    yield from res['jobSummaryList']
    if 'nextToken' in res and res['nextToken']:
        yield from _batch_jobs_by_status(status, res['nextToken'])


def _list_sfn_executions(token=None):
    res = _sfn_client.list_executions(
        **_dict_filter_values({'stateMachineArn': os.environ['STATE_MACHINE_ARN'], 'nextToken': token}))
    yield from res['executions']
    if 'nextToken' in res and res['nextToken']:
        yield from _list_sfn_executions(res['nextToken'])


def _put_metric(metric_name, value, dimensions={}, unit='None'):
    dimensions = {**{'Environment': os.environ['ENVIRONMENT']}, **dimensions}
    print(f'Putting {metric_name}={value} ({dimensions})')
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


def _dict_filter_values(d):
    return {k: v for k, v in d.items() if v}
