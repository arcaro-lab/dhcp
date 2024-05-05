'''
Conduct brain extraction by using segmentation mask

*This is mostly neeeded for volumentric ROI registration
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
import dhcp_params as params
import pdb
import nibabel as nib
from nilearn import plotting, image

#take subject and session as command line argument
sub = sys.argv[1]
ses = sys.argv[2]

#xfm = f'{params.raw_func_dir}/{sub}/{ses}/xfm/{sub}_{ses}_from-bold_to-T2w_mode-image.mat'

#invert xfm
#bash_cmd = f'convert_xfm -omat {params.raw_func_dir}/{sub}/{ses}/xfm/{sub}_{ses}_from-T2w_to-bold_mode-image.mat -inverse {xfm}'
#subprocess.run(bash_cmd, shell=True)

#for infants
#xfm_inverted = f'{params.raw_func_dir}/{sub}/{ses}/xfm/{sub}_{ses}_from-T2w_to-bold_mode-image.mat'
xfm = f'{params.raw_func_dir}/{sub}/{ses}/xfm/anat2func.mat'


#set sub dir
anat_input = f'{params.raw_anat_dir}/{sub}/{ses}'
func_input = f'{params.raw_func_dir}/{sub}/{ses}'
out_dir = f'{params.out_dir}/{sub}/{ses}'

anat = f'anat/{sub}_{ses}_{params.anat_suf}' 
func = f'func/{sub}_{ses}_{params.func_suf}'
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



#create brain mask in epi space
bash_cmd = f'flirt -in {out_dir}/{brain_mask}.nii.gz -ref {out_dir}/{func}_1vol.nii.gz -out {out_dir}/{brain_mask}_epi.nii.gz -init {xfm} -interp nearestneighbour'
subprocess.run(bash_cmd, shell=True)
#pdb.set_trace()
#fill holes in brain mask
bash_cmd = f'fslmaths {out_dir}/{brain_mask}_epi.nii.gz -fillh {out_dir}/{brain_mask}_epi.nii.gz'
subprocess.run(bash_cmd, shell=True)

#dilate mask
bash_cmd = f'fslmaths {out_dir}/{brain_mask}_epi.nii.gz -dilM -dilM {out_dir}/{brain_mask}_epi.nii.gz'
subprocess.run(bash_cmd, shell=True)

#load brain mask
#mask = nib.load(f'{out_dir}/{brain_mask}_epi.nii.gz')

#create new roi directory for brain

os.makedirs(f'{out_dir}/rois/brain', exist_ok=True)
#extract just left hemisphere
mask = image.load_img(f'{params.out_dir}/{sub}/{ses}/{brain_mask}_epi.nii.gz')
lh_mask = mask.get_fdata()

 #create left and right hemi mask of the mni template

#set right side to 0
lh_mask[(lh_mask.shape[0]//2):,:,:] = 0

#convert back to nifti
#lh_mask = image.new_image_like(mask, lh_mask)

lh_mask = image.image.new_img_like(mask, lh_mask)
nib.save(lh_mask, f'{out_dir}/rois/brain/lh_brain.nii.gz')

#set left side to 0
mask = image.load_img(f'{params.out_dir}/{sub}/{ses}/{brain_mask}_epi.nii.gz')
rh_mask = mask.get_fdata()

#set left side to 0
rh_mask[0:int(rh_mask.shape[0]//2),:,:] = 0
rh_mask = image.image.new_img_like(mask, rh_mask)

nib.save(rh_mask, f'{out_dir}/rois/brain/rh_brain.nii.gz')

#if its adults flip which is saved as left and right 
if params.group == 'adult':
    #flip left and right
    nib.save(lh_mask, f'{out_dir}/rois/brain/rh_brain.nii.gz')
    nib.save(rh_mask, f'{out_dir}/rois/brain/lh_brain.nii.gz')
