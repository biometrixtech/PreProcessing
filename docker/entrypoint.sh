#!/usr/bin/env bash

# Mount the EFS directory
echo "Mounting NFS directory"
mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=10,retrans=2 efs.internal:/ /net/efs 2>&1

# Execute the CMD from your Dockerfile, i.e. "npm start"
echo "Executing batch_entrypoint.py"
python ./batch_entrypoint.py "$1" "$2" "$3"
