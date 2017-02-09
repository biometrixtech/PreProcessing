# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 10:53:08 2017

@author: ankurmanikandan
"""

import math
from itertools import islice, count
import pandas as pd
import cStringIO
import boto


def multipartupload_movement_data(movement_data, file_name_s3, b):

    # Create a multipart upload request
    mp = b.initiate_multipart_upload(file_name_s3)
    
    # Use only a set of columns each time to write to fileobj
    rows_set_size = 10000  # number of rows durin each batch upload (change if needed)
    number_of_rows = len(movement_data)
    rows_set_count = int(math.ceil(number_of_rows/float(rows_set_size)))
#    _logger('number of parts to be uploaded' + str(rows_set_count))
    print rows_set_count, 'number of parts to be uploaded'
    
    # Initialize counter to the count number of parts uploaded in the loop below
    counter = 0
    
    # Send the file parts, using FileChunkIO to create a file-like object
    for i in islice(count(), 0, number_of_rows,  rows_set_size):
        counter = counter + 1
        movement_data_subset = movement_data.iloc[i:i+rows_set_size]
        print len(movement_data_subset), 'length of subset'
        fileobj = cStringIO.StringIO()
        if counter == 1:
            movement_data_subset.to_csv(fileobj, index=False)
        else:
            movement_data_subset.to_csv(fileobj, index=False, header=False)
        del movement_data_subset
        fileobj.seek(0)
        mp.upload_part_from_file(fileobj, part_num=counter)
        del fileobj
        print counter, 'this is the counter'
        
    if len(mp.get_all_parts()) == rows_set_count:
        mp.complete_upload()
#        _logger('Upload file done!')
        print 'Upload file done!'
    else:
#        _logger('Upload file failed!')
        print 'Upload file failed!' 
        
        
if __name__ == '__main__':
    
    file_name = 'processed_7803f828-bd32-4e97-860c-34a995f08a9e.csv'
    data_path = '/Users/ankurmanikandan/Downloads/' + file_name
    
    data = pd.read_csv(data_path)
    
    # Connect to S3
    c = boto.connect_s3()
    b = c.get_bucket('biometrix-sessionprocessedcontainer')  # name of the bucket 
    # you want the fiole to be dropped in
    
    # function call
    multipartupload_movement_data(movement_data=data, 
                                  file_name_s3='test_multipart_upload_movement_3', 
                                  b=b)













