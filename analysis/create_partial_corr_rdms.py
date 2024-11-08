'''
Create RDMs from timeseries data by correlating timeseries from each ROI using partial correlations

For each ROI pair, partial correlation is calculated between timeseries from each ROI pair while controlling for the timeseries from all other ROIs
'''

project_name = 'dhcp'
import os
#get current working directory
cwd = os.getcwd()
git_dir = cwd.split(project_name)[0] + project_name
import sys

#add git_dir to path
sys.path.append(git_dir)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import dhcp_params as params
import pingouin as pg

import pdb

group = sys.argv[1]



atlas = 'wang'

group_info = params.load_group_params(group)

 #load subject list
sub_list= group_info.sub_list
sub_list = sub_list[sub_list[f'{atlas}_ts'] == 1]

#load atlast name and roi labels
atlas_info = params.load_atlas_info(atlas)
roi_labels = atlas_info.roi_labels

data_dir = group_info.out_dir

age_groups= ['infant', 'adult']
age_groups= ['infant']

extract_group = True

extract_indiv = True


atlas_info = params.load_atlas_info(atlas)
roi_labels = atlas_info.roi_labels

#Create fc matrix for each subject


all_subs = []
#for each subject looop through wang labels and load timeseries
for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
    print(sub)
    all_ts = []

    
    #check if file exists
    #if not, skip
    if os.path.exists(f'{data_dir}/{sub}/{ses}/derivatives/timeseries/{sub}_{ses}_{atlas}_lh_ts.npy'):

        for hemi in params.hemis:
            #load timeseries
            #this is all ROIs for a given hemisphere

            #check if file exists
            
            ts = np.load(f'{data_dir}/{sub}/{ses}/derivatives/timeseries/{sub}_{ses}_{atlas}_{hemi}_ts.npy')

            
            #if ts is longer than params.vols, truncate
            #this is to equalize the number of volumes across groups
            if ts.shape[0] > group_info.vols:
                ts = ts[:group_info.vols,:]

            #append to all_ts
            all_ts.append(ts)
            
        
        #intersperse hemis so it goes lh->rh->lh->rh for each rois
        full_ts = np.zeros((all_ts[0].shape[1] * 2, all_ts[0].shape[0]))
        full_ts[0::2] = all_ts[0].T
        full_ts[1::2] = all_ts[1].T

        
        #convert to pandas dataframe with each timeseries as a column
        ts_df = pd.DataFrame(full_ts.T)

        corr_mat = ts_df.pcorr().values

        all_subs.append(corr_mat)

        #save
        np.save(f'{data_dir}/{sub}/{ses}/derivatives/fc_matrix/{sub}_{ses}_{atlas}_fc_partial.npy', corr_mat)

        #else:
        #    print(f'{sub} does not have timeseries file')

#convert to numpy array
all_subs = np.array(all_subs)

#compute median rdm
median_fc = np.median(all_subs, axis = 0)


#save median rdm to results dir as csv
median_fc = pd.DataFrame(median_fc)
median_fc.to_csv(f'{params.results_dir}/group_fc/{group}_{atlas}_median_fc_partial.csv', header = False, index = False)







