# -*- coding: utf-8 -*-
"""
Created on Wed Nov 02 13:26:20 2016

@author: Gautam
"""
import psycopg2
import cPickle as pickle
import numpy as np
import pandas as pd
from mechStressTraining import prepare_data
 ###Connect to the database
try:
    conn = psycopg2.connect("""dbname='biometrix' user='paul' 
    host='ec2-52-36-42-125.us-west-2.compute.amazonaws.com' 
    password='063084cb3b65802dbe01030756e1edf1f2d985ba'""")
except:
    print 'Fail! Unable to connect to database'

cur = conn.cursor()

ms_path = 'ms_trainmodel.pkl'
with open(ms_path, "rb") as f:
    mstress_fit = pickle.load(f)
    
    
#serialize the model (my system goes crazy here for some reason)
serialized = pickle.dumps(mstress_fit, 1)

#write to DB (we already have a couple of models stored in the database
#won't be a problem if we skip this step or change it to update but I've left the identifier column(test) blank)
sql = "INSERT INTO test_ms_model VALUES(%s)"
cur.execute(sql, (psycopg2.Binary(serialized),))
conn.commit()


#read data to predict
path = 'subject3_DblSquat_hist.csv'
data = np.genfromtxt(path, dtype=float, delimiter=',', names=True) #create ndarray from path
data_pd = pd.DataFrame(data)

x = prepare_data(data_pd, False)


#read from DB
sql_read = "select * from test_ms_model"
cur.execute(sql_read)
model_read = cur.fetchall()
fit_model = pickle.loads(model_read[0][0][:]) #we're reading the first model on the list, there are multiple

ms_1 = fit_model.predict(x)



ms_path = 'ms_trainmodel_1.sav'
with open(ms_path, "w") as f:
    pickle.dump(fit_model, f)
    
    




