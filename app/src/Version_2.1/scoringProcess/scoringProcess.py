from __future__ import print_function

import json
import urllib
import boto3
import logging
import cStringIO
import zipfile as zf

import runScoring as rs


logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.info('Loading scoringProcess')
    
def lambda_handler(event, context):
    

    logger.info('Received event: ' + json.dumps(event, indent=2))
    
    try:
        
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key']).encode('utf8')
        s3r = boto3.resource('s3')
        logger.info('Obtained S3 Resource')
        obj = s3r.Bucket(bucket).Object(key)
        logger.info('Obtained Key')        
        fileobj = obj.get()
        logger.info('Got Fileobj')        
        body = fileobj["Body"].read()
        logger.info('Read Content')        
        content = cStringIO.StringIO(body)
        logger.info('Converted Content')       
        result = rs.run_scoring(content, key)
        logger.info('outcome:' + result)
        return 'success'

    except Exception as e:
        logger.info(e)
        logger.info('Error completing scoring process. See details below!')
        raise e