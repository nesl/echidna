# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

'''
Probe moving towards target (AL/PVC)
Probe 1 faces target
Probe is circular
Probe numbered clockwise 1-8
moving along the y axis (increase y as it moves towards the target)

close a file:
-db.close()
-hdlr.close()

IPython magic
whos: lists workspace
reset: clears workspace
'''

# <codecell>

%qtconsole

# <codecell>

'''
 alTarget_4-5-2013_2.log
 pvcTarget_4-5-2013_2.log

%run echidna_data_read.py --file ~/Documents/tankDataBackup/pvcTarget_4-5-2013_2.log
pvcSamples = samples
pvcSamples = sorty(pvcSamples)
db.close();
hdlr.close();
del samples,hdlr
'''
%run echidna_data_read.py --file ~/Dropbox/echidna2/scripts/echidna_client/alum_2.5in_4_7_2013_tank_3_x7in_y16in/alumTarget_4-7-2013_3.log
alSamples = samples
alSamples = sorty(alSamples)
db.close();
hdlr.close();
del samples, hdlr

%run echidna_data_read.py --file ~/Dropbox/echidna2/scripts/echidna_client/pvc_2.5in_4_7_2013_1_tank_x7in_y16in/pvcTarget_2.5in_4-7-2013_0.log
pvcSamples = samples
pvcSamples = sorty(pvcSamples)
db.close();
hdlr.close();
del samples, hdlr

#%run echidna_data_read.py --file ~/Documents/tankDataBackup/empty_tank_2013_04_04_0.log

# <codecell>

# (250,300,8)
# 1 sinewave sample is 300
# 250 sinewaves taken
# target is near probe 1
# half inch steps
# variable db
# s.--- to run functions
from sklearn import cross_validation
from sklearn import svm
from random import shuffle

average = 1
s = pvcSamples[0]
sPeaks = s.getPeakPower()
rlen = sPeaks.shape[0]

x = range(rlen)
shuffle(x)
train_index = x[0:12]
test_index = x[12:24]

s = pvcSamples[0]
sPeaks = s.getPeakPower()
bkgnd_train = sPeaks[train_index,:]
bkgnd_test  = sPeaks[test_index,:]

clf = svm.SVC(kernel='rbf',C=1)

#for i in range(1,36):
cv = 2
score = np.zeros(cv)
acc = np.zeros((35,3)); # (y pos, mean, std)
for j in range(1,36):
    s = pvcSamples[j]
    sPeak = s.getPeakPower()
    sPeak_train = sPeak[train_index,:]
    sPeak_test = sPeak[test_index,:]
    
    train = np.append(bkgnd_train,sPeak_train,axis=0)
    test = np.append(bkgnd_test,sPeak_test,axis=0)
    label_train = np.append(np.zeros(12,dtype=int), np.ones(12,dtype=int))
    label_test = np.append(np.zeros(12,dtype=int), np.ones(12,dtype=int))

    clf.fit(train,label_train)
    results = clf.predict(test)
    score[0] = sum(results == label_test,dtype=float)/results.shape[0]
    clf.fit(test,label_test)
    results = clf.predict(train)
    score[1] = sum(results == label_train,dtype=float)/results.shape[0]
    acc[j-1,:] = np.array([s.pos.y, mean(score), std(score)])
    print 'pos %2.4f accuracy: %0.2f (+/0 %0.2f)' % (s.pos.y, mean(score), std(score))
    
print 'first third %0.2f' % (sum(acc[0:11,1])/11)   
print 'second third %0.2f' % (sum(acc[11:23,1])/12)   
print 'third third %0.2f' % (sum(acc[23:35,1])/12)   

#scores = cross_validation.cross_val_score(clf, sampPeaks[:,1:9], sampPeaks[:,0], cv=3)
#print "Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() / 2)

# <codecell>

import math
import numpy as np

def getPos(index):
    print 'x:',samples[index].pos.x,'y:', samples[index].pos.y

def averageData(d_samples, n_avg):
    '''
    d_samples: (250,8) typical set of probe peak values
    n_avg: number of samples to average
    '''
    row_len = d_samples.shape[0];
    div = row_len/n_avg
    new_samples = np.zeros((div,d_samples.shape[1]))
    
    for i in range(div):
        set_i = np.array(range(0,n_avg)) + i*n_avg*np.ones(n_avg,dtype=int)
        if i == div-1:
            set_i = range(set_i[0],row_len)
            new_samples[i,:] = mean(d_samples[set_i,:],axis=0)
        else:
            new_samples[i,:] = mean(d_samples[set_i,:],axis=0)
    return new_samples

def getPowerPeakJoin(set_samples,n_avg):
    '''
    Get all of the max peaks of the FFTs in the data
    and join them together in one big numpy array

    set_samples: input samples
    n_avg: how many values to average out
    '''
    s = set_samples[0] # first sample out of nlen
    sPeak = s.getPeakPower() # get the FFT peak (# of samples, probes)
    sPeak = averageData(sPeak,n_avg)
    
    setlen = len(set_samples)
    samplen = sPeak.shape[0] # length of samples at each distance
    tlen = setlen*samplen # total length of all data
    plen = sPeak.shape[1] # number of probes
    
    sampPeakJoin = np.zeros((tlen,plen))
    
    for i in range(setlen):
        s = set_samples[i]
        sPeak = s.getPeakPower()
        sPeak = averageData(sPeak,n_avg)
        
        set_i = range(0,samplen) + i*samplen*np.ones(samplen,dtype=int)
        sampPeakJoin[set_i,:] = sPeak
    
    return attachPowerPeakLabel(set_samples,sampPeakJoin,n_avg, setlen, samplen)

def attachPowerPeakLabel(set_samples, set_samples_join, n_avg, setlen, samplen):
    '''
    attach y axis labels to the data
    '''
    # Internal parameter
    threshold = 0
    
    labels = np.zeros((setlen*samplen,1))
    
    for i in range(setlen):
        s = set_samples[i]
        set_i = range(0,samplen) + i*samplen*np.ones(samplen,dtype=int)
        if i == 0 
            labels[set_i,0] = 0
        else:
            labels[set_i,0] = s.pos.y*np.ones(samplen,dtype=int)
        
    return np.append(labels, set_samples_join, axis=1)

# <codecell>

#samples = [s for s in samples if s.pos.x == samples[10].pos.x]
samples_sorted = sorted(samples,key=lambda o : o.pos.y)

a = [v.getMeanPower() for v in samples_sorted];
a = np.array(a)
figure(figsize(10,10))
pyplot.plot(a)
legend(['1','2','3','4','5','6','7','8'],bbox_to_anchor=(1,1), ncol=8)

# <codecell>


