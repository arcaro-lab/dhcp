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
atlas_name, roi_labels = params.load_roi_info(atlas)


age_groups = ['infant', 'adult']

def create_indiv_rdm(group, sub_list, data_dir, atlas):
    
    atlas_name, roi_labels = params.load_roi_info(atlas)

    #Create fc matrix for each subject
    

    all_subs = []
    #for each subject looop through wang labels and load timeseries
    for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
        all_ts = []
        for roi in roi_labels['label']:
            for hemi in params.hemis:
                #load timeseries
                ts = np.load(f'{data_dir}/{sub}/{ses}/derivatives/timeseries/{hemi}_{roi}.npy')

                #average across voxels
                mean_ts = np.mean(ts, axis = 1)
                #append to all_ts
                all_ts.append(mean_ts)
            
    
        #convert to numpy array
        all_ts = np.array(all_ts)

        #compute correlation matrix across all rois
        corr_mat = np.corrcoef(all_ts)

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
    atlas_name, roi_labels = params.load_roi_info(atlas)

    

    all_rdms = []
    #for each subject looop through wang labels and load timeseries
    for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
        #create empty RDM size of number of rois
        rdm = np.zeros((len(roi_labels), len(roi_labels)))
        
        for x, roi in enumerate(roi_labels['label']):
            lts = np.load(f'{data_dir}/{sub}/{ses}/derivatives/timeseries/lh_{roi}.npy')
            lts = np.mean(lts, axis = 1)
            for y, roi in enumerate(roi_labels['label']):
                #load timeseries
                rts = np.load(f'{data_dir}/{sub}/{ses}/derivatives/timeseries/rh_{roi}.npy')
                rts = np.mean(rts, axis = 1)

                #compute correlation between lts and rts and add to rdm
                r = np.corrcoef(lts, rts)[0,1]

                #add to rdm
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
for group in ['infant','adult']:
    #extract group data
    raw_data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf = params.load_group_params(group)

    #load subject list
    sub_list = pd.read_csv(f'{out_dir}/participants.csv')
    sub_list = sub_list[sub_list[f'{atlas}_ts'] == 1]

    print(f'Extracting individual {group} RDMs...')
    #create indiv rdm
    all_rdms = create_indiv_rdm(group, sub_list, out_dir, atlas)

    #compute median rdm
    median_fc = np.median(all_rdms, axis = 0)

    #save median rdm to results dir as csv
    median_fc = pd.DataFrame(median_fc)
    median_fc.to_csv(f'{params.results_dir}/{group}_{atlas}_median_fc.csv', header = False, index = False)

    print(f'Extracting cross-hemi {group} RDMs ...')
    #compute cross hemi rdm
    cross_hemi_rdms = compute_cross_hemi_rdm(group, sub_list, out_dir, atlas)

    #compute median cross hemi rdm
    median_cross_hemi_fc = np.median(cross_hemi_rdms, axis = 0)

    #save median rdm to results dir as csv
    median_cross_hemi_fc = pd.DataFrame(median_cross_hemi_fc)
    median_cross_hemi_fc.to_csv(f'{params.results_dir}/{group}_{atlas}_median_cross_hemi_fc.csv', header = False, index = False)


    
    