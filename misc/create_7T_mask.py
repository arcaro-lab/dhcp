'''
Create 7T brain mask
'''


git_dir = '/mnt/c/Users/ArcaroLab/Desktop/git_repos/dhcp'

import os
import sys
#add git_dir to path
sys.path.append(git_dir)

import subprocess
import dhcp_params as params
import pandas as pd


raw_data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf, brain_mask_suf, group_template,template_name = params.load_group_params('adult')

#load participant file
sub_file = pd.read_csv(f'{out_dir}/participants.csv')

#convert Atlas_wmparc.1.60.nii.gz to brain mask
source_file_dir = f'MNINonLinear/ROIs/Atlas_wmparc.1.60.nii.gz'

for sub in sub_file['participant_id']:
    sub_dir = f'{out_dir}/{sub}/ses-01'

    target_file =  f'{sub_dir}/anat/{sub}_ses-01_{anat_suf}_mask.nii.gz'
    source_file = f'{sub_dir}/{source_file_dir}'
    

    #use fslmaths to convert atlas to brain mask
    bash_cmd = f'fslmaths {source_file} -bin {target_file}'
    subprocess.run(bash_cmd, shell=True,check=True)


    


