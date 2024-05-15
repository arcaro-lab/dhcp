'''
Phase 4 of registration pipeline: Registers anat to EPI
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
import dhcp_params
import pdb

#take subjectand session as command line argument
sub = sys.argv[1]
#take subjectand session as command line argument
sub = sys.argv[1]
group = sys.argv[2]

group_info = dhcp_params.load_group_params(group)

ses = 'ses-'+glob(f'{group_info.raw_func_dir}/{sub}/ses-*')[0].split('ses-')[1]
#set sub dir
anat_input = f'{group_info.out_dir}/{sub}/{ses}'
func_input = f'{group_info.raw_func_dir}/{sub}/{ses}'
out_dir = f'{group_info.out_dir}/{sub}/{ses}'

anat = f'anat/{sub}_{ses}_{group_info.anat_suf}' 
func = f'func/{sub}_{ses}_{group_info.func_suf}'

func2anat_xfm = group_info.func2anat_xfm.replace('*SUB*',sub).replace('*SES*',ses)
anat2func_xfm = group_info.anat2func_xfm.replace('*SUB*',sub).replace('*SES*',ses)

#apply registration to 1vol func data
bash_cmd = f'flirt -in {out_dir}/{func}_1vol.nii.gz -ref {anat_input}/{anat}_brain.nii.gz -out {out_dir}/{func}_1vol_reg.nii.gz -applyxfm -init {func2anat_xfm} -interp trilinear'
subprocess.run(bash_cmd.split(), check = True)


#apply registration to anat data
bash_cmd = f'flirt -in {anat_input}/{anat}_brain.nii.gz -ref {out_dir}/{func}_1vol.nii.gz -out {out_dir}/{anat}_brain_func.nii.gz -applyxfm -init {anat2func_xfm} -interp trilinear'
subprocess.run(bash_cmd.split(), check = True)

