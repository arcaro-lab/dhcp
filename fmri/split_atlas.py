'''
Split atlas into ROIs
'''

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

#if atlas dir exists, delete it
if os.path.exists(f'{roi_dir}/{atlas}'):
    shutil.rmtree(f'{roi_dir}/{atlas}')

os.makedirs(f'{roi_dir}/{atlas}', exist_ok = True)

anat_img = image.load_img(f'{anat_dir}/anat/{sub}_{ses}_{group_info.anat_suf}_brain.nii.gz')
anat_affine = anat_img.affine

#load functional image
func_img = image.load_img(f'{out_dir}/func/{sub}_{ses}_{group_info.func_suf}_1vol.nii.gz')
func_affine = func_img.affine

#check if they are identical    
if np.array_equal(anat_affine, func_affine):
    same_affine = True
else:
    same_affine = False




for hemi in group_info.hemis:
    #replace hemi in atlas name with current hemi
    curr_atlas = atlas_name.replace('hemi', hemi)
    

    #load atlas
    atlas_img = image.load_img(f'{out_dir}/atlas/{curr_atlas}_anat.nii.gz')

    #loop through rois in labels file
    for roi_ind, roi in zip(roi_labels['index'],roi_labels['label']):
        #extract current roi
        roi_atlas = image.math_img(f'np.where(atlas == {roi_ind}, atlas, 0)', atlas = atlas_img)

        #save roi
        nib.save(roi_atlas, f'{roi_dir}/{atlas}/{hemi}_{roi}_anat.nii.gz')
        
        #binarize and fill holes in roi using fsl
        bash_cmd = f'fslmaths {roi_dir}/{atlas}/{hemi}_{roi}_anat.nii.gz -bin -fillh {roi_dir}/{atlas}/{hemi}_{roi}_anat.nii.gz'
        subprocess.run(bash_cmd.split(), check = True)

        #register to epi space
        
        if same_affine == False: #check if anat and func already have the same affine
            #register atlas to func
            bash_cmd = f'flirt -in {roi_dir}/{atlas}/{hemi}_{roi}_anat.nii.gz -ref {out_dir}/func/{sub}_{ses}_{group_info.func_suf}_1vol.nii.gz -out {roi_dir}/{atlas}/{hemi}_{roi}_epi.nii.gz -applyxfm -init {anat2func} -interp trilinear'
            subprocess.run(bash_cmd.split(), check = True)
        elif same_affine == True:
            #copy atlas to roi dir
            shutil.copy(f'{roi_dir}/{atlas}/{hemi}_{roi}_anat.nii.gz', f'{roi_dir}/{atlas}/{hemi}_{roi}_epi.nii.gz')
        


#create subplot for each hemi
fig, ax = plt.subplots(2, figsize = (4,6))
'''
Create new atlas with max probability roi
'''
for hemi in group_info.hemis:
    curr_atlas = atlas_name.replace('hemi', hemi)
    roi_imgs = []

    
    for roi in roi_labels['label']:
        roi_imgs.append(image.load_img(f'{roi_dir}/{atlas}/{hemi}_{roi}_epi.nii.gz').get_fdata())

    #create a zeros array with the same shape as the functional image
    zero_imgs = np.zeros(func_img.shape)  
    #insert zeros array as the first element of the roi_imgs list
    roi_imgs.insert(0, zero_imgs)
    #conert to numpy array
    roi_imgs = np.array(roi_imgs)
    #insert zeros array as the first element of the roi_imgs array
    

    #for every voxel, get the index of the max value
    max_roi = np.argmax(roi_imgs, axis=0)
    #add 1 to the index to get the roi label
    
    #convert max_roi to nifti
    max_roi = nib.Nifti1Image(max_roi, func_img.affine, func_img.header)

    #save it
    nib.save(max_roi, f'{out_dir}/atlas/{curr_atlas}_epi.nii.gz')


    #plot atlas on subject's brain
    plotting.plot_roi(f'{out_dir}/atlas/{curr_atlas}_epi.nii.gz', bg_img = func_img, axes = ax[group_info.hemis.index(hemi)], title = f'{sub} {hemi} {atlas}',draw_cross=False) 


#create qc directory if it doesn't exist
os.makedirs(f'{git_dir}/fmri/qc/{atlas}/{group}', exist_ok = True)

plt.savefig(f'{git_dir}/fmri/qc/{atlas}/{group}/{sub}_{atlas}_epi.png', bbox_inches = 'tight')

        

    

