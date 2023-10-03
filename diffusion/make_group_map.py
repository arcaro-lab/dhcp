'''
Create mean maps for diffusion data
'''

git_dir = '/mnt/c/Users/ArcaroLab/Desktop/git_repos/dhcp'
import sys
#add git_dir to path
sys.path.append(git_dir)
import pandas as pd
from nilearn import image, plotting, masking
#from nilearn.glm import threshold_stats_img
import numpy as np
import scipy.stats as stats

from nilearn.maskers import NiftiMasker

import nibabel as nib
import os

import pdb
from glob import glob as glob

import warnings
import dhcp_params as params
import subprocess

atlas = 'wang'
#load params
data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf, brain_mask_suf, group_template,template_name = params.load_group_params('diffusion')

analysis_type = 'Seeds'
data_types = ['distcorr_normmax','distcorr','nodistcorr','nodistcorr_normmax']
file_sufs = ['normmax','normmax_thr_liberal','normmax_thr_middle','normmax_thr_strict']

#create nested dictionary with suffixes

#load atlas info
atlas_name, roi_labels= params.load_atlas_info(atlas)
#replace V1v and V1d with V1
roi_labels['label'] = roi_labels['label'].replace(['V1v','V1d'],'V1')
#remove duplicates
roi_labels = roi_labels.drop_duplicates(subset=['label'])

target_dir = f'{data_dir}/{analysis_type}'


templates = ['40week','MNI']

for template in templates:
    for data_type in data_types:
        #create groupmaps folder in target_dir
        group_dir = f'{target_dir}/{template}/{data_type}/groupmaps'


    #loop through rois and create mean maps
    for roi in roi_labels['label']:
        for hemi in params.hemis:
            roi_dir = f'{target_dir}/{template}/{data_type}/{roi}_{hemi}'

            for suf in file_sufs:
                #check if directory exists
                #glob all files in directory
                
                files = glob(f'{roi_dir}/*{suf}.nii.gz')

                pdb.set_trace()




