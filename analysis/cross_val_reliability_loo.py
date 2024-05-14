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
atlas = 'wang'

#load roi labels
atlas_info = params.load_atlas_info(atlas)

roi_labels = atlas_info.roi_labels

networks = ['Occipital', 'ventral', 'lateral', 'dorsal']

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
    

    #load atlast name and roi labels
    atlas_info = params.load_atlas_info(atlas)

    roi_labels = atlas_info.roi_labels


    
    group_params = params.load_group_params(group)
    #load individual infant data
    all_rdms = np.load(f'{group_params.out_dir}/derivatives/fc_matrix/{group}_{atlas}_{summary_type}.npy')



    all_sub_df = pd.DataFrame()
    for i in range(all_rdms.shape[0]):
        #extract current subject
        curr_fc = all_rdms[i,:,:]
        #set diagonal to nan
        curr_fc = np.fill_diagonal(curr_fc, np.nan)


        #Create group RDM with remaining subs
        group_fc = np.delete(all_rdms, i, axis = 0)
        #make median fc
        group_fc = np.median(group_fc, axis = 0)
        #set diagnonal to nan
        group_fc = np.fill_diagonal(curr_fc, np.nan)

        pdb.set_trace()

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

def conduct_loo(group, summary_type, all_rois, all_networks):
    print('Conducting LOO...')


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
        group_fc = np.median(group_fc, axis = 0)
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
    conduct_loo(group, summary_type, all_rois, all_networks)

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