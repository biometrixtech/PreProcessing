# -*- coding: utf-8 -*-
"""
Created on Thu Nov  3 16:04:07 2016

@author: ankurmanikandan
"""

import boto3
import pandas as pd
import cStringIO
import numpy as np
import cPickle as pickle
import pandas as pd
from mechStressTraining import prepare_data
import time

start_time = time.timestart_time = time.time()

s3 = boto3.resource('s3')
cont_read = 'biometrix-globalmodels'
obj = s3.Bucket(cont_read).Object('ms_trainmodel.pkl')
fileobj = obj.get()
body = fileobj["Body"].read()
#feet = cStringIO.StringIO(body)

print("--- %s seconds ---" % (time.time() - start_time))

#
path = 'subject3_DblSquat_hist.csv'
data = np.genfromtxt(path, dtype=float, delimiter=',', names=True) #create ndarray from path
data_pd = pd.DataFrame(data)
#
x = prepare_data(data_pd, False)
#
fit_model = pickle.loads(body) #we're reading the first model on the list, there are multiple
#
ms_1 = fit_model.predict(x)
