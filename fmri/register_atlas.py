'''
Register atlas to subject
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

import matplotlib.pyplot as plt
from nilearn import plotting, image
import nibabel as nib
import shutil
import matplotlib
matplotlib.use('Agg')

#take subjectand session as command line argument
sub = sys.argv[1]
ses = sys.argv[2]
atlas = sys.argv[3]

#set sub dir
anat_dir = f'{params.out_dir}/{sub}/{ses}'
out_dir = f'{params.out_dir}/{sub}/{ses}'
atlas_dir = params.atlas_dir

atlas_name, roi_labels = params.load_atlas_info(atlas)


#load anat
#load anatomical image
anat_img = image.load_img(f'{anat_dir}/anat/{sub}_{ses}_{params.anat_suf}_brain.nii.gz')
anat_affine = anat_img.affine

#load functional image
func_img = image.load_img(f'{out_dir}/func/{sub}_{ses}_{params.func_suf}_1vol.nii.gz')
func_affine = func_img.affine

#check if they are identical    
if np.array_equal(anat_affine, func_affine):
    same_affine = True
else:
    same_affine = False

for hemi in params.hemis:
    #replace hemi in atlas name with current hemi
    curr_atlas = atlas_name.replace('hemi', hemi)

    #check if curr atlas exists
    #if it does, delete it
    if os.path.exists(f'{out_dir}/atlas/{curr_atlas}_anat+orig.BRIK.gz'):
        #delete atlas
        os.remove(f'{out_dir}/atlas/{curr_atlas}_anat+orig.BRIK.gz')
        os.remove(f'{out_dir}/atlas/{curr_atlas}_anat+orig.HEAD')

    if os.path.exists(f'{out_dir}/atlas/{curr_atlas}_anat+tlrc.BRIK.gz'):
        #delete atlas
        os.remove(f'{out_dir}/atlas/{curr_atlas}_anat+tlrc.BRIK.gz')
        os.remove(f'{out_dir}/atlas/{curr_atlas}_anat+tlrc.HEAD')
    
    
    #register atlas to subject with afni
    bash_cmd = f"""3dSurf2Vol \
        -spec {out_dir}/SUMA/std.141.{sub}_{hemi}.spec -surf_A std.141.{hemi}.white.asc \
            -surf_B std.141.{hemi}.pial.asc \
                -sv {anat_dir}/anat/{sub}_{ses}_{params.anat_suf}_brain.nii.gz \
                    -grid_parent {out_dir}/func/{sub}_{ses}_{params.func_suf}_1vol_reg.nii.gz \
                        -sdata {atlas_dir}/{curr_atlas}.1D.dset \
                            -map_func mode \
                                    -prefix {out_dir}/atlas/{curr_atlas}_anat"""
    
    
    subprocess.run(bash_cmd.split(), check = True)

    
    #check if atlas has orgi or tlrc extension
    if os.path.exists(f'{out_dir}/atlas/{curr_atlas}_anat+orig.BRIK.gz'): atlas_ext = '+orig'
    if os.path.exists(f'{out_dir}/atlas/{curr_atlas}_anat+tlrc.BRIK.gz'): atlas_ext = '+tlrc'

    #convert to nifti
    bash_cmd = f'3dAFNItoNIFTI {out_dir}/atlas/{curr_atlas}_anat{atlas_ext} {curr_atlas}_anat.nii'
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

    #extract mask dimension from roi
    atlas_data = atlas_data[:,:,:,:,1]

    #drop last dimension
    atlas_data = np.squeeze(atlas_data)

    #convert back to nifti
    atlas_nifti = nib.Nifti1Image(atlas_data, affine=anat_affine)

    #save nifti
    nib.save(atlas_nifti, f'{out_dir}/atlas/{curr_atlas}_anat.nii.gz')








