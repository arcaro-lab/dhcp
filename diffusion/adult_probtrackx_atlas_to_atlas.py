'''
Run probtrax between seed roi and regions of an atlas
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
from nilearn import plotting, image
import shutil
import pdb

#add timing code
import time
import argparse


#set up argparser for sub, ses, group, atlas, roi
parser = argparse.ArgumentParser(description='Run probtrackx2 between seed roi and regions of an atlas')
parser.add_argument('--sub', help='subject id',default='chon')
parser.add_argument('--group', help='group name',default='adult')
parser.add_argument('--seed', help='seed atlas name', default='wang')
parser.add_argument('--target', help='target atlas name', default='wang')

args = parser.parse_args()

#take subjectand session as command line argument
sub = args.sub

group = args.group
atlas = args.target
seed = args.seed


group_info = dhcp_params.load_group_params(group)

#hemis = ['lh','rh']

#set sub dir

sub_dir = f'/mnt/DataDrive3/vlad/diffusion/individual_subjects_adult/{sub}'
roi_dir = f'{sub_dir}/ROIs/VisualCortexROIs/DiffusionSpace'
#setting this to roi_dir because thats where it already is for adults
seed_atlas_dir = roi_dir
xfm_dir = f'{sub_dir}/xfm'

anat_img = f'{sub_dir}/structural/structural_restore_brain_susan.nii.gz'

atlas_info = dhcp_params.load_atlas_info(atlas)
seed_info = dhcp_params.load_atlas_info(seed)
atlas_name = atlas_info.atlas_name
roi_labels = atlas_info.roi_labels

out_dir = f'{sub_dir}/derivatives/probtrackx2'

#create paths ans seeds dirs
paths_dir = f'{sub_dir}/derivatives/dwi_paths'
seeds_dir = f'{sub_dir}/derivatives/dwi_seeds'

template_dir = f'/mnt/DataDrive3/vlad/diffusion/templates_and_rois'
template_img = f'{template_dir}/mni_icbm152_t1_tal_nlin_asym_09a_brain.nii.gz'

#load nodif
nodif_img = image.load_img(f'{sub_dir}/bedpostx.bedpostX/nodif_brain.nii.gz')


os.makedirs(paths_dir, exist_ok = True)
os.makedirs(seeds_dir, exist_ok = True)

merged_dir = f'{sub_dir}/bedpostx.bedpostX/merged'

#check if bedpostx dir exists
if not os.path.exists(f'{sub_dir}/bedpostx.bedpostX'):
    print(f'Files do not exist, exiting')
    sys.exit(1)

rerun = True


#create atlas from individual rois
#loop through rois, create waypoint file and target file, run probtrackx2
for hemi in ['lh','rh']:
    #check if atlas exists
    atlas_img = f'{roi_dir}/{atlas_name}_{hemi}_dwi.nii.gz'
    if os.path.exists(atlas_img) == False or rerun == True:
        all_rois = []
        #loop through ROIs
        for roi in roi_labels['label']:
            
            #set roi name to adult version
            roi = roi.replace('hMT', 'TO1').replace('MST','TO2')
            roi= roi.replace('V1v','V1').replace('V1d','V1').replace('V2v','V2').replace('V2d','V2')
            roi = roi.replace('V3v','V3').replace('V3d','V3').replace('SPL1','SPL')
            #load roi
            curr_roi = image.load_img(f'{roi_dir}/{roi}_{hemi}_diff.nii.gz')

            #add roi to list
            all_rois.append(curr_roi.get_fdata())

        #create atlas from all rois
        all_rois = np.array(all_rois)
        all_rois = np.sum(all_rois, axis=0)
        all_rois = np.where(all_rois > 0, 1, 0)
        all_rois_img = image.new_img_like(nodif_img, all_rois, affine=curr_roi.affine, copy_header=True)

        #save atlas
        atlas_img = f'{roi_dir}/{atlas_name.replace('hemi',hemi)}_dwi_bin.nii.gz'
        all_rois_img.to_filename(atlas_img)

        #fill holes using fslmaths
        bash_cmd = f'fslmaths {atlas_img} -fillh {atlas_img}'
        subprocess.run(bash_cmd, shell=True)

        
    '''register MNI hemi masks to diffusion space'''
    curr_mask = f'{template_dir}/{hemi}_mask_mni.nii.gz'

    #first register mni mask to anat
    #f'flirt -in {data_dir}/rois/{roi}/{hemi}_{roi}_anat.nii.gz -ref {data_dir}/func/{sub}_{ses}_{group_info.func_suf}_1vol.nii.gz -out {data_dir}/rois/{roi}/{hemi}_{roi}_epi.nii.gz -applyxfm -init {data_dir}/xfm/anat2func.mat -interp nearestneighbour'
    bash_cmd = f'flirt -in {curr_mask} -ref {anat_img} -out {sub_dir}/ROIs/{hemi}_brain_mask_anat.nii.gz -applyxfm -init {xfm_dir}/mni2anat.mat -interp nearestneighbour'
    subprocess.run(bash_cmd, shell=True)

    #then register anat to diffusion space
    bash_cmd = f'flirt -in {sub_dir}/ROIs/{hemi}_brain_mask_anat.nii.gz -ref {sub_dir}/bedpostx.bedpostX/nodif_brain.nii.gz -out {sub_dir}/ROIs/{hemi}_brain_mask_dwi.nii.gz -applyxfm -init {xfm_dir}/anat2b0.mat -interp nearestneighbour'
    subprocess.run(bash_cmd, shell=True)

    #pdb.set_trace()





#loop through rois, create waypoint file and target file, run probtrackx2
for hemi in ['lh','rh']:
    #set seed roi

    #set seed roi from new atlas
    seed_roi = f'{seed_atlas_dir}/{atlas_info.atlas_name}_dwi_bin.nii.gz'.replace('hemi',hemi)


    #pdb.set_trace()

    #set exclusion mask
    #should be for opposite hemisphere
    if hemi == 'lh':
        exclusionmask = f'{sub_dir}/ROIs/rh_brain_mask_dwi.nii.gz'
    else:
        exclusionmask = f'{sub_dir}/ROIs/lh_brain_mask_dwi.nii.gz'


    for roi in roi_labels['label']:
        print(f'Running probtrackx2 for {hemi} {roi}...')
        #timit
        start = time.time()

        #set roi name to adult version
        roi = roi.replace('hMT', 'TO1').replace('MST','TO2')
        roi= roi.replace('V1v','V1').replace('V1d','V1').replace('V2v','V2').replace('V2d','V2')
        roi = roi.replace('V3v','V3').replace('V3d','V3').replace('SPL1','SPL')

        #set target roi
        target_roi = f'{roi_dir}/{roi}_{hemi}_diff.nii.gz'
        

        #create a txt file with the target file
        target_file = f'{roi_dir}/targets.txt'
        with open(target_file, 'w') as f:
            f.write(f'{target_roi}\n')
        
        #check if files already exist in seeds_dir
        
        if os.path.exists(f'{seeds_dir}/{seed}_seeds_to_{hemi}_{roi}_dwi.nii.gz') == False or rerun == True:
            
            
            #run probtrackx2
            #            probtrackx2 -x ${seed_roi} -l --onewaycondition --pd -c 0.2 -S 2000 --steplength=0.5 -P 10000 --fibthresh=0.01 --distthresh=0.0 --sampvox=0.0 --avoid=${exclusionmask} --forcedir --opd -s ${merged} -m ${nodif_brain_mask} --dir=${out_dir} --waypoints=${waypoint_file} --waycond=AND --targetmasks=${target_file} --os2t
            bash_cmd = f'probtrackx2 -x {seed_roi} -l --onewaycondition --pd -c 0.2 -S 2000 --steplength=0.5 -P 10000 --fibthresh=0.01 --distthresh=0.0 --sampvox=0.0 --avoid={exclusionmask} --forcedir --opd -s {merged_dir} -m {sub_dir}/bedpostx.bedpostX/nodif_brain_mask --dir={out_dir} --targetmasks={target_file} --os2t'
            print(bash_cmd)
            subprocess.run(bash_cmd, shell=True)
            
            #move fdtpaths to paths_dir
            paths_file = f'{out_dir}/fdt_paths.nii.gz'
            shutil.move(paths_file, f'{paths_dir}/{seed}_to_{hemi}_{roi}_fdt_paths.nii.gz')

            #move seed file to seeds_dir
            seed_file = f'{out_dir}/seeds_to_{hemi}_{roi}_dwi.nii.gz'
            shutil.move(seed_file, f'{seeds_dir}/{seed}_seeds_to_{hemi}_{roi}_dwi.nii.gz')

            #remove target and waypoint files
            os.remove(target_file)
            
        else:
            print(f'Files already exist, skipping...')


        #check if files already exist
        if os.path.exists(f'{seeds_dir}/{seed}_seeds_to_{hemi}_{roi}_mni.nii.gz') == False or rerun == True:
                
            #transform seed file to template space
            seed_file = f'{seeds_dir}/{seed}_seeds_to_{hemi}_{roi}_dwi.nii.gz'

            #first transform to anat space
            bash_cmd = f'flirt -in {seed_file} -ref {anat_img} -out {seed_file.replace("_dwi","_anat")} -applyxfm -init {xfm_dir}/b0toanat.mat -interp trilinear'
            subprocess.run(bash_cmd, shell=True)

            #then transform to template space
            bash_cmd = f'flirt -in {seed_file.replace("_dwi","_anat")} -ref {template_img} -out {seed_file.replace("_dwi","_mni")} -applyxfm -init {xfm_dir}/anat2mni.mat -interp trilinear'
            
        else:
            print(f'Files already exist, skipping...')

        #print timing
        end = time.time()
        print(f'Probtrackx2 for {hemi} {roi} took {end-start} seconds')
        pdb.set_trace()

