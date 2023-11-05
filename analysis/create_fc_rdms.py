git_dir = '/mnt/c/Users/ArcaroLab/Desktop/git_repos/dhcp'

import os
import sys
#add git_dir to path
sys.path.append(git_dir)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import dhcp_params as params

import pdb

atlas = 'wang'


#load atlast name and roi labels
atlas_name, roi_labels = params.load_atlas_info(atlas)


age_groups= ['infant', 'adult']
age_groups = ['infant']

def create_indiv_rdm(group, sub_list, data_dir, atlas):
    
    atlas_name, roi_labels = params.load_atlas_info(atlas)

    #Create fc matrix for each subject
    

    all_subs = []
    #for each subject looop through wang labels and load timeseries
    for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
        all_ts = []

        for hemi in params.hemis:
            #load timeseries
            #this is all ROIs for a given hemisphere
            ts = np.load(f'{data_dir}/{sub}/{ses}/derivatives/timeseries/{sub}_{ses}_{atlas}_{hemi}_ts.npy')

            
            #if ts is longer than params.vols, truncate
            #this is to equalize the number of volumes across groups
            if ts.shape[0] > params.vols:
                ts = ts[:params.vols,:]

            #append to all_ts
            all_ts.append(ts)
            
        
        #intersperse hemis so it goes lh->rh->lh->rh for each rois
        full_ts = np.zeros((all_ts[0].shape[1] * 2, all_ts[0].shape[0]))
        full_ts[0::2] = all_ts[0].T
        full_ts[1::2] = all_ts[1].T
       

        #compute correlation matrix across all rois
        corr_mat = np.corrcoef(full_ts)

        all_subs.append(corr_mat)

        #save
        np.save(f'{data_dir}/derivatives/fc_matrix/{sub}_{atlas}_fc.npy', corr_mat)

    #convert to numpy array
    all_subs = np.array(all_subs)

    

    np.save(f'{data_dir}/derivatives/fc_matrix/{group}_{atlas}_fc.npy', all_subs)
    
    

    return all_subs





def compute_cross_hemi_rdm(group, sub_list, data_dir, atlas):

    ''' 
    create assymmetric RDM by correlating timeseries from one hemisphere with the other hemisphere
    '''
    atlas_name, roi_labels = params.load_atlas_info(atlas)

    

    all_rdms = []
    #for each subject looop through wang labels and load timeseries
    for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
        #create empty RDM size of number of rois
        rdm = np.zeros((len(roi_labels), len(roi_labels)))
        
    
        #load timeseries
        #this is all ROIs for a given hemisphere
        lh_ts = np.load(f'{data_dir}/{sub}/{ses}/derivatives/timeseries/{sub}_{ses}_{atlas}_lh_ts.npy')
        rh_ts = np.load(f'{data_dir}/{sub}/{ses}/derivatives/timeseries/{sub}_{ses}_{atlas}_rh_ts.npy')

        
        #if ts is longer than params.vols, truncate
        if lh_ts.shape[0] > params.vols:
            lh_ts = lh_ts[:params.vols,:]
            rh_ts = rh_ts[:params.vols,:]

        #correlate each roi in lh with each roi in rh
        for x, ts1 in enumerate(lh_ts.T):
            for y, ts2 in enumerate(rh_ts.T):
                
                r = np.corrcoef(ts1,ts2)[0,1]
                rdm[x,y] = r

  
                #append to all_ts
        all_rdms.append(rdm)

        #save 
        np.save(f'{data_dir}/derivatives/fc_matrix/{sub}_{atlas}_cross_hemi_fc.npy', rdm)

    #convert to numpy array
    all_rdms = np.array(all_rdms)
    #save all subs
    np.save(f'{data_dir}/derivatives/fc_matrix/{group}_{atlas}_cross_hemi_fc.npy', all_rdms)

    
    return all_rdms
            



    
#create indiv rdm for each subject
for group in age_groups:
    #extract group data
    raw_data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf, brain_mask_suf, group_template,template_name = params.load_group_params(group)

    #load subject list
    sub_list = pd.read_csv(f'{out_dir}/participants.csv')
    sub_list = sub_list[sub_list[f'{atlas}_ts'] == 1]

    print(f'Extracting individual {group} RDMs...', len(sub_list)) 
    #create indiv rdm
    all_rdms = create_indiv_rdm(group, sub_list, out_dir, atlas)

    #compute median rdm
    median_fc = np.median(all_rdms, axis = 0)

    #save median rdm to results dir as csv
    median_fc = pd.DataFrame(median_fc)
    median_fc.to_csv(f'{params.results_dir}/group_fc/{group}_{atlas}_median_fc.csv', header = False, index = False)

    print(f'Extracting cross-hemi {group} RDMs ...')
    #compute cross hemi rdm
    cross_hemi_rdms = compute_cross_hemi_rdm(group, sub_list, out_dir, atlas)

    #compute median cross hemi rdm
    median_cross_hemi_fc = np.median(cross_hemi_rdms, axis = 0)

    #save median rdm to results dir as csv
    median_cross_hemi_fc = pd.DataFrame(median_cross_hemi_fc)
    median_cross_hemi_fc.to_csv(f'{params.results_dir}/group_fc/{group}_{atlas}_median_cross_hemi_fc.csv', header = False, index = False)


    
    