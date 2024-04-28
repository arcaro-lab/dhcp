'''
whole brain correlations between atlas and brain
'''
project_name = 'dhcp'
import os
#get current working directory
cwd = os.getcwd()
git_dir = cwd.split(project_name)[0] + project_name
import sys

#add git_dir to path

sys.path.append(git_dir)

import pandas as pd
from nilearn import image, plotting, masking
#from nilearn.glm import threshold_stats_img
import numpy as np

from nilearn.maskers import NiftiMasker

import nibabel as nib
import os

import pdb

import warnings
warnings.filterwarnings("ignore")

import dhcp_params as params
import subprocess

group = 'infant'

raw_data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf, brain_mask_suf, group_template,template_name = params.load_group_params(group)


analysis_name = 'whole_brain'
seed_atlas = 'wang'
target_roi = 'pulvinar'

#analysis_name = 'thalmocortical'
#seed_atlas = 'wang'
#target_roi = 'pulvinar'
#load subject list
#load subject list
sub_list = pd.read_csv(f'{git_dir}/participants.csv')
sub_list = sub_list[sub_list[f'{seed_atlas}_ts'] == 1]
#sub_list = sub_list[sub_list[f'{target_roi}_reg'] == 1]

#load atlas info
#atlas_name, roi_labels = params.load_atlas_info(seed_atlas)

atlas_name, atlas_labels = params.load_atlas_info(seed_atlas)
'''
#load target atlas info
try:
    target_name, target_labels = params.load_atlas_info(target_roi)
    target_dir = f'atlas/{target_name}_epi.nii.gz'
except:
    target_name = target_roi
    target_name = params.load_roi_info(target_roi)
    target_dir = f'rois/{target_roi}/hemi_{target_roi}_epi.nii.gz'
'''
#sub = sys.argv[1]
#ses = sys.argv[2]
#atlas = sys.argv[3]
#target = sys.argv[4]
target_name = target_roi
target_dir = f'rois/{target_roi}/hemi_{target_roi}.nii.gz'

template = '40wk'

for hemi in params.hemis:

    
    roi = image.load_img(f'{out_dir}/atlases/rois/{target_roi}/{template}/{target_roi}_{hemi}.nii.gz')

    #load hemi mask
    hemi_mask = image.load_img(f'{out_dir}/atlases/rois/{hemi}_mask_{template}.nii.gz')

    #binarize both
    roi = image.binarize_img(roi)
    hemi_mask = image.binarize_img(hemi_mask)

    #mask roi with hemi mask
    masked_roi = image.math_img('roi * mask', roi = roi, mask = hemi_mask)


    #create a masker
    masker = NiftiMasker(mask_img=masked_roi, standardize=True)
    #loop through subjects
    for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
        target_file = f'{out_dir}/{sub}/{ses}/{target_dir}'
        source_dir = f'{out_dir}/{sub}/{ses}/derivatives/whole_brain'
        results_dir = f'{out_dir}/{sub}/{ses}/derivatives/{target_roi}'

        os.makedirs(results_dir, exist_ok = True)
        print(f'Extracting map for {sub} {ses}')

        for n, roi in enumerate(atlas_labels['label']):
            whole_brain_img = image.load_img(f'{source_dir}/{hemi}_{roi}_corr_{template}.nii.gz')

            #mask whole brain image with roi mask
            roi_vals = masker.fit_transform(whole_brain_img)

            #convert back to nifti
            roi_img = masker.inverse_transform(roi_vals)

            #make 0s nans
            roi_img = image.math_img('np.where(img == 0, np.nan, img)', img = roi_img)

            #save image
            roi_img.to_filename(f'{results_dir}/{hemi}_{roi}_corr_{template}.nii.gz')

            




