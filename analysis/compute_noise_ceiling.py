'''
compute noise cieling
'''

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

age_groups= ['infant', 'adult']
atlas = 'wang'

#load roi labels
atlas_name, roi_labels = params.load_roi_info(atlas)

#add networks to roi labels
roi_labels['network'] = ['EVC']*6 + ['ventral']*5 + ['lateral']*6 + ['dorsal']*7

networks = ['EVC', 'ventral', 'lateral', 'dorsal']

n_subs = 30

def compute_noise_ceiling(all_rdms):

    '''
    Compute the noise ceiling by using leave one out cross validation
    
    '''
    #create list of indices with length of number of subjects
    sub_idx = np.arange(len(all_rdms.columns))

    #create empty list to store noise ceiling values
    noise_ceiling = []

    #loop through indices and remove one subject at a time
    #calcualte median rdm for remaining subjects
    #compute correlation between median rdm and removed subject
    for idx in sub_idx:
        
        #remove subject col from df
        sub_removed = all_rdms.drop(columns = idx)
        
        #compute median rdm
        median_rdm = np.median(sub_removed, axis = 1)

        #extract upper triangle of removed subject
        curr_sub = all_rdms[idx].values
        
        #compute correlation between median rdm and removed subject
        r = np.corrcoef(median_rdm, curr_sub)[0,1]

        #append to noise_ceiling
        noise_ceiling.append(r)

    return noise_ceiling


def split_half_reliability(group, atlas, all_rois, all_networks):
    '''
    Compute split half reliability for each roi
    '''

    atlas_name, roi_labels = params.load_roi_info(atlas)
    raw_data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf = params.load_group_params(group)

    sub_list = pd.read_csv(f'{out_dir}/participants.csv')

    #select only subs who have atlas_ts
    sub_list = sub_list[sub_list[f'{atlas}_ts'] == 1]

    


    #for each subject looop through wang labels and load timeseries
    for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
        all_ts1 = []
        all_ts2 = []
        for roi in roi_labels['label']:
            for hemi in params.hemis:
                #load timeseries
                ts = np.load(f'{out_dir}/{sub}/{ses}/derivatives/timeseries/{hemi}_{roi}.npy')

                #split into two halves
                ts1 = ts[:int(ts.shape[0]/2),:]
                ts2 = ts[int(ts.shape[0]/2):,:]

                #average across voxels
                mean_ts1 = np.mean(ts1, axis = 1)
                mean_ts2 = np.mean(ts2, axis = 1)
                #append to all_ts
                all_ts1.append(mean_ts1)
                all_ts2.append(mean_ts2)

        
    
        #convert to numpy array
        all_ts1 = np.array(all_ts1)
        all_ts2 = np.array(all_ts2)

        #compute correlation matrix across all rois
        corr_mat1 = np.corrcoef(all_ts1)
        corr_mat2 = np.corrcoef(all_ts2)

        #set diagnonal to nan
        np.fill_diagonal(corr_mat1, np.nan)
        np.fill_diagonal(corr_mat2, np.nan)

        

        #convert to dataframe
        corr_mat1 = pd.DataFrame(corr_mat1, index = all_rois, columns = all_rois)
        corr_mat2 = pd.DataFrame(corr_mat2, index = all_rois, columns = all_rois)

        #melt
        corr_mat1 = pd.melt(corr_mat1, var_name ='roi',value_name='corr')
        corr_mat2 = pd.melt(corr_mat2, var_name ='roi',value_name='corr')

        #combine into one df
        corr_mat1['corr2'] = corr_mat2['corr']

        #add network names
        corr_mat1 = add_network_names(corr_mat1, all_rois, all_networks)

        #drop nan values
        corr_mat1 = corr_mat1.dropna()

        roi_corrs = pd.DataFrame(columns = ['roi', 'network','r'])
        #correlate for each ROI
        for roi in all_rois:
            #extract roi fc
            roi_fc = corr_mat1[corr_mat1['roi'] == roi]

            r = np.corrcoef(roi_fc['corr'], roi_fc['corr2'])[0,1]

            #add to roi_corrs using concat
            roi_corrs = pd.concat([roi_corrs, pd.DataFrame([[roi, roi_fc['network'].values[0], r]], columns = ['roi', 'network','r'])], ignore_index=True)
            



        

        #create noise ceiling folder
        os.makedirs(f'{out_dir}/derivatives/noise_ceiling', exist_ok=True)
        #save  
        roi_corrs.to_csv(f'{out_dir}/derivatives/noise_ceiling/{sub}_{atlas}_split_half_reliability.csv', index=False)


def add_network_names(sub_df, all_rois, all_networks):

    #add network column
    #add columns for network
    for roi in sub_df['roi']:
        #find index of roi in all_labels
        idx = all_rois.index(roi)
        #get network
        network = all_networks[idx]
        #add to dataframe
        sub_df.loc[sub_df['roi'] == roi, 'network'] = network

    return sub_df

    

def preprocess_data(group, summary_type, all_rois, all_networks):
    '''
    Organize data for noise ceiling analysis
    '''
    

    raw_data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf = params.load_group_params(group)
    #load individual infant data
    all_rdms = np.load(f'{out_dir}/derivatives/fc_matrix/{group}_{atlas}_{summary_type}.npy')




    all_sub_df = pd.DataFrame()
    for i in range(all_rdms.shape[0]):
        curr_fc = all_rdms[i,:,:]
        #set diagonal to nan only if analysis type i not cross-hemi
        if summary_type != 'cross_hemi':
            np.fill_diagonal(curr_fc, np.nan)

        #convert to pandas dataframe and melt
        curr_sub = pd.DataFrame(curr_fc, index = all_rois, columns = all_rois)
        curr_sub = pd.melt(curr_sub, var_name ='roi',value_name='corr')
        curr_sub = curr_sub.dropna()

        #add curr_sub to all_sub_df
        all_sub_df[i] = curr_sub['corr']

    all_sub_df['roi'] = curr_sub['roi']


    #add network column
    #add columns for network
    all_sub_df = add_network_names(all_sub_df, all_rois, all_networks)

    #extract noise ceiling for each roi
    roi_df = pd.DataFrame(columns = all_rois)
    for roi in all_rois:

        #extract roi fc
        roi_fc = all_sub_df[all_sub_df['roi'] == roi]

        #extract only subject columns
        roi_fc = roi_fc.drop(columns = ['roi','network'])
        
        #compute noise ceiling
        noise_ceilings = compute_noise_ceiling(roi_fc)
        #add to all_sub_df
        roi_df[roi] = noise_ceilings

    #save
    roi_df.to_csv(f'{params.results_dir}/noise_ceilings/{group}_{atlas}_{summary_type}_roi_noise_ceilings.csv', index=False)

    #Extract noise ceiling for each network
    network_df = pd.DataFrame(columns = networks)
    #First compute overall noise ceiling

    network_fc = all_sub_df.drop(columns = ['roi','network'])
    noise_ceilings = compute_noise_ceiling(network_fc)
    network_df['overall'] = noise_ceilings
    for network in networks:

        #extract network fc
        network_fc = all_sub_df[all_sub_df['network'] == network]

        #extract only subject columns
        network_fc = network_fc.drop(columns = ['roi','network'])
        
        #compute noise ceiling
        noise_ceilings = compute_noise_ceiling(network_fc)
        #add to all_sub_df
        network_df[network] = noise_ceilings



    #save
    network_df.to_csv(f'{params.results_dir}/noise_ceilings/{group}_{atlas}_{summary_type}_network_noise_ceilings.csv', index=False)


#define all rois and networks
all_rois = []
all_networks = []
for roi in roi_labels['label']:
    for hemi in params.hemis:
        all_rois.append(f'{hemi}_{roi}')
        all_networks.append(roi_labels[roi_labels['label'] == roi]['network'].values[0])

for group in age_groups:
    print(f'calculating split half {group} data...')
    split_half_reliability(group, atlas, all_rois, all_networks)


""" 
summary_type = 'fc'

#define all rois and networks
all_rois = []
all_networks = []
for roi in roi_labels['label']:
    for hemi in params.hemis:
        all_rois.append(f'{hemi}_{roi}')
        all_networks.append(roi_labels[roi_labels['label'] == roi]['network'].values[0])

for group in age_groups:
    print(f'Preprocessing {group} {summary_type} data...')
    preprocess_data(group, summary_type, all_rois, all_networks)


summary_type = 'cross_hemi_fc'

#define all rois and networks
all_rois = []
all_networks = []
for roi in roi_labels['label']:

    all_rois.append(f'{roi}')
    all_networks.append(roi_labels[roi_labels['label'] == roi]['network'].values[0])

for group in age_groups:
    print(f'Preprocessing {group} {summary_type} data...')
    preprocess_data(group, summary_type, all_rois, all_networks) """