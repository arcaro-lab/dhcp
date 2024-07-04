'''
Runs volumetric ROI registration with ANTs
'''

project_name = 'dhcp'
import os
#get current working directory
cwd = os.getcwd()
git_dir = cwd.split(project_name)[0] + '/' + project_name
import sys

#add git_dir to path
sys.path.append(git_dir)

import subprocess
import numpy as np
import pandas as pd
from glob import glob as glob
import dhcp_params
import matplotlib.pyplot as plt
import pdb
from nilearn import plotting, image
import shutil
import matplotlib
matplotlib.use('Agg')
import argparse

sub = sys.argv[1]
group = sys.argv[2]

group_info = dhcp_params.load_group_params(group)

ses = 'ses-'+glob(f'{group_info.raw_func_dir}/{sub}/ses-*')[0].split('ses-')[1]
roi = sys.argv[3]


roi_name, roi_labels, template, template_name, xfm, method = group_info.load_roi_info(roi)

xfm = xfm.replace('*SUB*', sub).replace('*SES*', ses)
xfm = f'{group_info.raw_func_dir}/{sub}/{ses}/xfm/{xfm}.nii.gz'


#set sub dir
anat_input = f'{group_info.raw_anat_dir}/{sub}/{ses}'
func_input = f'{group_info.raw_func_dir}/{sub}/{ses}'
data_dir = f'{group_info.out_dir}/{sub}/{ses}'
atlas_dir = group_info.atlas_dir

anat = f'anat/{sub}_{ses}_{group_info.anat_suf}' 

anat_img = image.load_img(f'{data_dir}/{anat}_brain.nii.gz')
anat_affine = anat_img.affine

#load functional image
func_img = image.load_img(f'{data_dir}/func/{sub}_{ses}_{group_info.func_suf}_1vol.nii.gz')
func_affine = func_img.affine

#check if they are identical    
if np.array_equal(anat_affine, func_affine):
    same_affine = True
else:
    same_affine = False

os.makedirs(f'{data_dir}/rois/{roi}', exist_ok=True)

#create subplot for each hemi
fig, ax = plt.subplots(2, figsize = (4,6))


def register_with_ants():
    #check if ants transformation already exists
    if os.path.exists(f'{data_dir}/xfm/{template_name}2anat1Warp.nii.gz') == False:

        #create transformations from template to anat
        bash_cmd =f'antsRegistrationSyN.sh -f {data_dir}/{anat}_brain.nii.gz -m {atlas_dir}/{template}.nii.gz -d 3 -o {data_dir}/xfm/{template_name}2anat -n 4'
        subprocess.run(bash_cmd, shell=True)

    #apply inverse transform to anat
    bash_cmd = f'antsApplyTransforms \
        -d 3 \
            -i {data_dir}/{anat}_brain.nii.gz \
                -r {atlas_dir}/{template}.nii.gz \
                    -t {data_dir}/xfm/{template_name}2anat1InverseWarp.nii.gz \
                        -t [{data_dir}/xfm/{template_name}2anat0GenericAffine.mat, 1] \
                            -o {data_dir}/{anat}_brain_{template_name}.nii.gz \
                                -n Linear'

    subprocess.run(bash_cmd, shell=True)

        #apply transformations to roi
    bash_cmd = f"antsApplyTransforms \
        -d 3 \
            -i {atlas_dir}/{curr_roi}.nii.gz \
                -r  {data_dir}/{anat}_brain.nii.gz \
                    -t {data_dir}/xfm/{template_name}2anat1Warp.nii.gz \
                        -t {data_dir}/xfm/{template_name}2anat0GenericAffine.mat \
                            -o {data_dir}/rois/{roi}/{hemi}_{roi}_anat.nii.gz \
                                -n NearestNeighbor"
    subprocess.run(bash_cmd, shell=True)

    if same_affine == False:
        #register anat roi to func space
        bash_cmd = f'flirt -in {data_dir}/rois/{roi}/{hemi}_{roi}_anat.nii.gz -ref {data_dir}/func/{sub}_{ses}_{group_info.func_suf}_1vol.nii.gz -out {data_dir}/rois/{roi}/{hemi}_{roi}_epi.nii.gz -applyxfm -init {data_dir}/xfm/anat2func.mat -interp nearestneighbour'
        subprocess.run(bash_cmd, shell=True)
    elif same_affine ==True:
        #copy atlas to roi dir
        shutil.copy(f'{data_dir}/rois/{roi}/{hemi}_{roi}_anat.nii.gz', f'{data_dir}/rois/{roi}/{hemi}_{roi}_epi.nii.gz')


        #binarize and fill holes in roi using fsl
    bash_cmd = f'fslmaths {data_dir}/rois/{roi}/{hemi}_{roi}_epi.nii.gz -bin -fillh {data_dir}/rois/{roi}/{hemi}_{roi}_epi.nii.gz'
    subprocess.run(bash_cmd.split(), check = True)

def register_with_applywarp(curr_roi, xfm):

    os.makedirs(f'{data_dir}/rois/{roi}', exist_ok=True)
    
    #check if inwarp already exists
    if os.path.exists(f'{data_dir}/xfm/{sub}_{ses}_from-extdhcp40wk_to-bold_mode-image.nii.gz') == False:
    
        bash_cmd = f'invwarp -w {xfm} -o {data_dir}/xfm/{sub}_{ses}_from-extdhcp40wk_to-bold_mode-image.nii.gz -r {data_dir}/func/{sub}_{ses}_{group_info.func_suf}_1vol.nii.gz'
        subprocess.run(bash_cmd, shell=True)

    final_xfm = f'{data_dir}/xfm/{sub}_{ses}_from-extdhcp40wk_to-bold_mode-image.nii.gz'

    bash_cmd = f'applywarp -i {group_info.atlas_dir}/{curr_roi}.nii.gz -r {data_dir}/func/{sub}_{ses}_{group_info.func_suf}_1vol.nii.gz  -w {final_xfm} -o {data_dir}/rois/{roi}/{hemi}_{roi}_epi.nii.gz --interp=nn'
    
    subprocess.run(bash_cmd, shell=True)




for hemi in group_info.hemis:
    curr_roi = roi_name.replace('hemi', hemi)

    if method == 'ants':
        register_with_ants()

    elif method == 'applywarp':
        register_with_applywarp(curr_roi, xfm)
    







    #plot atlas on subject's brain
    #plotting.plot_roi(f'{data_dir}/rois/{roi}/{hemi}_{roi}_epi.nii.gz', bg_img = func_img, axes = ax[group_info.hemis.index(hemi)], title = f'{sub} {hemi} {roi}',draw_cross=False) 


#create qc folder for atlas and group
#os.makedirs(f'{git_dir}/fmri/qc/{roi}/{group_info.group}', exist_ok = True)


#save figure with tight layout
#plt.savefig(f'{git_dir}/fmri/qc/{roi}/{group_info.group}/{sub}_{roi}_epi.png', bbox_inches = 'tight')