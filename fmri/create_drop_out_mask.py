'''
Create drop out masks
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
from nilearn.maskers import NiftiMasker
#take subject and group as command line argument
#sub = sys.argv[1]
#ses = sys.argv[2]
#group = sys.argv[3]



group = 'infant'
#load group info
group_info = dhcp_params.load_group_params(group)

#load sub_list
sub_info = group_info.sub_list

def create_drop_out_mask(sub,ses, group_info):

    #set sub dir
    anat_input = f'{group_info.raw_anat_dir}/{sub}/{ses}'
    func_input = f'{group_info.raw_func_dir}/{sub}/{ses}'
    out_dir = f'{group_info.out_dir}/{sub}/{ses}'
    roi_dir = f'{out_dir}/rois/drop_out'

    anat = f'anat/{sub}_{ses}_{group_info.anat_suf}' 
    func = f'func/{sub}_{ses}_{group_info.func_suf}'
    brain_mask = f'anat/{sub}_{ses}_{group_info.brain_mask_suf}'

    #create new qc dir
    os.makedirs(f'{git_dir}/fmri/qc/drop_out', exist_ok=True)

    #make roi drop out mask directory
    os.makedirs(roi_dir, exist_ok=True)

    #check if brain mask exists in original anat directory or in preprocessing directory
    #this should only happen for infant
    if not os.path.isfile(f'{anat_input}/{brain_mask}.nii.gz'):
        
        
        brain_mask = f'anat/{sub}_{ses}_desc-brain_mask'


    #create masker from brain mask
    masker = NiftiMasker(mask_img=f'{out_dir}/{brain_mask}_epi.nii.gz')


    #extract brain data from func_1vol
    brain_data = masker.fit_transform(f'{out_dir}/{func}_1vol.nii.gz')

    #compute mean and sd
    mean = np.mean(brain_data, axis=1)[0]
    sd = np.std(brain_data, axis=1)[0]

    #compute threshold
    threshold = mean - (1 * sd)



    #set anything below threshold to 1
    brain_data[brain_data <= threshold] = 1

    #set any data not 1 to 0
    brain_data[brain_data != 1] = 0

    #create drop_out mask
    drop_out = masker.inverse_transform(brain_data)

    #plot on epi for qc
    plotting.plot_roi(drop_out, bg_img=f'{out_dir}/{func}_1vol.nii.gz', title='Drop Out Mask', display_mode='ortho', cut_coords=(12, -12, 15), output_file=f'{git_dir}/fmri/qc/drop_out/{sub}_{ses}_drop_out_mask.png')

    #save drop out mask
    drop_out.to_filename(f'{roi_dir}/drop_out_mask.nii.gz')



#loop through subs in sub_list
for sub, ses in zip(sub_info['participant_id'], sub_info['ses']):
    #print progress
    print(f'Creating drop out mask for {sub} {ses}')
    try:
        #create drop out mask
        create_drop_out_mask(sub, ses, group_info)
    except:
        print(f'Error creating drop out mask for {sub} {ses}')
        continue

