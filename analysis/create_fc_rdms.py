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

infant_dir = '/mnt/e/dhcp_analysis_full'
adult_dir = '/mnt/f/7T_HCP'

#load atlast name and roi labels
atlas_name, roi_labels = params.load_roi_info(atlas)

#remove FEF from roi_labels
roi_labels = roi_labels[roi_labels['label'] != 'FEF']

age_groups = ['infant', 'adult']

def create_indiv_rdm(sub_list, data_dir, atlas):
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

    np.save(f'{data_dir}/derivatives/fc_matrix/all_subs_{atlas}_fc.npy', all_subs)

    return all_subs


def compute_mean_rdm(sub_list, data_dir, atlas):
    all_mats = []
    
    for sub in sub_list['participant_id']:

        #check if file exists
        if not os.path.exists(f'{data_dir}/{sub}_{atlas}_fc.npy'):
            print(f'{sub} does not exist')
            continue
        #load fc matrix
        fc_mat = np.load(f'{data_dir}/{sub}_{atlas}_fc.npy')
        

        #append to all mats
        all_mats.append(fc_mat)
        
    #convert to numpy array
    all_mats = np.array(all_mats)

    #for each cell, get the mean value across subjects
    mean_fc = np.mean(all_mats, axis = 0)

    return mean_fc, all_mats



def compute_median_rdm(sub_list, data_dir, atlas):

    all_mats = []

    for sub in sub_list['participant_id']:

        #check if file exists
        if not os.path.exists(f'{data_dir}/{sub}_{atlas}_fc.npy'):
            print(f'{sub} does not exist')
            continue
        #load fc matrix
        fc_mat = np.load(f'{data_dir}/{sub}_{atlas}_fc.npy')


        #append to all mats
        all_mats.append(fc_mat)


    #convert to numpy array
    all_mats = np.array(all_mats)

    #for each cell, get the median value across subjects
    median_fc = np.median(all_mats, axis = 0)

    return median_fc, all_mats


def compute_noise_ceiling(all_mats):

    '''
    Compute the noise ceiling by using leave one out cross validation
    
    '''
    #create list of indices with length of number of subjects
    sub_idx = np.arange(all_mats.shape[0])

    #create empty list to store noise ceiling values
    noise_ceiling = []

    #loop through indices and remove one subject at a time
    #calcualte median rdm for remaining subjects
    #compute correlation between median rdm and removed subject
    for idx in sub_idx:
        #remove subject
        sub_removed = np.delete(all_mats, idx, axis = 0)

        #compute median rdm
        median_rdm = np.median(sub_removed, axis = 0)

        #extract upper triangle of median rdm
        median_rdm = np.triu(median_rdm, k = 1)

        #extract upper triangle of removed subject
        curr_sub = np.triu(all_mats[idx], k = 1)

        #compute correlation between median rdm and removed subject
        r = np.corrcoef(median_rdm, curr_sub[idx])[0,1]

        #append to noise_ceiling
        noise_ceiling.append(r)

    return noise_ceiling


def compute_cross_hemi_rdm(sub_list, data_dir, atlas):

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
    np.save(f'{data_dir}/derivatives/fc_matrix/{sub}_{atlas}_cross_hemi_fc.npy', all_rdms)

    return all_rdms
            



    
#create indiv rdm for each subject
for group in ['infant','adult']:
    #extract group data
    raw_data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf = params.load_group_params(group)

    #load subject list
    sub_list = pd.read_csv(f'{out_dir}/subject_list.csv')

    #create indiv rdm
    all_rdms = create_indiv_rdm(sub_list, out_dir, atlas)

    #compute median rdm
    median_fc = np.median(all_rdms, axis = 0)

    #save median rdm to results dir as csv
    median_fc = pd.DataFrame(median_fc, columns = False, index = False)
    median_fc.to_csv(f'{params.results_dir}/{group}_{atlas}_median_fc.csv')

    #compute cross hemi rdm
    cross_hemi_rdms = compute_cross_hemi_rdm(sub_list, out_dir, atlas)

    #compute median cross hemi rdm
    median_cross_hemi_fc = np.median(cross_hemi_rdms, axis = 0)

    #save median rdm to results dir as csv
    median_cross_hemi_fc = pd.DataFrame(median_cross_hemi_fc, columns = False, index = False)
    median_cross_hemi_fc.to_csv(f'{params.results_dir}/{group}_{atlas}_median_cross_hemi_fc.csv')


    
    