'''
Split atlas into ROIs
'''

git_dir = '/mnt/c/Users/ArcaroLab/Desktop/git_repos/dhcp'

import os
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
import warnings
warnings.filterwarnings("ignore")

#take subjectand session as command line argument
sub = sys.argv[1]
ses = sys.argv[2]
atlas = sys.argv[3]

#sub-CC00056XX07 ses-10700 wang


#set sub dir
anat_dir = f'{params.raw_anat_dir}/{sub}/{ses}'
func_dir = f'{params.raw_func_dir}/{sub}/{ses}'
out_dir = f'{params.out_dir}/{sub}/{ses}'
atlas_dir = params.atlas_dir

results_dir = f'{out_dir}/derivatives/timeseries'
os.makedirs(results_dir, exist_ok = True)

os.makedirs(f'{params.out_dir}/derivatives/fc_matrix', exist_ok = True)


roi_dir = f'{out_dir}/rois/{atlas}'

atlas_name, roi_labels = params.load_roi_info(atlas)

#glob all func files
func_files = glob(f'{func_dir}/func/*_bold.nii.gz')

#loop through func files
all_func = []
for n, func_file in enumerate(func_files):
    
    #load func
    try:

        curr_img = image.load_img(func_file)
        
    except:
        print(f'Error loading {func_file}')
        continue
    
    all_func.append(curr_img)
    del curr_img

#concatenate all func files
func_img = image.concat_imgs(all_func)


del all_func
gc.collect()


all_ts = []
#loop through rois in labels file
for roi_name in roi_labels['label']:
    for hemi in params.hemis:
        print(f'Extracting {roi_name} {hemi} timeseries for {sub}...')
        
        #load roi
        roi_img = image.load_img(f'{roi_dir}/{hemi}_{roi_name}_epi.nii.gz')
        

        #extract roi timeseries
        masker = NiftiMasker(mask_img = roi_img, standardize = True, smoothing_fwhm=params.smooth_mm)
        del roi_img        

        roi_ts = masker.fit_transform(func_img)
        print('roi_ts shape: ', roi_ts.shape)
        
        #save multivariate timeseries
        np.save(f'{results_dir}/{hemi}_{roi_name}.npy', roi_ts)

        #average across voxels
        mean_ts = np.mean(roi_ts, axis = 1)

        #append to all_ts
        all_ts.append(mean_ts)

        gc.collect()
                



#convert to numpy array
all_ts = np.array(all_ts)

#compute correlation matrix across all rois
corr_mat = np.corrcoef(all_ts)

#save
np.save(f'{params.out_dir}/derivatives/fc_matrix/{sub}_{atlas}_fc.npy', corr_mat)

