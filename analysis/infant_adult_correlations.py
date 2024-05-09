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

from sklearn.manifold import MDS
import pdb

import warnings
#warnings.filterwarnings("ignore")

atlas = 'wang'


#load atlast name and roi labels
atlas_name, roi_labels = params.load_atlas_info(atlas)

sub_info = pd.read_csv(f'{git_dir}/participants_dhcp.csv')

age_groups = ['infant', 'adult']


networks = ['EVC', 'ventral', 'lateral', 'dorsal']
network_colors = ['#fd0000', '#be00fd', '#1105d8', 'green']

#expand roi labels to include hemis
all_rois = []
all_networks = []






summary_type = 'within_hemi_fc'

if summary_type == 'fc':
    all_rois = []
    all_networks = []
    for roi in roi_labels['label']:
        for hemi in params.hemis:
            all_rois.append(f'{hemi}_{roi}')
            all_networks.append(roi_labels[roi_labels['label'] == roi]['network'].values[0])

elif summary_type == 'within_hemi_fc' or summary_type == 'within_hemi_fc':
    all_rois = list(roi_labels['label'])
    all_networks = list(roi_labels['network'])
    hemi = 'both'

''' 
Load and organize group adult fc matrix
'''
#load median fc matrix for adults
adult_fc = pd.read_csv(f'{params.results_dir}/group_fc/adult_{atlas}_median_{summary_type}.csv', header = None).values

#set diagonal to nan
np.fill_diagonal(adult_fc, np.nan)

#convert to pandas dataframe and melt
adult_df = pd.DataFrame(adult_fc, index = all_rois, columns = all_rois)


#melt so that you have an roi1 and roi1 column
adult_df = adult_df.melt(var_name = 'roi2', value_name = 'fc', ignore_index = False).reset_index().rename(columns = {'index':'roi1'})
adult_df = adult_df.dropna()

#add network labels
adult_df['network1'] = [all_networks[all_rois.index(roi)] for roi in adult_df['roi1']]
adult_df['network2'] = [all_networks[all_rois.index(roi)] for roi in adult_df['roi2']]

if summary_type == 'fc':
    #split roi into hemi and roi
    adult_df['hemi1'] = adult_df['roi1'].apply(lambda x: x.split('_')[0])
    adult_df['roi1'] = adult_df['roi1'].apply(lambda x: x.split('_')[1])

    adult_df['hemi2'] = adult_df['roi2'].apply(lambda x: x.split('_')[0])
    adult_df['roi2'] = adult_df['roi2'].apply(lambda x: x.split('_')[1])

'''
Calculate correlations for all rois
'''

summary_df = pd.DataFrame(columns = ['sub', 'sex','birth_age', 'scan_age', 'hemi', 'infant_roi','infant_network','adult_roi','adult_network', 'roi_similarity','network_similarity','corr' ])




group= 'infant'
raw_data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf, brain_mask_suf, group_template,template_name = params.load_group_params(group)
#load individual infant data
infant_fc = np.load(f'{out_dir}/derivatives/fc_matrix/{group}_{atlas}_{summary_type}.npy')




for i in range(infant_fc.shape[0]):
    print(i + 1, '/',infant_fc.shape[0])
    sub = sub_info['participant_id'][i]
    sex = sub_info['sex'][i]
    birth_age = sub_info['birth_age'][i]
    scan_age = sub_info['scan_age'][i]

    curr_fc = infant_fc[i,:,:]
    #set diagonal to nan
    np.fill_diagonal(curr_fc, np.nan)

    #melt so that you have an roi1 and roi1 column
    curr_df = pd.DataFrame(curr_fc, index = all_rois, columns = all_rois)
    curr_df = curr_df.melt(var_name = 'roi2', value_name = 'fc', ignore_index = False).reset_index().rename(columns = {'index':'roi1'})
    curr_df = curr_df.dropna()
    
    #add network labels
    curr_df['network1'] = [all_networks[all_rois.index(roi)] for roi in curr_df['roi1']]
    curr_df['network2'] = [all_networks[all_rois.index(roi)] for roi in curr_df['roi2']]

    #split roi into hemi and roi
    #curr_df['hemi1'] = curr_df['roi1'].apply(lambda x: x.split('_')[0])
    #curr_df['roi1'] = curr_df['roi1'].apply(lambda x: x.split('_')[1])
    #curr_df['hemi2'] = curr_df['roi2'].apply(lambda x: x.split('_')[0])
    #curr_df['roi2'] = curr_df['roi2'].apply(lambda x: x.split('_')[1])

    


    #for hemi in ['lh','rh']:
    #loop through rois and calculate correlation
    for infant_roi, infant_network in zip(roi_labels['label'], roi_labels['network']):
        infant_data = curr_df[(curr_df['roi1'] == infant_roi)]

        for adult_roi, adult_network in zip(roi_labels['label'], roi_labels['network']):
            adult_data = adult_df[(adult_df['roi1'] == adult_roi)]
            #pdb.set_trace()

            #calculate correlation
            corr = np.corrcoef(infant_data['fc'], adult_data['fc'])[0,1]

            if infant_roi == adult_roi:
                roi_sim = 'same'
            else:
                roi_sim = 'diff'

            if infant_network == adult_network:
                net_sim = 'same'
            else:
                net_sim = 'diff'


            #add to summary_df
            curr_data = [sub, sex, birth_age, scan_age, hemi, infant_roi, infant_network, adult_roi, adult_network, roi_sim, net_sim, corr]
            summary_df.loc[len(summary_df)] = curr_data

        


#save 
summary_df.to_csv(f'{params.results_dir}/infant_adult_roi_similarity_{summary_type}.csv', index = False)
