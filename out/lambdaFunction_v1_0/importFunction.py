from __future__ import print_function

import json
import urllib
import boto3
import logging
import cStringIO
import psycopg2
import runAnalytics as ra
import numpy as np

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.info('Loading function')
    
def lambda_handler(event, context):
    

    logger.info('Received event: ' + json.dumps(event, indent=2))
    
    try:
                #s3 = boto3.client('s3')
        # Get the object from the event and show its content type
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key']).encode('utf8')
        s3r = boto3.resource('s3')
        logger.info('stage1')        
        obj = s3r.Bucket(bucket).Object(key)
        fileobj = obj.get()
        body = fileobj["Body"].read()
        logger.info('stage2')                
        content = cStringIO.StringIO(body)
        logger.info('stage2b') 
        cme = ra.RunAnalytics(content, 75, 0, 250, None)  
        logger.info('stage3')  
        obsCount = len(cme.load)    
        userId = np.full((obsCount),116,np.int32)
        exerciseId = np.full((obsCount),1,np.int32)
        obsIndex = np.arange(obsCount)
        merged = np.vstack((userId, exerciseId,obsIndex, cme.cont_contra[:,1],cme.cont_hiprot[:,1],cme.load[:,0],cme.load[:,1],cme.load[:,2],cme.load[:,3],cme.contr_prosup[:,1],cme.contl_prosup[:,1],cme.timestamp, cme.cont_contra[:,2],cme.cont_hiprot[:,2], cme.contr_prosup[:,2], cme.contl_prosup[:,2]))
        f = cStringIO.StringIO()
        np.savetxt(f, merged.transpose(), delimiter="\t",fmt="%i\t%i\t%i\t%1.3f\t%1.3f\t%1.3f\t%1.3f\t%1.3f\t%1.3f\t%1.3f\t%1.3f\t%i\t%1.3f\t%1.3f\t%1.3f\t%1.3f")    
        f.seek(0) #put the position of the buffer at the beginning
        logger.info('stage4')        
        conn = psycopg2.connect("dbname='biometrix' user='paul' host='ec2-52-36-42-125.us-west-2.compute.amazonaws.com' password='063084cb3b65802dbe01030756e1edf1f2d985ba'")
        
        #conn = psycopg2.connect("dbname='dd1dlev350skqf' user='psaqpvkuzkdnrc' host='ec2-50-19-219-148.compute-1.amazonaws.com' password='2S7ZXijF-CdK2-DYBQ6UfSbtAE'")
        #conn = psycopg2.connect("dbname='dd1dlev350skqf' user='psaqpvkuzkdnrc' password='2S7ZXijF-CdK2-DYBQ6UfSbtAE' host='172.31.17.160' port='5432'")
                      
        cur = conn.cursor()
                        
        cur.copy_from(file=f, table='movement',sep='\t', columns=('"userId"', '"exerciseId"','"obsIndex"','"hipDrop"','"hipRot"','"loadR"','"loadL"','"phaseR"','"phaseL"','"pronR"','"pronL"','"epochTime"','"nHipDrop"','"nHipRot"','"nPronR"','"nPronL"'))
        conn.commit()    
        logger.info('stage5')        
        conn.close()
        logger.info('success')
        #response = s3.get_object(Bucket=bucket, Key=key)
        #logger.info("CONTENT TYPE: " + response['ContentType'])
        #return response['ContentType']
        return 'success'
    except Exception as e:
        logger.info(e)
        logger.info('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e