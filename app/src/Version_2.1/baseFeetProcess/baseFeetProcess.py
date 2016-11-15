from __future__ import print_function

import json
import urllib
import boto3
import logging
import cStringIO
import zipfile as zf

import runBaseFeet as rb


logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.info('Loading baseFeetProcess')
    
    
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
        zipped = zf.ZipFile(content)
        try:
            name = zipped.namelist()[0]
        except IndexError:
            logger.info('Fail!, no data inside zipped file')
            return 'success'
        else:
            unzipped_content = cStringIO.StringIO()
            unzipped_content = zipped.open(name)
            logger.info('Unzipped File')
            result = rb.record_special_feet(unzipped_content, key)
            logger.info('outcome:' + result)
            
            #response = s3.get_object(Bucket=bucket, Key=key)
            #logger.info("CONTENT TYPE: " + response['ContentType'])
            #return response['ContentType']
            return 'success'
    except Exception as e:
        logger.info(e)
        logger.info('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e