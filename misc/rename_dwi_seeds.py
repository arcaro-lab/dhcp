'''
Rename files in dwi_seeds to include seed roi
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

import shutil
import pdb

#add timing code
import time

#load dhcp_params for infants
group_info = dhcp_params.load_group_params('infant')

#load sub_info
sub_list = group_info.sub_list
#extract only subs where wang_probtrackx = 1
sub_list = sub_list[sub_list['wang_probtrackx'] == 1]
seed_roi = 'pulvinar'

for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
    seed_dir = f'{group_info.out_dir}/{sub}/{ses}/derivatives/dwi_seeds'
    paths_dir = f'{group_info.out_dir}/{sub}/{ses}/derivatives/dwi_paths'


    #glob all files in seed_dir
    seeds = glob(f'{seed_dir}/*.nii.gz')

    #loop through seeds and rename to add seed_roi at the front
    for seed in seeds:
        #check if seed file already contains seed_roi
        if seed_roi in seed:
            continue


        seed_name = seed.split('/')[-1].split('.')[0]
        new_seed = f'{seed_dir}/{seed_roi}_{seed_name}.nii.gz'
        
        os.rename(seed, new_seed)

    #loop through paths and rename to add seed_roi at the front
    paths = glob(f'{paths_dir}/*.nii.gz')
    for path in paths:
        #check if path file already contains seed_roi
        if seed_roi in path:
            continue

        path_name = path.split('/')[-1].split('.')[0]
        new_path = f'{paths_dir}/{seed_roi}_to_{path_name}.nii.gz'
        os.rename(path, new_path)

    





