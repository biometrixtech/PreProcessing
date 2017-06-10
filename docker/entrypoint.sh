#!/usr/bin/env bash

# Mount the EFS directory
mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2 efs.internal:/ /net/efs

# Execute the CMD from your Dockerfile, i.e. "npm start"
python ./batch_entrypoint.py "$1" "$2" "$3"
