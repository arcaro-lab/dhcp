'''
Conduct brain extraction by using segmentation mask

*This is mostly neeeded for volumentric ROI registration
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



#set sub dir
anat_input = f'{params.raw_anat_dir}/{sub}/{ses}'
func_input = f'{params.raw_func_dir}/{sub}/{ses}'
out_dir = f'{params.out_dir}/{sub}/{ses}'

anat = f'anat/{sub}_{ses}_{params.anat_suf}' 
brain_mask = f'anat/{sub}_{ses}_{params.brain_mask_suf}'


#binarize brain mask
bash_cmd = f'fslmaths {anat_input}/{brain_mask}.nii.gz -bin {out_dir}/{brain_mask}.nii.gz'
subprocess.run(bash_cmd, shell=True)

#check if file exists
# if os.path.isfile(f'{out_dir}/anat/{brain_mask}.nii.gz'):
#     print(f'Brain mask for {sub} {ses} exists')

#apply brain mask to anat
bash_cmd = f'fslmaths {anat_input}/{anat}.nii.gz -mas {out_dir}/{brain_mask}.nii.gz {out_dir}/{anat}_brain.nii.gz'
subprocess.run(bash_cmd, shell=True)


