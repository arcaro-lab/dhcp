'''
Append adult similarity data to infant similarity data
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

from sklearn.manifold import MDS
import pdb

import warnings
warnings.filterwarnings("ignore")

atlas = 'wang'

summary_type = 'fc'

#load atlast name and roi labels
atlas_info = params.load_atlas_info(atlas)

roi_labels = atlas_info.roi_labels


infant_params = params.load_group_params('infant')
adult_params = params.load_group_params('adult')
#load individual infant data

os.makedirs(f'{infant_params.out_dir}/derivatives/{atlas}', exist_ok=True)

#infant_fc = infant_fc[0:30,:,:]

sub_info = infant_params.sub_list
sub_info = sub_info[(sub_info[f'{atlas}_ts'] == 1) & (sub_info[f'{atlas}_exclude'] != 1)]

infant_data = pd.read_csv(f'{infant_params.out_dir}/derivatives/{atlas}/infant_{atlas}_roi_similarity.csv')
#sub_info = sub_info.head(30)

age_groups = ['infant', 'adult']

networks = ['Occipital', 'Ventral', 'Lateral', 'Dorsal']

#expand roi labels to include hemis
all_rois = []
all_networks = []

#flag whether to rerun correlations
re_run = True

all_rois = []
all_networks = []
for roi in roi_labels['label']:
    for hemi in params.hemis:
        all_rois.append(f'{hemi}_{roi}')
        all_networks.append(roi_labels[roi_labels['label'] == roi]['network'].values[0])




''' 
Load and organize group adult fc matrix
'''

#load median fc matrix for adults
adult_data = pd.read_csv(f'{adult_params.out_dir}/derivatives/{atlas}/adult_{atlas}_roi_similarity.csv')

adult_df = adult_data.groupby(by=['hemi1', 'network1','roi1', 'hemi2','network2','roi2']).median(numeric_only=True).reset_index()

#sort adult data by hemi2, roi2
adult_df = adult_df.sort_values(by=['hemi2', 'roi2'])

#add adult data to infant data as new columns

infant_data['adult_fc'] = np.nan

#loop through adult data and add to infant data
for ii in range(0, len(adult_df)):
    print(ii, len(adult_df))
    #add adult fc where hemi1,roi1, hemi2, roi2 match
    infant_data.loc[(infant_data['hemi1'] == adult_df['hemi1'][ii]) & (infant_data['roi1'] == adult_df['roi1'][ii]) & (infant_data['hemi2'] == adult_df['hemi2'][ii]) & (infant_data['roi2'] == adult_df['roi2'][ii]), 'adult_fc'] = adult_df['fc'][ii]


#save new infant data
infant_data.to_csv(f'{infant_params.out_dir}/derivatives/{atlas}/infant_adult_{atlas}_roi_similarity.csv', index=False)
