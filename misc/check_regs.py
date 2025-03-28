'''
Group QC files by age group
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
from nilearn import plotting, image

import pdb

import warnings
warnings.filterwarnings("ignore")

group = 'infant'
atlas = 'wang'
suf = ''

age_bins = [26,33, 38,42,46]
age_groups = ['pre','early','term','post']


#load atlast name and roi labels
atlas_info = params.load_atlas_info(atlas)
group_info = params.load_group_params(group)

roi_labels = atlas_info.roi_labels

#expand roi labels to include hemis
all_rois = []
all_networks = []



#load group data
sub_info = group_info.sub_list

sub_info['age'] = sub_info['scan_age'] - sub_info['birth_age']*7
sub_info['age_group'] = np.nan

for i in range(len(age_bins)-1):
    sub_info.loc[(sub_info['scan_age'] >= age_bins[i]) & (sub_info['scan_age'] < age_bins[i+1]), 'age_group'] = age_groups[i]

    #create age_group folder in qc folder
    os.makedirs(f'{git_dir}/fmri/qc/wang/infant/{age_groups[i]}', exist_ok=True)

n = 0
#loop through subjects and copy qc files to age_group folder
for sub, ses,age_group in zip(sub_info['participant_id'], sub_info['ses'], sub_info['age_group']):
    sub_dir = f'{group_info.out_dir}/{sub}/{ses}/'

    func_img = f'{sub_dir}/func/{sub}_{ses}_{group_info.func_suf}_1vol.nii.gz'
    try:
        #create subplot for each hemi
        fig, ax = plt.subplots(2,1, figsize=(4,6))
        for hemi in ['lh','rh']:
            atlas_img =f'{sub_dir}/atlas/{atlas_info.atlas_name}_epi.nii.gz'.replace('hemi',hemi)

            plotting.plot_roi(atlas_img, bg_img = func_img, axes = ax[group_info.hemis.index(hemi)], alpha = .4, title = f'{sub} {hemi} {atlas}',draw_cross=False) 

        out_file = f'{git_dir}/fmri/qc/wang/infant/{age_group}/{sub}_{ses}_{atlas}_epi.png'
        plt.savefig(out_file)
        plt.close()
    except:
        print(f'Error: {sub} {ses}')
        continue
    n += 1
    print(f'{n}/{len(sub_info)}')


        


