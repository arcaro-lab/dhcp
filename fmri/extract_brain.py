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
import dhcp_params
import pdb
import nibabel as nib
from nilearn import plotting, image

#take subject and group as command line argument
sub = sys.argv[1]
ses = sys.argv[2]
group = sys.argv[3]

group_info = dhcp_params.load_group_params(group)



#create sub directories
os.makedirs(f'{group_info.out_dir}/{sub}/{ses}/anat', exist_ok=True)
os.makedirs(f'{group_info.out_dir}/{sub}/{ses}/func', exist_ok=True)
os.makedirs(f'{group_info.out_dir}/{sub}/{ses}/surf', exist_ok=True)
os.makedirs(f'{group_info.out_dir}/{sub}/{ses}/xfm', exist_ok=True)



#for infants invert xfm to make anatomical to functional
if group == 'infant':

    #check if anat2func xfm exists
    bash_cmd = f'convert_xfm -omat {group_info.anat2func.replace('*SUB*',sub).replace('*SES*',ses)} -inverse {group_info.func2anat.replace('*SUB*',sub).replace('*SES*',ses)}'
    subprocess.run(bash_cmd, shell=True)


#for infants
xfm = group_info.anat2func.replace('*SUB*',sub).replace('*SES*',ses)
#xfm = f'{group_info.raw_func_dir}/{sub}/{ses}/xfm/anat2func.mat'


#set sub dir
anat_input = f'{group_info.raw_anat_dir}/{sub}/{ses}'
func_input = f'{group_info.raw_func_dir}/{sub}/{ses}'
out_dir = f'{group_info.out_dir}/{sub}/{ses}'

anat = f'anat/{sub}_{ses}_{group_info.anat_suf}' 
func = f'func/{sub}_{ses}_{group_info.func_suf}'
brain_mask = f'anat/{sub}_{ses}_{group_info.brain_mask_suf}'


#check if brain mask exists in original anat directory or in preprocessing directory
#this should only happen for infant
if not os.path.isfile(f'{anat_input}/{brain_mask}.nii.gz'):
    
    #binarize brain mask and output to preprocessing directory
    brain_mask = f'anat/{sub}_{ses}_desc-brain_mask'


#binarize brain mask and save in preprocessing directory
bash_cmd = f'fslmaths {anat_input}/{brain_mask}.nii.gz -bin {out_dir}/{brain_mask}.nii.gz'
subprocess.run(bash_cmd, shell=True)

#check if file exists
# if os.path.isfile(f'{out_dir}/anat/{brain_mask}.nii.gz'):
#     print(f'Brain mask for {sub} {ses} exists')

#apply brain mask to anat
bash_cmd = f'fslmaths {anat_input}/{anat}.nii.gz -mas {out_dir}/{brain_mask}.nii.gz {out_dir}/{anat}_brain.nii.gz'
subprocess.run(bash_cmd, shell=True)

#create 1 volume version of func file
bash_cmd = f'fslmaths {func_input}/{func}.nii.gz -Tmean {out_dir}/{func}_1vol.nii.gz'
subprocess.run(bash_cmd.split(), check = True)

#check if xfm exists, else create it
if group == 'adult':
    #create anat2func xfm
    bash_cmd = f'flirt -in {out_dir}/{anat}_brain.nii.gz -ref {out_dir}/{func}_1vol.nii.gz -omat {group_info.anat2func_xfm.replace('*SUB*',sub).replace('*SES*',ses)} -bins 256 -cost corratio -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 12'
    subprocess.run(bash_cmd, shell=True)
    
    #run flirt in reverse to get func2anat xfm
    bash_cmd = f'flirt -in {out_dir}/{func}_1vol.nii.gz -ref {out_dir}/{anat}_brain.nii.gz -omat {group_info.func2anat_xfm.replace('*SUB*',sub).replace('*SES*',ses)} -bins 256 -cost corratio -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 12'
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
mask = image.load_img(f'{group_info.out_dir}/{sub}/{ses}/{brain_mask}_epi.nii.gz')
lh_mask = mask.get_fdata()

#create left and right hemi mask of the mni template

#set right side to 0
lh_mask[(lh_mask.shape[0]//2):,:,:] = 0

#convert back to nifti
#lh_mask = image.new_image_like(mask, lh_mask)

lh_mask = image.image.new_img_like(mask, lh_mask)
nib.save(lh_mask, f'{out_dir}/rois/brain/lh_brain.nii.gz')

#set left side to 0
mask = image.load_img(f'{group_info.out_dir}/{sub}/{ses}/{brain_mask}_epi.nii.gz')
rh_mask = mask.get_fdata()

#set left side to 0
rh_mask[0:int(rh_mask.shape[0]//2),:,:] = 0
rh_mask = image.image.new_img_like(mask, rh_mask)

nib.save(rh_mask, f'{out_dir}/rois/brain/rh_brain.nii.gz')

#if its adults flip which is saved as left and right 
if group == 'adult':
    #flip left and right
    nib.save(lh_mask, f'{out_dir}/rois/brain/rh_brain.nii.gz')
    nib.save(rh_mask, f'{out_dir}/rois/brain/lh_brain.nii.gz')
