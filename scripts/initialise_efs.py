#!/usr/bin/env python
# Initialise a new EFS filesystem
import json

import boto3
import argparse
import time


def register_job_definition(job_name, commands):
    res = batch_client.register_job_definition(
        jobDefinitionName=job_name,
        type="container",
        containerProperties={
            "image": "faisyl/alpine-nfs",
            "vcpus": 1,
            "memory": 128,
            "command": [
                "/bin/sh", "-c",
                " \
                    mkdir /net /net/efs ; \
                    mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=10,retrans=2 efs.internal:/ /net/efs 2>&1 ; \
                    {commands}; \
                ".format(commands='; '.join(commands))
            ],
            "readonlyRootFilesystem": False,
            "privileged": True,
            "jobRoleArn": 'arn:aws:iam::887689817172:role/preprocessing-{}-execute-{}'.format(args.environment, args.region)
        }
    )
    print("Registered new job definition (revision {})".format(res['revision']))
    return res['jobDefinitionArn']


def get_latest_job_definition(job_name):
    res = batch_client.describe_job_definitions(jobDefinitionName=job_name)
    revisions = sorted([(jd['revision'], jd['jobDefinitionArn']) for jd in res['jobDefinitions']])
    return revisions[-1][1]


def submit_job(job_definition_arn, job_name):
    print("Submitting job")
    res = batch_client.submit_job(
        jobName=job_name,
        jobQueue='preprocessing-{}-compute'.format(args.environment),
        jobDefinition=job_definition_arn,
    )
    print("Job ID: {}".format(res['jobId']))
    return res['jobId']


def await_job(job_id):
    while True:
        job = batch_client.describe_jobs(jobs=[job_id])['jobs'][0]
        print("Job status: {}".format(job['status']))
        if job['status'] in ['FAILED']:
            raise Exception("Job failed!")
        elif job['status'] in ['SUCCEEDED']:
            print('Job complete')
            return
        else:
            print('Job still running')
            time.sleep(15)
            continue
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Initialise a newly-created EFS filesystem')
    parser.add_argument('--region', '-r',
                        type=str,
                        default='us-west-2',
                        help='AWS Region')
    parser.add_argument('--environment', '-e',
                        type=str,
                        help='Environment',
                        default='dev')
    parser.add_argument('--no-register',
                        action='store_true',
                        dest='noregister',
                        help='Skip registering a new job definition, use the current latest one')

    args = parser.parse_args()
    batch_client = boto3.client('batch', region_name=args.region)

    if args.noregister:
        initialise_arn = get_latest_job_definition('maintenance-initialiseefs')
        install_arn = get_latest_job_definition('maintenance-downloadmodels')
    else:
        initialise_arn = register_job_definition(
            'maintenance-initialiseefs',
            ['mkdir -p /net/efs/preprocessing /net/efs/globalmodels /net/efs/globalscalers']
        )
        commands = ['apk update && apk upgrade musl && apk add aws-cli']
        models = [
            ('grf_model_v3_1.h5', 'globalmodels'),
            ('grf_model_left_v2_1.h5', 'globalmodels'),
            ('grf_model_right_v2_1.h5', 'globalmodels'),
            ('placement_model_v1_0.pkl', 'globalmodels'),
            ('scaler_model_v3_1.pkl', 'globalscalers'),
            ('scaler_model_single_v2_1.pkl', 'globalscalers'),
        ]
        for model, directory in models:
            commands.append('aws s3 cp s3://biometrix-globalmodels/{env}/{model} /net/efs/{directory}/{model}'.format(env=args.environment, model=model, directory=directory))
        install_arn = register_job_definition('maintenance-downloadmodels', commands)
    print('Running job {}'.format(initialise_arn))

    initialise_id = submit_job(initialise_arn, '00000000-0000-0000-0000-maintenance-initialiseefs')
    await_job(initialise_id)
    install_id = submit_job(install_arn, '00000000-0000-0000-0000-maintenance-downloadmodels')
    await_job(install_id)
