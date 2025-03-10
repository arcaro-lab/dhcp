'''
register waypoints and exclusion masks to 40wk
'''

project_name = 'dhcp'
import os
#get current working directory
cwd = os.getcwd()
git_dir = cwd.split(project_name)[0] + project_name
import sys

#add git_dir to path

sys.path.append(git_dir)

import pandas as pd
from nilearn import image, plotting, masking
#from nilearn.glm import threshold_stats_img
import numpy as np

from nilearn.maskers import NiftiMasker

import nibabel as nib
import os

import pdb

import warnings
warnings.filterwarnings("ignore")

import dhcp_params as params
import subprocess
from glob import glob as glob
import shutil


def reg_to_template():
    '''
    register exclusion and waypoint masks to 40wk template
    '''

    source_sub = 'sub-CC00071XX06'
    source_ses = 'ses-27000'

    source_dir = f'/mnt/DataDrive3/vlad/diffusion/individual_subjects/{source_sub}/{source_ses}'
    xfm = f'{source_dir}/xfm/{source_sub}_{source_ses}_from-dwi_to-extdhcp40wk_mode-image.nii.gz'

    exclusion_file ='binaryMask_dwispace_*hemi*'

    waypoint_file = f'*roi*_*hemi*_{source_sub}_waypoint_mask_dwispace.nii.gz'

    infant_params = params.load_group_params('infant')
    template = f'{infant_params.group_template}.nii.gz'

    target_dir = f'{params.atlas_dir}/diffusion_wangatlas/40wk'


    '''
    #THIS IS NOT CORRECT    
    for hemi in ['lh', 'rh']:
        print('registering exclusion mask')
        
        #apply transform to exclusion mask
        bash_cmd = f'applywarp --ref={template} --in={source_dir}/exclusionmasks/{exclusion_file.replace('*hemi*', hemi)}.nii --warp={xfm} --out={target_dir}/{exclusion_file.replace('*hemi*', hemi)}_40wk.nii'
        subprocess.run(bash_cmd, shell=True)
    '''
    
    #glob all waypoint files
    waypoint_files = glob(f'{source_dir}/waypointmasks/*.nii.gz')

    for waypoint_file in waypoint_files:
        
        out_file = waypoint_file.replace('waypoints', 'waypoints_40wk').replace(source_dir, target_dir).replace(source_sub+'_', '')
        
        #apply transform to waypoint mask
        bash_cmd = f'applywarp --ref={template} --in={waypoint_file} --warp={xfm} --out={out_file}'
        subprocess.run(bash_cmd, shell=True)
    
reg_to_template()
'''
Register exclusion and waypoint masks from 40wk template to individual subjects
'''

print('Registering exclusion and waypoint masks to individual subjects')
group_params = params.load_group_params('infant')
#load individual infant data
sub_info = group_params.sub_list
sub_info = sub_info[(sub_info[f'wang_ts'] == 1) & (sub_info[f'wang_exclude'] != 1)]


#load only subs with two sessions
sub_info = sub_info[sub_info.duplicated(subset = 'participant_id', keep = False)]
sub_info = sub_info.reset_index()

#loop through subs and register exclusion and waypoint masks
source_dir = f'{params.atlas_dir}/diffusion_wangatlas/40wk'

#glob exclusion and waypoint masks
exclusion_files = glob(f'{source_dir}/exclusionmasks/*.nii.gz')
waypoint_files = glob(f'{source_dir}/waypointmasks/*.nii.gz')



n = 0 
#loop through subjects
for sub, ses in zip(sub_info['participant_id'], sub_info['ses']):
    #print progress
    n += 1
    print(f'{n}/{len(sub_info)}', sub, ses)
    #set sub_dir
    sub_dir = f'{group_params.out_dir}/{sub}/{ses}'
    
    #get xfm for sub
    xfm = f'{sub_dir}/xfm/{sub}_{ses}_from-extdhcp40wk_to-dwi_mode-image.nii.gz'

    #check if xfm exists
    if os.path.exists(xfm):
        #create exclusion and waypoint directories under rois
        exclusion_dir = f'{sub_dir}/rois/exclusionmasks'
        waypoint_dir = f'{sub_dir}/rois/waypointmasks'
        
        os.makedirs(exclusion_dir, exist_ok = True)
        os.makedirs(waypoint_dir, exist_ok = True)

        #loop through exclusion files
        for exclusion_file in exclusion_files:
            #set out file
            out_file = f'{exclusion_dir}/{os.path.basename(exclusion_file).replace('40wk', '')}'
            
            #apply transform to exclusion mask
            bash_cmd = f'applywarp --ref={sub_dir}/dwi/nodif_brain.nii.gz --in={exclusion_file} --warp={xfm} --out={out_file}'
            subprocess.run(bash_cmd, shell=True)

        #loop through waypoint files
        for waypoint_file in waypoint_files:
            #replace sub in waypoint file
            
            out_file = waypoint_file
            #set out file
            out_file = f'{waypoint_dir}/{os.path.basename(waypoint_file).replace('40wk', '')}'
            
            #apply transform to waypoint mask
            bash_cmd = f'applywarp --ref={sub_dir}/dwi/nodif_brain.nii.gz --in={waypoint_file} --warp={xfm} --out={out_file}'
            subprocess.run(bash_cmd, shell=True)
    else:
        print(f'{sub} {ses} missing xfm')
        continue
