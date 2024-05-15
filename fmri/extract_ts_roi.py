'''
Extract mean timeseries from a set of ROIs
'''

project_name = 'dhcp'
import os
#get current working directory
cwd = os.getcwd()
git_dir = cwd.split(project_name)[0] + project_name
import sys

#add git_dir to path
sys.path.append(git_dir)


import subprocess
import numpy as np
import pandas as pd
from glob import glob as glob
import dhcp_params as params
import pdb

import matplotlib.pyplot as plt
from nilearn import plotting, image
import nibabel as nib
import shutil
import pdb
import gc

from nilearn.maskers import NiftiMasker
from nilearn.maskers import NiftiLabelsMasker
import warnings
warnings.filterwarnings("ignore")

#take subjectand session as command line argument
sub = sys.argv[1]
group = sys.argv[2]
atlas = sys.argv[3]

#sub-CC00056XX07 ses-10700 wang
group_info = params.load_group_params(group)


#set sub dir
anat_dir = glob(f'{group_info.raw_anat_dir}/{sub}/ses-*')[0]
func_dir = glob(f'{group_info.raw_func_dir}/{sub}/ses-*')[0]
out_dir = glob(f'{group_info.out_dir}/{sub}/ses-*')[0]
atlas_dir = params.atlas_dir


#extract ses 
ses = 'ses-' + anat_dir.split('ses-')[1]



results_dir = f'{out_dir}/derivatives/timeseries'
os.makedirs(results_dir, exist_ok = True)

os.makedirs(f'{group_info.out_dir}/derivatives/fc_matrix', exist_ok = True)


roi_dir = f'{out_dir}/rois/{atlas}'


atlas_info= params.load_atlas_info(atlas)

atlas_name, roi_labels = atlas_info.atlas_name, atlas_info.roi_labels
#glob all func files
func_files = glob(f'{func_dir}/func/*_bold.nii.gz')

#loop through func files
all_func = []

    

gc.collect()

all_ts = []
#loop through rois in labels file
for hemi in ['lh','rh']:
    print(f'Extracting {atlas} {hemi} timeseries for {sub}...')

    curr_atlas = atlas_name.replace('hemi', hemi)
    
    #load roi
    atlas_dir = f'{out_dir}/atlas/{curr_atlas}_epi.nii.gz'
    
    #extract roi timeseries
    masker = NiftiLabelsMasker(
        labels_img=atlas_dir,
        standardize="zscore",
        standardize_confounds="zscore",
        smoothing_fwhm=params.smooth_mm)    

    all_runs = []
    for n, func_file in enumerate(func_files):
        
        #load func
        try:

            func_img = image.load_img(func_file)
            
            
        except:
            print(f'Error loading {func_file}')
            continue
        

        roi_ts = masker.fit_transform(func_img)

        

        #append to all_ts
        all_runs.append(roi_ts)

        gc.collect()
    
    

    #concatenate all runs
    roi_ts = np.concatenate(all_runs, axis = 0)

    
    #save
    np.save(f'{results_dir}/{sub}_{ses}_{atlas}_{hemi}_ts.npy', roi_ts)

    #append to all_ts
    all_ts.append(roi_ts)

            


#convert to numpy array
all_ts = np.concatenate(all_ts, axis = 1)

#transpose
all_ts = all_ts.T


#compute correlation matrix across all rois
corr_mat = np.corrcoef(all_ts)

#save
np.save(f'{group_info.out_dir}/derivatives/fc_matrix/{sub}_{atlas}_fc.npy', corr_mat)

