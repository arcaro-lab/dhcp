'''
compute noise cieling
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
age_groups= ['adult']
atlas = 'wang'

#load roi labels
atlas_info = params.load_atlas_info(atlas)

roi_labels = atlas_info.roi_labels

networks = ['Occipital', 'ventral', 'lateral', 'dorsal']



    


def conduct_loo_single_hemis(group, summary_type, all_rois, all_networks):

    print('Conducting LOO for' , group, summary_type)
    
    summary_df = pd.DataFrame(columns=['sub','network1','roi1','network2','roi2','roi_similarity','network_similarity','corr'])
    #load atlast name and roi labels
    atlas_info = params.load_atlas_info(atlas)

    roi_labels = atlas_info.roi_labels
   
    group_params = params.load_group_params(group)
    sub_list= group_params.sub_list
    sub_list = sub_list[sub_list[f'{atlas}_ts'] == 1]
    #load individual infant data
    all_rdms = np.load(f'{group_params.out_dir}/derivatives/fc_matrix/{group}_{atlas}_within_hemi_fc.npy')


    all_sub_df = pd.DataFrame()
    for i in range(all_rdms.shape[0]):
        
        sub = sub_list['participant_id'][i]
        #extract current subject
        curr_fc = all_rdms[i,:,:]
        #set diagonal to nan
        np.fill_diagonal(curr_fc, np.nan)


        #Create group RDM with remaining subs
        group_fc = np.delete(all_rdms, i, axis = 0)
        #make median fc
        group_fc = np.median(group_fc, axis = 0)
        #set diagnonal to nan
        np.fill_diagonal(group_fc, np.nan)

        #loop through rois
        for (rn1, roi1), (_,network1) in zip(enumerate(all_rois), enumerate(all_networks)):
            curr_data = curr_fc[rn1,:]

            #hemi1 = roi1.split('_')[0]
            roi_name1 = roi1
            
            for (rn2, roi2), (_,network2) in zip(enumerate(all_rois), enumerate(all_networks)):
                #hemi2 = roi2.split('_')[0]
                roi_name2 = roi2

                group_data = group_fc[rn2,:]
                
                #find indices where curr_data and group_data are nan
                nan_idx = np.isnan(curr_data) | np.isnan(group_data)


                

                r = np.corrcoef(curr_data[~nan_idx], group_data[~nan_idx])[0,1]

                if roi1 == roi2:
                    roi_similarity = "same"
                else:
                    roi_similarity = "different"

                if network1 == network2:
                    network_similarity = "same"
                else:
                    network_similarity = "different"

                #add to summary_df using concat
                curr_df = pd.DataFrame([[sub,  all_networks[rn1],  roi_name1,  all_networks[rn2], roi_name2, roi_similarity, network_similarity, r]], 
                                       columns = ['sub','network1','roi1','network2','roi2','roi_similarity','network_similarity','corr'])
                summary_df = pd.concat([summary_df, curr_df])


                

    #save summary_df
    summary_df.to_csv(f'{params.results_dir}/noise_ceilings/{group}_{atlas}_{summary_type}_loo_noise_ceilings_single_hemi.csv', index=False)

def conduct_loo_both_hemis(group, summary_type, all_rois, all_networks):
    print('Conducting LOO for' , group, summary_type)


    summary_df = pd.DataFrame(columns=['sub','hemi1','network1','roi1','hemi2','network2','roi2','roi_similarity','network_similarity','corr'])
    #load atlast name and roi labels
    atlas_info = params.load_atlas_info(atlas)

    roi_labels = atlas_info.roi_labels
   
    group_params = params.load_group_params(group)
    sub_list= group_params.sub_list
    sub_list = sub_list[sub_list[f'{atlas}_ts'] == 1]
    #load individual infant data
    all_rdms = np.load(f'{group_params.out_dir}/derivatives/fc_matrix/{group}_{atlas}_{summary_type}.npy')


    all_sub_df = pd.DataFrame()
    for i in range(all_rdms.shape[0]):
        
        sub = sub_list['participant_id'][i]
        #extract current subject
        curr_fc = all_rdms[i,:,:]
        #set diagonal to nan
        np.fill_diagonal(curr_fc, np.nan)


        #Create group RDM with remaining subs
        group_fc = np.delete(all_rdms, i, axis = 0)
        #make median fc
        group_fc = np.mean(group_fc, axis = 0)
        #set diagnonal to nan
        np.fill_diagonal(group_fc, np.nan)

        #loop through rois
        for (rn1, roi1), (_,network1) in zip(enumerate(all_rois), enumerate(all_networks)):
            curr_data = curr_fc[rn1,:]

            hemi1 = roi1.split('_')[0]
            roi_name1 = roi1.split('_')[1]
            
            for (rn2, roi2), (_,network2) in zip(enumerate(all_rois), enumerate(all_networks)):
                hemi2 = roi2.split('_')[0]
                roi_name2 = roi2.split('_')[1]

                group_data = group_fc[rn2,:]
                
                #find indices where curr_data and group_data are nan
                nan_idx = np.isnan(curr_data) | np.isnan(group_data)


                

                r = np.corrcoef(curr_data[~nan_idx], group_data[~nan_idx])[0,1]

                if roi1 == roi2:
                    roi_similarity = "same"
                else:
                    roi_similarity = "different"

                if network1 == network2:
                    network_similarity = "same"
                else:
                    network_similarity = "different"

                #add to summary_df using concat
                curr_df = pd.DataFrame([[sub, hemi1,  all_networks[rn1],  roi_name1, hemi2, all_networks[rn2], roi_name2, roi_similarity, network_similarity, r]], 
                                       columns = ['sub','hemi1','network1','roi1','hemi2','network2','roi2','roi_similarity','network_similarity','corr'])
                summary_df = pd.concat([summary_df, curr_df])


                

    #save summary_df
    summary_df.to_csv(f'{params.results_dir}/noise_ceilings/{group}_{atlas}_{summary_type}_loo_noise_ceilings.csv', index=False)

                                         


summary_type = 'fc'

#define all rois and networks
all_rois = []
all_networks = []
for roi in roi_labels['label']:
    for hemi in params.hemis:
        all_rois.append(f'{hemi}_{roi}')
        all_networks.append(roi_labels[roi_labels['label'] == roi]['network'].values[0])

for group in age_groups:
    #print(f'Preprocessing {group} {summary_type} data...')
    #preprocess_data(group, summary_type, all_rois, all_networks)
    conduct_loo_both_hemis(group, summary_type, all_rois, all_networks)
    #conduct_loo_single_hemis(group, summary_type, roi_labels['label'].to_list(), roi_labels['network'].to_list())

'''
summary_type = 'cross_hemi_fc'

#define all rois and networks
all_rois = []
all_networks = []
for roi in roi_labels['label']:

    all_rois.append(f'{roi}')
    all_networks.append(roi_labels[roi_labels['label'] == roi]['network'].values[0])

for group in age_groups:
    #print(f'Preprocessing {group} {summary_type} data...')
    #preprocess_data(group, summary_type, all_rois, all_networks)
    conduct_loo(group, summary_type, all_rois, all_networks)
'''