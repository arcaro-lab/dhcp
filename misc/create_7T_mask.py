'''
Create 7T brain mask
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
import dhcp_params as params
import pandas as pd


group_info = params.load_group_params('adult')
out_dir = group_info.out_dir
anat_suf = group_info.anat_suf

#load participant file
sub_file = pd.read_csv(f'{git_dir}/participants_7T.csv')

#convert Atlas_wmparc.1.60.nii.gz to brain mask
source_file_dir = f'MNINonLinear/ROIs/Atlas_wmparc.1.60.nii.gz'

for sub in sub_file['participant_id']:
    print(sub)
    sub_dir = f'{out_dir}/{sub}/ses-01'

    target_file =  f'{sub_dir}/anat/{sub}_ses-01_{anat_suf}_mask.nii.gz'
    source_file = f'{sub_dir}/{source_file_dir}'
    

    #use fslmaths to convert atlas to brain mask
    bash_cmd = f'fslmaths {source_file} -bin {target_file}'
    subprocess.run(bash_cmd, shell=True,check=True)


    


