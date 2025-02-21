'''
Register rois to template
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
import matplotlib.pyplot as plt
import pdb
from nilearn import plotting, image
import shutil
import matplotlib
matplotlib.use('Agg')

#take subject and session as command line argument
sub = sys.argv[1]
ses = sys.argv[2] 


atlas = 'wang'
#load atlas info
atlas_name, roi_labels= params.load_atlas_info(atlas)
atlas_dir = params.atlas_dir

#load subject info
raw_data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf, brain_mask_suf, group_template,template_name = params.load_group_params('infant')

sub_dir = f'{out_dir}/{sub}/{ses}'

roi_dir = f'{sub_dir}/rois/{atlas}'
anat = f'anat/{sub}_{ses}_{params.anat_suf}_brain' 
func = f'func/{sub}_{ses}_{params.func_suf}_1vol'
#create transformations from template to anat
bash_cmd =f'antsRegistrationSyN.sh -f {sub_dir}/{func}.nii.gz -m {atlas_dir}/templates/{group_template}.nii.gz -d 3 -o {sub_dir}/xfm/{template_name}2epi -n 4'
subprocess.run(bash_cmd, shell=True)


#loop through rois and register to template
for hemi in params.hemis:
    for roi in roi_labels['label']:
        curr_roi = f'{hemi}_{roi}'



        #apply transformations to roi
        bash_cmd = f"antsApplyTransforms \
            -d 3 \
                -i {roi_dir}/{curr_roi}_epi.nii.gz \
                    -r  {out_dir}/templates/{group_template}.nii.gz \
                        -t {sub_dir}/xfm/{template_name}2anat1InverseWarp.nii.gz \
                            -t [{sub_dir}/xfm/{template_name}2anat0GenericAffine.mat, 1] \
                                -o {atlas_dir}/rois/{atlas}/{template_name}/{curr_roi}_{template_name}.nii.gz \
                                    -n NearestNeighbor"
        subprocess.run(bash_cmd, shell=True)

        #binarize roi
        bash_cmd = f"fslmaths {atlas_dir}/rois/{atlas}/{template_name}/{curr_roi}_{template_name}.nii.gz -bin {atlas_dir}/rois/{atlas}/{template_name}/{curr_roi}_{template_name}.nii.gz"
        subprocess.run(bash_cmd, shell=True)




