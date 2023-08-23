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

#take subjectand session as command line argument
sub = sys.argv[1]
ses = sys.argv[2]
atlas = sys.argv[3]

#set sub dir
anat_dir = f'{params.raw_anat_dir}/{sub}/{ses}'
func_dir = f'{params.raw_func_dir}/{sub}/{ses}'
out_dir = f'{params.out_dir}/{sub}/{ses}'
atlas_dir = params.atlas_dir

roi_dir = f'{out_dir}/rois'

atlas_name, roi_labels = params.load_roi_info(atlas)

#if atlas dir exists, delete it
if os.path.exists(f'{roi_dir}/{atlas}'):
    shutil.rmtree(f'{roi_dir}/{atlas}')

os.makedirs(f'{roi_dir}/{atlas}', exist_ok = True)



for hemi in params.hemis:
    #replace hemi in atlas name with current hemi
    curr_atlas = atlas_name.replace('hemi', hemi)
    

    #load atlas
    atlas_img = image.load_img(f'{out_dir}/atlas/{curr_atlas}_epi.nii.gz')

    #loop through rois in labels file
    for roi_ind, roi in zip(roi_labels['index'],roi_labels['label']):
        #extract current roi
        roi_atlas = image.math_img(f'np.where(atlas == {roi_ind}, atlas, 0)', atlas = atlas_img)

        #save roi
        nib.save(roi_atlas, f'{roi_dir}/{atlas}/{hemi}_{roi}_epi.nii.gz')
        
        #binarize and fill holes in roi using fsl
        bash_cmd = f'fslmaths {roi_dir}/{atlas}/{hemi}_{roi}_epi.nii.gz -bin -fillh {roi_dir}/{atlas}/{hemi}_{roi}_epi.nii.gz'
        subprocess.run(bash_cmd.split(), check = True)



        

    

