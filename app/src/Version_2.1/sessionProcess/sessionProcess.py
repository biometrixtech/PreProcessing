from __future__ import print_function

import json
import urllib
import boto3
import logging
import cStringIO
#import zipfile as zf

#import runAnalytics as ra
import input_data_in_batches as idb


logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.info('Loading sessionProcess')
    
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
        result = idb.send_batches_of_data(content, key)
        logger.info('outcome:' + result)
        return 'success'
#        zipped = zf.ZipFile(content)
#        try:
#            name = zipped.namelist()[0]
#        except IndexError:
#            logger.warning('Fail!, no data inside zipped file')
#            return 'success'
#        else:
#            unzipped_content = cStringIO.StringIO()
#            unzipped_content = zipped.open(name)
#            logger.info('Unzipped File')
#            result = ra.run_session(unzipped_content, key)
#            logger.info('outcome:' + result)
#            return 'success'

    except Exception as e:
        logger.info(e)
        logger.info('Process did not complete successfully! See error below!')
        raise e
