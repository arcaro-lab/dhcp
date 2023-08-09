'''
Register atlas to subject
'''

git_dir = '/mnt/c/Users/ArcaroLab/Desktop/git_repos/dhcp'

import os
import sys
#add git_dir to path
sys.path.append(git_dir)

import subprocess
import numpy as np
import pandas as pd
from glob import glob as glob
import dhcp_params as params
import pdb

import matplotlib.pyplot as plt
from nilearn import plotting, image
import nibabel as nib
import shutil

#take subjectand session as command line argument
sub = sys.argv[1]
ses = sys.argv[2]
atlas = sys.argv[3]

#set sub dir
anat_dir = f'{params.raw_anat_dir}/{sub}/{ses}'
func_dir = f'{params.raw_func_dir}/{sub}/{ses}'
out_dir = f'{params.out_dir}/{sub}/{ses}'
atlas_dir = params.atlas_dir

atlas_name, roi_labels = params.load_roi_info(atlas)

#create subplot for each hemi
fig, ax = plt.subplots(2, figsize = (4,6))

#load anat
anat = nib.load(f'{anat_dir}/anat/{sub}_{ses}_desc-restore_T2w.nii.gz')
affine = anat.affine

for hemi in params.hemis:
    #replace hemi in atlas name with current hemi
    curr_atlas = atlas_name.replace('hemi', hemi)

    #check if curr atlas exists
    #if it does, delete it
    if os.path.exists(f'{out_dir}/atlas/{curr_atlas}_anat+orig.BRIK.gz'):
        #delete atlas
        os.remove(f'{out_dir}/atlas/{curr_atlas}_anat+orig.BRIK.gz')
        os.remove(f'{out_dir}/atlas/{curr_atlas}_anat+orig.HEAD')
                
    #register atlas to subject with afni
    bash_cmd = f"""3dSurf2Vol \
        -spec {out_dir}/SUMA/std.141.{sub}_{hemi}.spec -surf_A std.141.{hemi}.white.asc \
            -surf_B std.141.{hemi}.pial.asc \
                -sv {anat_dir}/anat/{sub}_{ses}_desc-restore_T2w.nii.gz \
                    -grid_parent {out_dir}/func/{sub}_{ses}_task-rest_desc-preproc_bold_1vol_reg.nii.gz \
                        -sdata {atlas_dir}/{curr_atlas}.1D.dset \
                            -map_func mode \
                                -f_steps 500 \
                                    -f_p1_mm -0.5 \
                                        -f_pn_mm 0.5 \
                                            -prefix {out_dir}/atlas/{curr_atlas}_anat"""
    

    subprocess.run(bash_cmd.split(), check = True)

    
    #convert to nifti
    bash_cmd = f'3dAFNItoNIFTI {out_dir}/atlas/{curr_atlas}_anat+orig {curr_atlas}_anat.nii'
    subprocess.run(bash_cmd.split(), check = True)
   
    #move new atlas_anat.nii to atlas dir
    shutil.move(f'{curr_atlas}_anat.nii', f'{out_dir}/atlas/{curr_atlas}_anat.nii')
    

    '''
    Extract just the rois from the atlas
    '''
    #load atlas
    atlas_img = image.load_img(f'{out_dir}/atlas/{curr_atlas}_anat.nii')

    #convert to numpy
    atlas_data = atlas_img.get_fdata()

    #extrat mask dimension from roi
    atlas_data = atlas_data[:,:,:,:,1]

    #drop last dimension
    atlas_data = np.squeeze(atlas_data)

    #convert back to nifti
    atlas_nifti = nib.Nifti1Image(atlas_data, affine=affine)

    #save nifti
    nib.save(atlas_nifti, f'{out_dir}/atlas/{curr_atlas}_anat.nii')
    
    # #register atlas to func with flirt
    #bash_cmd = f'flirt -in {out_dir}/atlas/{curr_atlas}_anat.nii -ref {out_dir}/func/{sub}_{ses}_task-rest_desc-preproc_bold_1vol.nii.gz -out {out_dir}/atlas/{curr_atlas}_epi.nii -applyxfm -init {out_dir}/xfm/anat2func.mat -interp trilinear'
    # subprocess.run(bash_cmd.split(), check = True)

    #plot atlas on subject's brain
    plotting.plot_roi(f'{out_dir}/atlas/{curr_atlas}_anat.nii', bg_img = anat, axes = ax[params.hemis.index(hemi)], title = f'{sub} {hemi} {atlas}',draw_cross=False) 


#save figure with tight layout
plt.savefig(f'{git_dir}/registration/qc/reg_plots/{sub}_{atlas}_anat.png', bbox_inches = 'tight')
