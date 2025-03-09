'''
Runs volumetric ROI registration with ANTs
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
import matplotlib.pyplot as plt
import pdb
from nilearn import plotting, image
import shutil
import matplotlib
matplotlib.use('Agg')
import argparse

sub = sys.argv[1]
ses = sys.argv[2]
group = sys.argv[3]

group_info = dhcp_params.load_group_params(group)


roi = sys.argv[4]


roi_info = dhcp_params.load_roi_info(roi, group)

template = roi_info.template
template_name = roi_info.template_name
method = roi_info.method
roi_name = roi_info.roi_name


#pull transforms
template2func = group_info.template2func.replace('*SUB*', sub).replace('*SES*', ses)
func2template = group_info.func2template.replace('*SUB*', sub).replace('*SES*', ses)

func2anat = group_info.func2anat.replace('*SUB*', sub).replace('*SES*', ses)
anat2func = group_info.anat2func.replace('*SUB*', sub).replace('*SES*', ses)
template2anat = group_info.template2anat.replace('*SUB*', sub).replace('*SES*', ses)
template2dwi = group_info.template2dwi.replace('*SUB*', sub).replace('*SES*', ses)


#set sub dir
anat_input = f'{group_info.raw_anat_dir}/{sub}/{ses}'
func_input = f'{group_info.raw_func_dir}/{sub}/{ses}'
data_dir = f'{group_info.out_dir}/{sub}/{ses}'
atlas_dir = dhcp_params.atlas_dir

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


def register_to_infants(curr_roi):
    

    os.makedirs(f'{data_dir}/rois/{roi}', exist_ok=True)
    
    #check if template2func already exists
    if os.path.exists(template2func) == False:
    
        bash_cmd = f'invwarp -w {func2template} -o {template2func} -r {data_dir}/func/{sub}_{ses}_{group_info.func_suf}_1vol.nii.gz'
        subprocess.run(bash_cmd, shell=True)

    #final_xfm = f'{data_dir}/xfm/{sub}_{ses}_from-extdhcp40wk_to-bold_mode-image.nii.gz'
    
    #apply transformations for template2func
    bash_cmd = f'applywarp -i {atlas_dir}/{curr_roi}.nii.gz -r {data_dir}/func/{sub}_{ses}_{group_info.func_suf}_1vol.nii.gz  -w {template2func} -o {data_dir}/rois/{roi}/{hemi}_{roi}_epi.nii.gz --interp=nn'
    subprocess.run(bash_cmd, shell=True)

    #apply transformations for template2dwi
    bash_cmd = f'applywarp -i {atlas_dir}/{curr_roi}.nii.gz -r {data_dir}/dwi_bedpostx.bedpostX/nodif_brain_mask.nii.gz  -w {template2dwi} -o {data_dir}/rois/{roi}/{hemi}_{roi}_dwi.nii.gz --interp=nn'
    subprocess.run(bash_cmd, shell=True)

    #apply transformations to anat
    #bash_cmd = f'applywarp -i {atlas_dir}/{curr_roi}.nii.gz -r {data_dir}/{anat}_brain.nii.gz  -w {template2anat} -o {data_dir}/rois/{roi}/{hemi}_{roi}_anat.nii.gz --interp=nn'
    bash_cmd = f'flirt -in {data_dir}/rois/{roi}/{hemi}_{roi}_epi.nii.gz -ref {data_dir}/{anat}_brain.nii.gz -out {data_dir}/rois/{roi}/{hemi}_{roi}_anat.nii.gz -applyxfm -init {func2anat} -interp nearestneighbour'
    subprocess.run(bash_cmd, shell=True)    

    

def register_to_adults(curr_roi):
    os.makedirs(f'{data_dir}/rois/{roi}', exist_ok=True)

    #check if template2anat already exists
    if os.path.exists(template2anat) == False:
        #create omat
        bash_cmd = f'flirt -in {group_info.group_template} -ref {data_dir}/{anat}_brain.nii.gz -omat {template2anat} -bins 256 -cost corratio -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 12'
        subprocess.run(bash_cmd, shell=True)

    #transform roi to anat space
    bash_cmd = f'flirt -in {atlas_dir}/{curr_roi}.nii.gz -ref {data_dir}/{anat}_brain.nii.gz -out {data_dir}/rois/{roi}/{hemi}_{roi}_anat.nii.gz -applyxfm -init {template2anat} -interp nearestneighbour'
    subprocess.run(bash_cmd, shell=True)

    #copy roi and rename to epi
    shutil.copy(f'{data_dir}/rois/{roi}/{hemi}_{roi}_anat.nii.gz', f'{data_dir}/rois/{roi}/{hemi}_{roi}_epi.nii.gz')
    
    


def register_with_applywarp(curr_roi):

    os.makedirs(f'{data_dir}/rois/{roi}', exist_ok=True)

  
    
    #check if template2func already exists
    if os.path.exists(template2func) == False:
    
        bash_cmd = f'invwarp -w {func2template} -o {template2func} -r {data_dir}/func/{sub}_{ses}_{group_info.func_suf}_1vol.nii.gz'
        subprocess.run(bash_cmd, shell=True)

    #final_xfm = f'{data_dir}/xfm/{sub}_{ses}_from-extdhcp40wk_to-bold_mode-image.nii.gz'
    
    #apply transformations for template2func
    bash_cmd = f'applywarp -i {atlas_dir}/{curr_roi}.nii.gz -r {data_dir}/func/{sub}_{ses}_{group_info.func_suf}_1vol.nii.gz  -w {template2func} -o {data_dir}/rois/{roi}/{hemi}_{roi}_epi.nii.gz --interp=nn'
    subprocess.run(bash_cmd, shell=True)

    #apply transformations for template2anat
    bash_cmd = f'applywarp -i {atlas_dir}/{curr_roi}.nii.gz -r {data_dir}/{anat}_brain.nii.gz  -w {template2anat} -o {data_dir}/rois/{roi}/{hemi}_{roi}_anat.nii.gz --interp=nn'
    subprocess.run(bash_cmd, shell=True)
    


def register_with_flirt(curr_roi, func2template, template2func):

    os.makedirs(f'{data_dir}/rois/{roi}', exist_ok=True)

    #check if template2anat already exists
    if os.path.exists(template2anat) == False:
        #create omat
        bash_cmd = f'flirt -in {group_info.group_template} -ref {data_dir}/{anat}_brain.nii.gz -omat {template2anat} -bins 256 -cost corratio -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 12'
        subprocess.run(bash_cmd, shell=True)

    #transform roi to anat space
    bash_cmd = f'flirt -in {atlas_dir}/{curr_roi}.nii.gz -ref {data_dir}/{anat}_brain.nii.gz -out {data_dir}/rois/{roi}/{hemi}_{roi}_anat.nii.gz -applyxfm -init {template2anat} -interp nearestneighbour'
    subprocess.run(bash_cmd, shell=True)

    #transform roi from anat to func space
    bash_cmd = f'flirt -in {data_dir}/rois/{roi}/{hemi}_{roi}_anat.nii.gz -ref {data_dir}/func/{sub}_{ses}_{group_info.func_suf}_1vol.nii.gz -out {data_dir}/rois/{roi}/{hemi}_{roi}_epi.nii.gz -applyxfm -init {anat2func} -interp nearestneighbour'


    if os.path.exists(template2func) == False:
        bash_cmd = f'flirt -in {data_dir}/func/{sub}_{ses}_{group_info.func_suf}_1vol.nii.gz -ref {group_info.group_template} -out {template2func} -omat {template2func.replace(".nii.gz",".mat")}'
        subprocess.run(bash_cmd, shell=True)



for hemi in group_info.hemis:
    curr_roi = roi_name.replace('hemi', hemi)
    if group == 'infant':
        register_to_infants(curr_roi)

    elif group == 'adult':
        register_to_adults(curr_roi)
'''
    if method == 'ants':
        register_with_ants()

    elif method == 'applywarp':
        register_with_applywarp(curr_roi)


    elif method == 'flirt':
        register_with_flirt(curr_roi, func2template, template2func)
    
'''






    #plot atlas on subject's brain
    #plotting.plot_roi(f'{data_dir}/rois/{roi}/{hemi}_{roi}_epi.nii.gz', bg_img = func_img, axes = ax[group_info.hemis.index(hemi)], title = f'{sub} {hemi} {roi}',draw_cross=False) 


#create qc folder for atlas and group
#os.makedirs(f'{git_dir}/fmri/qc/{roi}/{group_info.group}', exist_ok = True)


#save figure with tight layout
#plt.savefig(f'{git_dir}/fmri/qc/{roi}/{group_info.group}/{sub}_{roi}_epi.png', bbox_inches = 'tight')