
project_name = 'dhcp'
import os
#get current working directory
cwd = os.getcwd()
git_dir = cwd.split(project_name)[0] + project_name
import sys

#add git_dir to path
sys.path.append(git_dir)
sys.path.append(git_dir)

import subprocess
import numpy as np
import pandas as pd
from glob import glob as glob
import dhcp_params
import pdb

import matplotlib.pyplot as plt
from nilearn import plotting, image
import nibabel as nib
import shutil
import pdb
import matplotlib
matplotlib.use('Agg')

#take subjectand session as command line argument
sub = sys.argv[1]
ses = sys.argv[2]
group = sys.argv[3]
atlas = sys.argv[4]

group_info = dhcp_params.load_group_params(group)




#hemis = ['lh','rh']

#set sub dir
anat_dir = f'{group_info.out_dir}/{sub}/{ses}'
func_dir = f'{group_info.raw_func_dir}/{sub}/{ses}'
out_dir = f'{group_info.out_dir}/{sub}/{ses}'
atlas_dir = dhcp_params.atlas_dir

roi_dir = f'{out_dir}/rois'

atlas_info = dhcp_params.load_atlas_info(atlas)
atlas_name = atlas_info.atlas_name
roi_labels = atlas_info.roi_labels

anat2func = group_info.anat2func.replace('*SUB*',sub).replace('*SES*',ses)
func2anat = group_info.func2anat.replace('*SUB*',sub).replace('*SES*',ses)

anat2dwi = group_info.anat2dwi.replace('*SUB*',sub).replace('*SES*',ses)

#if atlas dir exists, delete it
if os.path.exists(f'{roi_dir}/{atlas}'):
    shutil.rmtree(f'{roi_dir}/{atlas}')

os.makedirs(f'{roi_dir}/{atlas}', exist_ok = True)

anat_img = image.load_img(f'{anat_dir}/anat/{sub}_{ses}_{group_info.anat_suf}_brain.nii.gz')
anat_affine = anat_img.affine

#load functional image
func_img = image.load_img(f'{out_dir}/func/{sub}_{ses}_{group_info.func_suf}_1vol.nii.gz')
func_affine = func_img.affine



for hemi in group_info.hemis:
    #replace hemi in atlas name with current hemi
    curr_atlas = atlas_name.replace('hemi', hemi)

    #register atlas to anatomical space and then dwi space
    bash_cmd = f'flirt -in {out_dir}/atlas/{curr_atlas}_epi.nii.gz -ref {anat_dir}/anat/{sub}_{ses}_{group_info.anat_suf}_brain.nii.gz -applyxfm -init {func2anat} -out {out_dir}/atlas/{curr_atlas}_anat2dwi.nii.gz -interp nearestneighbour'
    subprocess.run(bash_cmd.split(), check = True)

    bash_cmd = f'flirt -in {out_dir}/atlas/{curr_atlas}_anat2dwi.nii.gz -ref {out_dir}/dwi/nodif_brain.nii.gz -applyxfm -init {anat2dwi} -out {out_dir}/atlas/{curr_atlas}_dwi.nii.gz -interp nearestneighbour'
    subprocess.run(bash_cmd.split(), check = True)


    

    #load atlas
    atlas_img = image.load_img(f'{out_dir}/atlas/{curr_atlas}_dwi.nii.gz')

    #loop through rois in labels file
    for roi_ind, roi in zip(roi_labels['index'],roi_labels['label']):
        #extract current roi
        roi_atlas = image.math_img(f'np.where(atlas == {roi_ind}, atlas, 0)', atlas = atlas_img)

        #save roi
        nib.save(roi_atlas, f'{roi_dir}/{atlas}/{hemi}_{roi}_dwi.nii.gz')
        
        #binarize and fill holes in roi using fsl
        bash_cmd = f'fslmaths {roi_dir}/{atlas}/{hemi}_{roi}_dwi.nii.gz -bin -fillh {roi_dir}/{atlas}/{hemi}_{roi}_dwi.nii.gz'
        subprocess.run(bash_cmd.split(), check = True)