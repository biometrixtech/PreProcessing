#!/usr/bin/env python
# Entrypoint when called as a batch job
import json
import sys

if __name__ == '__main__':
    script = sys.argv[1]
    input_data = json.loads(sys.argv[2])
    meta_data = json.loads(sys.argv[3])

    print([script,input_data,meta_data])
