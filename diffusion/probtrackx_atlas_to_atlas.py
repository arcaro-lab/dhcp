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
parser.add_argument('--sub', help='subject id',default='sub-CC00087AN14')
parser.add_argument('--ses', help='session id',default='ses-31800')
parser.add_argument('--group', help='group name',default='infant')
parser.add_argument('--seed', help='seed atlas name', default='wang')
parser.add_argument('--target', help='target atlas name', default='wang')

args = parser.parse_args()

#take subjectand session as command line argument
sub = args.sub
ses = args.ses
group = args.group
atlas = args.target
seed = args.seed


group_info = dhcp_params.load_group_params(group)

#hemis = ['lh','rh']

#set sub dir

sub_dir = f'{group_info.out_dir}/{sub}/{ses}'
atlas_dir = dhcp_params.atlas_dir

seed_atlas_dir = f'{sub_dir}/atlas'
roi_dir = f'{sub_dir}/rois'

atlas_info = dhcp_params.load_atlas_info(atlas)
seed_info = dhcp_params.load_atlas_info(seed)
atlas_name = atlas_info.atlas_name
roi_labels = atlas_info.roi_labels

out_dir = f'{sub_dir}/derivatives/probtrackx2'

#create paths ans seeds dirs
paths_dir = f'{sub_dir}/derivatives/dwi_paths'
seeds_dir = f'{sub_dir}/derivatives/dwi_seeds'

dwi2template_xfm = f'{group_info.dwi2template.replace("*SUB*",sub).replace("*SES*",ses)}'

#load nodif
nodif_img = image.load_img(f'{sub_dir}/dwi/nodif.nii.gz')




os.makedirs(paths_dir, exist_ok = True)
os.makedirs(seeds_dir, exist_ok = True)

merged_dir = f'{sub_dir}/dwi_bedpostx.bedpostX/merged'

#check if bedpostx dir exists
if not os.path.exists(dwi2template_xfm):
    print(f'Files do not exist, exiting')
    sys.exit(1)

rerun = True

#loop through rois, create waypoint file and target file, run probtrackx2
for hemi in ['lh','rh']:
    #set seed roi
    seed_atlas = f'{seed_atlas_dir}/{atlas_info.atlas_name}_dwi.nii.gz'.replace('hemi',hemi)

    #create binarized version of seed_atlas using fslmaths
    bash_cmd = f'fslmaths {seed_atlas} -bin {seed_atlas.replace(".nii.gz","_bin.nii.gz")}'
    subprocess.run(bash_cmd, shell=True)

    #set seed roi from new atlas
    seed_roi = f'{seed_atlas_dir}/{atlas_info.atlas_name}_dwi_bin.nii.gz'.replace('hemi',hemi)

    #load seed roi and update header to match dwi
    atlas_img = image.load_img(seed_roi)
    seed_img = image.new_img_like(nodif_img, atlas_img.get_fdata(), affine=nodif_img.affine, copy_header=True)
    seed_img.to_filename(seed_roi)

    #pdb.set_trace()

    #set exclusion mask
    #should be for opposite hemisphere
    if hemi == 'lh':
        exclusionmask = f'{roi_dir}/brain/rh_brain_mask_dwi.nii.gz'
    else:
        exclusionmask = f'{roi_dir}/brain/lh_brain_mask_dwi.nii.gz'


    for roi in roi_labels['label']:
        print(f'Running probtrackx2 for {hemi} {roi}...')
        #timit
        start = time.time()

        #set target roi
        target_roi = f'{roi_dir}/{atlas}/{hemi}_{roi}_dwi.nii.gz'
        

        #create a txt file with the target file
        target_file = f'{roi_dir}/targets.txt'
        with open(target_file, 'w') as f:
            f.write(f'{target_roi}\n')
        
        #check if files already exist in seeds_dir
        
        if os.path.exists(f'{seeds_dir}/{seed}_seeds_to_{hemi}_{roi}_dwi.nii.gz') == False or rerun == True:
            

            #run probtrackx2
            #            probtrackx2 -x ${seed_roi} -l --onewaycondition --pd -c 0.2 -S 2000 --steplength=0.5 -P 10000 --fibthresh=0.01 --distthresh=0.0 --sampvox=0.0 --avoid=${exclusionmask} --forcedir --opd -s ${merged} -m ${nodif_brain_mask} --dir=${out_dir} --waypoints=${waypoint_file} --waycond=AND --targetmasks=${target_file} --os2t
            bash_cmd = f'probtrackx2 -x {seed_roi} -l --onewaycondition --pd -c 0.2 -S 2000 --steplength=0.5 -P 10000 --fibthresh=0.01 --distthresh=0.0 --sampvox=0.0 --avoid={exclusionmask} --forcedir --opd -s {merged_dir} -m {sub_dir}/dwi_bedpostx.bedpostX/nodif_brain_mask --dir={out_dir} --targetmasks={target_file} --os2t'
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
        if os.path.exists(f'{seeds_dir}/{seed}_seeds_to_{hemi}_{roi}_40wk.nii.gz') == False or rerun == True:
                
            #warp seed file to template space
            seed_file = f'{seeds_dir}/{seed}_seeds_to_{hemi}_{roi}_dwi.nii.gz'
            bash_cmd = f'applywarp -i {seed_file} -r {group_info.group_template}.nii.gz -o {seed_file.replace("_dwi","_40wk")} -w {dwi2template_xfm}'
            subprocess.run(bash_cmd, shell=True)
        else:
            print(f'Files already exist, skipping...')

        #print timing
        end = time.time()
        print(f'Probtrackx2 for {hemi} {roi} took {end-start} seconds')

