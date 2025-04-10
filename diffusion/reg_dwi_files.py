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



rerun_exclusion = True
rerun_waypoint = False
rerun_brain = False


def reg_to_template():
    '''
    register exclusion and waypoint masks from example sub to 40wk template
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
    #THIS IS NOT USED ANYMROE    
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
        bash_cmd = f'applywarp --ref={template} --in={waypoint_file} --warp={xfm} --out={out_file} --interp=nn'
        subprocess.run(bash_cmd, shell=True)
    


def reg_to_masks_to_subjects():

    '''
    Register exclusion and waypoint masks from 40wk template to individual subjects
    '''

    print('Registering exclusion and waypoint masks to individual subjects')
    group_params = params.load_group_params('infant')
    #load individual infant data
    sub_info = group_params.sub_list
    sub_info = sub_info[(sub_info[f'wang_exclude'] != 1)]


    #load only subs with two sessions
    sub_info = sub_info[sub_info.duplicated(subset = 'participant_id', keep = False)]
    sub_info = sub_info.reset_index()

    #loop through subs and register exclusion and waypoint masks
    source_dir = f'{params.atlas_dir}/diffusion_wangatlas/40wk'

    #glob exclusion and waypoint masks
    exclusion_files = glob(f'{source_dir}/exclusionmasks/*.nii.gz')
    waypoint_files = glob(f'{source_dir}/waypointmasks/*.nii.gz')
    brain_files = glob(f'{params.atlas_dir}/rois/*brain_mask_40wk.nii.gz')

    #only keep sub-CC00063AN06 in sub_info
    #sub_info = sub_info[sub_info['participant_id'] == 'sub-CC00063AN06']


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

        last_exclusion_file = f'{sub_dir}/rois/exclusionmasks/{os.path.basename(exclusion_files[-1]).replace('40wk', '')}'
        last_waypoint_file = f'{sub_dir}/rois/waypointmasks/{os.path.basename(waypoint_files[-1]).replace('40wk', '')}'
        last_brain_file = f'{sub_dir}/rois/brain/{os.path.basename(brain_files[-1]).replace('40wk', 'dwi')}'

        drop_out_mask = f'{sub_dir}/rois/drop_out/drop_out_mask_dwi.nii.gz'


        #check if xfm exists
        if os.path.exists(xfm):
            dwi_img = image.load_img(f'{sub_dir}/dwi/nodif.nii.gz')
            dwi_affine = dwi_img.affine
            dwi_header = dwi_img.header
            #create exclusion and waypoint directories under rois
            exclusion_dir = f'{sub_dir}/rois/exclusionmasks'
            waypoint_dir = f'{sub_dir}/rois/waypointmasks'

            
            #check if last exclusion file already exists or rerun is True
            if os.path.exists(last_exclusion_file) == False or rerun_exclusion == True:
                print('registering exclusion mask')
                
                #remove existing exclusion directory if it exists
                shutil.rmtree(exclusion_dir, ignore_errors = True)
                os.makedirs(exclusion_dir, exist_ok = True)

                #loop through exclusion files
                for exclusion_file in exclusion_files:
                    #set out file
                    out_file = f'{exclusion_dir}/{os.path.basename(exclusion_file).replace('40wk', '')}'
                    
                    #apply transform to exclusion mask
                    bash_cmd = f'applywarp --ref={sub_dir}/dwi/nodif_brain.nii.gz --in={exclusion_file} --warp={xfm} --out={out_file} --interp=nn'
                    subprocess.run(bash_cmd, shell=True)

                    #add dropout mask
                    bash_cmd = f'fslmaths {out_file} -add {drop_out_mask} -bin {out_file}'
                    subprocess.run(bash_cmd, shell=True)

                    #load file and apply dwi header
                    exclusion_img = image.load_img(out_file)
                    exclusion_img = image.new_img_like(dwi_img, exclusion_img.get_fdata(), affine = dwi_affine, copy_header = True)
                    #save file
                    exclusion_img.to_filename(out_file)

            
            #check if last waypoint file already exists or rerun is True
            if os.path.exists(last_waypoint_file) == False or rerun_waypoint == True:
                print('registering waypoint mask')
                #remove existing waypoint directory if it exists
                shutil.rmtree(waypoint_dir, ignore_errors = True)
                os.makedirs(waypoint_dir, exist_ok = True)

                #loop through waypoint files
                for waypoint_file in waypoint_files:
                    #replace sub in waypoint file
                    
                    out_file = waypoint_file
                    #set out file
                    out_file = f'{waypoint_dir}/{os.path.basename(waypoint_file).replace('40wk', '')}'
                    
                    #check if file already exists or rerun is True
                    if os.path.exists(out_file) and rerun == False:
                        continue

                    #apply transform to waypoint mask
                    bash_cmd = f'applywarp --ref={sub_dir}/dwi/nodif_brain.nii.gz --in={waypoint_file} --warp={xfm} --out={out_file} --interp=nn'
                    subprocess.run(bash_cmd, shell=True)

                    #load file and apply dwi header
                    waypoint_img = image.load_img(out_file)
                    waypoint_img = image.new_img_like(dwi_img, waypoint_img.get_fdata(), affine = dwi_affine, copy_header = True)
                    #save file
                    waypoint_img.to_filename(out_file)

            
            #check if last brain file already exists or rerun is True
            if os.path.exists(last_brain_file) == False or rerun_brain == True:
                print('registering brain mask')                    

                #loop through brain mask files
                for brain_file in brain_files:
                    #set out file
                    
                    out_file = f'{sub_dir}/rois/brain/{os.path.basename(brain_file).replace('40wk', 'dwi')}'
                    
                    #check if file already exists or rerun is True
                    if os.path.exists(out_file) and rerun_brain == False:
                        continue

                    #apply transform to brain mask
                    bash_cmd = f'applywarp --ref={sub_dir}/dwi/nodif_brain.nii.gz --in={brain_file} --warp={xfm} --out={out_file} --interp=nn'
                    subprocess.run(bash_cmd, shell=True)

                    #load file and apply dwi header
                    brain_img = image.load_img(out_file)
                    brain_img = image.new_img_like(dwi_img, brain_img.get_fdata(), affine = dwi_affine, copy_header = True)
                    #save file
                    brain_img.to_filename(out_file)

        else:
            print(f'{sub} {ses} missing xfm')
            continue


#reg_to_template()
reg_to_masks_to_subjects()