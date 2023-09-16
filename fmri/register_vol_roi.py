'''
Runs volumetric ROI registration with ANTs
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

#take subject and session as command line argument
sub = sys.argv[1]
ses = sys.argv[2] 
roi = sys.argv[3]

roi_name, template, template_name = params.load_roi_info(roi)

#set sub dir
anat_input = f'{params.raw_anat_dir}/{sub}/{ses}'
func_input = f'{params.raw_func_dir}/{sub}/{ses}'
data_dir = f'{params.out_dir}/{sub}/{ses}'
atlas_dir = params.atlas_dir

anat = f'anat/{sub}_{ses}_{params.anat_suf}_brain' 

os.makedirs(f'{data_dir}/rois/{roi}', exist_ok=True)

#create transformations from template to anat
bash_cmd =f'antsRegistrationSyN.sh -f {data_dir}/{anat}.nii.gz -m {atlas_dir}/{template}.nii.gz -d 3 -o {data_dir}/xfm/{template_name}2anat -n 4'
subprocess.run(bash_cmd, shell=True)

for hemi in params.hemis:
    curr_roi = roi_name.replace('hemi', hemi)



    #apply transformations to roi
    bash_cmd = f"antsApplyTransforms \
        -d 3 \
            -i {atlas_dir}/{curr_roi}.nii.gz \
                -r  {data_dir}/{anat}.nii.gz \
                    -t {data_dir}/xfm/{template_name}2anat1Warp.nii.gz \
                        -t {data_dir}/xfm/{template_name}2anat0GenericAffine.mat \
                            -o {data_dir}/rois/{roi}_{hemi}.nii.gz"
    subprocess.run(bash_cmd, shell=True)
