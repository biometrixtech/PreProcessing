#!/usr/bin/env python3
# Find the Batch logs for a particular execution
from datetime import datetime
import argparse
import boto3
import json

_sfn_client = None


def _get_execution_history(execution_arn):
    # TODO pagination
    return _sfn_client.get_execution_history(executionArn=args.executionarn)['events']


def main():
    execution_history = _get_execution_history(args.executionarn)
    states = {}
    base_time = None

    for event in execution_history:
        timestamp = event['timestamp'].replace(tzinfo=None)
        base_time = timestamp if base_time is None else min(base_time, timestamp)

        if 'stateEnteredEventDetails' in event:
            name = event['stateEnteredEventDetails']['name']
            states.setdefault(name, {'timings': {}})
            states[name]['timings']['State Entered'] = timestamp
        elif 'stateExitedEventDetails' in event:
            name = event['stateExitedEventDetails']['name']
            states.setdefault(name, {'timings': {}})
            states[name]['timings']['State Exited'] = timestamp

            output = json.loads(event['stateExitedEventDetails']['output'])
            if 'TaskResult' in output and output['TaskResult']['Container']['Command'][0].lower() == name.lower():
                states[name]['timings']['Job Created'] = datetime.utcfromtimestamp(output['TaskResult']['CreatedAt'] / 1000)
                states[name]['timings']['Job Started'] = datetime.utcfromtimestamp(output['TaskResult']['StartedAt'] / 1000)
                states[name]['timings']['Job Stopped'] = datetime.utcfromtimestamp(output['TaskResult']['StoppedAt'] / 1000)

    state_names = ['State Entered', 'Job Created', 'Job Started', 'Job Stopped', 'State Exited']
    print('Job' + ' '*17 + 'State Entered' + ' '*16 + 'Job Created' + ' '*16 + 'Job Started' + ' '*16 + 'Job Stopped' + ' '*15 + 'State Exited')
    for name, state in states.items():
        timings = state['timings']
        fstring = [f'{name:>22}']
        for i in range(len(state_names) - 1):
            current_state_name, next_state_name = state_names[i], state_names[i+1]
            if current_state_name in timings:
                fstring.append(f'{_get_time_offset_ms(base_time, timings[current_state_name]):>7,}ms')
            else:
                fstring.append(' ' * 9)

            if next_state_name in timings and current_state_name in timings:
                fstring.append(f'--{_get_time_offset_ms(timings[current_state_name], timings[next_state_name]):->7,}ms-->')
            else:
                fstring.append(' ' * 14)

        if state_names[-1] in timings:
            fstring.append(f'{_get_time_offset_ms(base_time, timings[state_names[-1]]):>7,}ms')
        print('  '.join(fstring))
        
        
def _get_time_offset_ms(from_ts, to_ts):
    return int((to_ts - from_ts).total_seconds() * 1000)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Profile a SFN execution')
    parser.add_argument('--region', '-r',
                        type=str,
                        choices=['us-west-2'],
                        default='us-west-2',
                        help='AWS Region')
    parser.add_argument('executionarn',
                        type=str,
                        help='The execution to profile')

    args = parser.parse_args()
    _sfn_client = boto3.client('stepfunctions', region_name=args.region)
    main()
