'''
compute split half

*i think by splitting the TS
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

import dhcp_params as params

import pdb

age_groups= ['infant', 'adult']
age_groups = ['infant']
atlas = 'wang'

#load roi labels
atlas_info= params.load_atlas_info(atlas)


#add networks to roi labels
#atlas_info.roi_labels['network'] = ['EVC']*6 + ['ventral']*5 + ['lateral']*6 + ['dorsal']*7

networks = ['Occipital', 'Ventral', 'Lateral', 'Dorsal']

n_subs = 30

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

def split_half_reliability(group, atlas, all_rois, all_networks):
    '''
    Compute split half reliability for each roi
    '''

    atlas_info= params.load_atlas_info(atlas)
    group_info = params.load_group_params(group)

    sub_list = group_info.sub_list

    #select only subs who have atlas_ts
    sub_list = sub_list[sub_list[f'{atlas}_ts'] == 1]

    
    all_sub_df = pd.DataFrame(columns = ['sub', 'ses','sex','birth_age', 'scan_age', 'hemi', 'roi','network','fc' ])

    #for each subject looop through wang labels and load timeseries
    for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):

        sex = sub_list.loc[(sub_list['participant_id'] == sub) & (sub_list['ses'] == ses), 'sex'].values[0]
        birth_age = sub_list.loc[(sub_list['participant_id'] == sub) & (sub_list['ses'] == ses), 'birth_age'].values[0]
        scan_age = sub_list.loc[(sub_list['participant_id'] == sub) & (sub_list['ses'] == ses), 'scan_age'].values[0]


        all_ts1 = []
        all_ts2 = []
        all_ts = []
        for hemi in params.hemis:
            #load timeseries
            #this is all ROIs for a given hemisphere
            ts = np.load(f'{group_info.out_dir}/{sub}/{ses}/derivatives/timeseries/{sub}_{ses}_{atlas}_{hemi}_ts.npy')

            
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


        #split into two halves
        all_ts1 = full_ts[:,:int(full_ts.shape[1]/2)]
        all_ts2 = full_ts[:,int(full_ts.shape[1]/2):]

        
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

        roi_corrs = pd.DataFrame(columns = all_sub_df.columns)

        
        #correlate for each ROI
        for roi in all_rois:
            #extract hemi and roi
            hemi = roi.split('_')[0]
            curr_roi = roi.split('_')[1]
            network = atlas_info.roi_labels[atlas_info.roi_labels['label'] == curr_roi]['network'].values[0]

            #extract roi fc
            roi_fc = corr_mat1[corr_mat1['roi'] == roi]

            r = np.corrcoef(roi_fc['corr'], roi_fc['corr2'])[0,1]

            

            #add to roi_corrs using concat
            roi_corrs = pd.concat([roi_corrs, pd.DataFrame([[sub, ses, sex, birth_age, scan_age, hemi, curr_roi, network, r]], columns =  all_sub_df.columns)], ignore_index=True)
        

            


        #create noise ceiling folder
        os.makedirs(f'{group_info.out_dir}/{sub}/{ses}/derivatives/noise_ceiling', exist_ok=True)
        #save  
        roi_corrs.to_csv(f'{group_info.out_dir}/{sub}/{ses}/derivatives/noise_ceiling/{sub}_{atlas}_split_half_reliability.csv', index=False)

        #add to all_sub_df
        all_sub_df = pd.concat([all_sub_df, roi_corrs], ignore_index=True)

    #save
    all_sub_df.to_csv(f'{group_info.out_dir}/derivatives/noise_ceilings/{group}_{atlas}_split_half_reliability.csv', index=False)


def network_summary(group, atlas):
    
    '''
    Summarize split half reliability by network
    '''
    print('computing network summary...')

    atlas_name, roi_labels = params.load_atlas_info(atlas)
    raw_data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf = params.load_group_params(group)

    sub_list = pd.read_csv(f'{out_dir}/participants.csv')

    #select only subs who have atlas_ts
    sub_list = sub_list[sub_list[f'{atlas}_ts'] == 1]

    #create dataframe to store all subs
    all_sub_df = pd.DataFrame(columns=networks)

    #loop through subjects and load split half reliability
    for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
        #load split half reliability
        sub_df = pd.read_csv(f'{out_dir}/derivatives/noise_ceiling/{sub}_{atlas}_split_half_reliability.csv')

        #compute mean by network
        #sub_df = sub_df.groupby(['network']).mean()

        
        #add mean value for each network to all_sub_df
        for network in networks:
            all_sub_df.loc[sub, network] = sub_df[sub_df['network'] == network]['r'].mean()
        

    
    #save
    all_sub_df.to_csv(f'{git_dir}/results/noise_ceilings/{group}_{atlas}_network_split_half_reliability.csv', index=False)


def roi_summary(group, atlas, all_rois):
    '''
    Summarize split half reliability by roi
    '''
    print('computing roi summary...')
    atlas_name, roi_labels = params.load_atlas_info(atlas)
    raw_data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf = params.load_group_params(group)

    sub_list = pd.read_csv(f'{out_dir}/participants.csv')

    #select only subs who have atlas_ts
    sub_list = sub_list[sub_list[f'{atlas}_ts'] == 1]

    #create dataframe to store all subs
    all_sub_df = pd.DataFrame(columns=all_rois)

    #loop through subjects and load split half reliability
    for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
        #load split half reliability
        sub_df = pd.read_csv(f'{out_dir}/derivatives/noise_ceiling/{sub}_{atlas}_split_half_reliability.csv')

        #compute mean by network
        #sub_df = sub_df.groupby(['network']).mean()

        
        #add mean value for each network to all_sub_df
        for roi in all_rois:
            all_sub_df.loc[sub, roi] = sub_df[sub_df['roi'] == roi]['r'].mean()
        

    
    #save
    all_sub_df.to_csv(f'{git_dir}/results/noise_ceilings/{group}_{atlas}_roi_split_half_reliability.csv', index=False)
    

#define all rois and networks
all_rois = []
all_networks = []
for roi in atlas_info.roi_labels['label']:
    for hemi in params.hemis:
        all_rois.append(f'{hemi}_{roi}')
        all_networks.append(atlas_info.roi_labels[atlas_info.roi_labels['label'] == roi]['network'].values[0])

for group in age_groups:
    print(f'calculating split half {group} data...')
    split_half_reliability(group, atlas, all_rois, all_networks)
    #network_summary(group, atlas)
    #roi_summary(group, atlas, all_rois)
