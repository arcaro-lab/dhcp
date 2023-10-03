'''
Phase 4 of registration pipeline: Registers anat to EPI
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

#take subjectand session as command line argument
sub = sys.argv[1]
ses = sys.argv[2]

#set sub dir
anat_input = f'{params.out_dir}/{sub}/{ses}'
func_input = f'{params.raw_func_dir}/{sub}/{ses}'
out_dir = f'{params.out_dir}/{sub}/{ses}'

anat = f'anat/{sub}_{ses}_{params.anat_suf}' 
func = f'func/{sub}_{ses}_{params.func_suf}'

#create 1 volume func file
bash_cmd = f'fslmaths {func_input}/{func}.nii.gz -Tmean {out_dir}/{func}_1vol.nii.gz'
subprocess.run(bash_cmd.split(), check = True)

#create registration matrix for func2anat
bash_cmd = f'flirt -in {out_dir}/{func}_1vol.nii.gz -ref {anat_input}/{anat}_brain.nii.gz -omat {out_dir}/xfm/func2anat.mat -bins 256 -cost corratio -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 12'
subprocess.run(bash_cmd.split(), check = True)

#apply registration to 1vol func data
bash_cmd = f'flirt -in {out_dir}/{func}_1vol.nii.gz -ref {anat_input}/{anat}_brain.nii.gz -out {out_dir}/{func}_1vol_reg.nii.gz -applyxfm -init {out_dir}/xfm/func2anat.mat -interp trilinear'
subprocess.run(bash_cmd.split(), check = True)

#create registration matrix for anat2func
bash_cmd = f'flirt -in {anat_input}/{anat}_brain.nii.gz -ref {out_dir}/{func}_1vol.nii.gz -omat {out_dir}/xfm/anat2func.mat -bins 256 -cost corratio -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 12'
subprocess.run(bash_cmd.split(), check = True)

#apply registration to anat data
bash_cmd = f'flirt -in {anat_input}/{anat}_brain.nii.gz -ref {out_dir}/{func}_1vol.nii.gz -out {out_dir}/{anat}_brain_func.nii.gz -applyxfm -init {out_dir}/xfm/anat2func.mat -interp trilinear'
subprocess.run(bash_cmd.split(), check = True)

