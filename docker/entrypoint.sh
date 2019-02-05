#!/usr/bin/env sh

# Execute the CMD from your Dockerfile, i.e. "npm start"
echo "Executing batch_entrypoint.py"
python ./batch_entrypoint.py "$1"
