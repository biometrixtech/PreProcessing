#!/usr/bin/env python3
import argparse
import boto3
import pandas as pd
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime

pd.set_option('display.height', 1000)
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


parser = argparse.ArgumentParser(description='Get an extract from the accessory sync log')
parser.add_argument('--region', '-r',
                    type=str,
                    help='AWS Region',
                    choices=['us-west-2'],
                    default='us-west-2')
parser.add_argument('--environment', '-e',
                    type=str,
                    help='Environment',
                    choices=['dev', 'qa', 'production'],
                    default='production')
parser.add_argument('--accessory',
                    type=str,
                    help='Accessory mac address')
parser.add_argument('--start',
                    type=str,
                    default=None,
                    help='Start date')
parser.add_argument('--end',
                    type=str,
                    default=None,
                    help='End date')

args = parser.parse_args()

dynamodb_table = boto3.resource('dynamodb', region_name=args.region).Table('preprocessing-{}-ingest-sessions'.format(args.environment))


def query_dynamodb(filter_expression, limit=10000, scan_index_forward=True, exclusive_start_key=None):
    if exclusive_start_key is not None:
        ret = dynamodb_table.scan(
            Select='ALL_ATTRIBUTES',
            Limit=limit,
            FilterExpression=filter_expression,
            ExclusiveStartKey=exclusive_start_key,
        )
    else:
        ret = dynamodb_table.scan(
            Select='ALL_ATTRIBUTES',
            Limit=limit,
            FilterExpression=filter_expression,
        )
    if 'LastEvaluatedKey' in ret:
        # There are more records to be scanned
        return ret['Items'] + query_dynamodb(filter_expression, limit, scan_index_forward, ret['LastEvaluatedKey'])
    else:
        # No more items
        return ret['Items']


def print_table(sessions):
    matrix = [[
        s['id'],
        datetime.strptime(s['event_date'], "%Y-%m-%dT%H:%M:%SZ").strftime('%Y-%m-%d at %H:%M:%S'),
        datetime.strptime(s['created_date'], "%Y-%m-%dT%H:%M:%SZ").strftime('%Y-%m-%d at %H:%M:%S'),
        datetime.strptime(s['updated_date'], "%Y-%m-%dT%H:%M:%SZ").strftime('%Y-%m-%d at %H:%M:%S'),
        s['session_status'],
        s['accessory_id'],
    ] for s in sessions]
    matrix_pd = pd.DataFrame(matrix)
    matrix_pd.columns = ['Session ID', 'Happened At', 'Created Date', 'Updated Date', 'Status', 'Accessory']
    matrix_pd.fillna(0, inplace=True)
    print(matrix_pd.round(2))


def main():
    fx = Attr('accessory_id').eq(args.accessory)
    if args.start is not None:
        fx = fx & Attr('event_date').gte(args.start)
    if args.end is not None:
        fx = fx & Attr('event_date').lte(args.end)
    res = query_dynamodb(fx)

    if len(res):
        print_table(res)
    else:
        print('No sessions found')


if __name__ == '__main__':
    main()
