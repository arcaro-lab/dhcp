'''
Compute second-order similarity for a region

e.g., create a voxel x network map for the pulvinar of each subject
'''

git_dir = '/mnt/c/Users/ArcaroLab/Desktop/git_repos/dhcp'
import sys
#add git_dir to path
sys.path.append(git_dir)
import pandas as pd
from nilearn import image, plotting, masking
#from nilearn.glm import threshold_stats_img
import numpy as np
import scipy.stats as stats

from nilearn.maskers import NiftiMasker

import nibabel as nib
import os

import pdb

import warnings
import dhcp_params as params
import subprocess

group = 'infant'

raw_data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf, brain_mask_suf, template, template_name = params.load_group_params(group)

analysis_name = 'thalmocortical'
seed_atlas = 'wang'
target_roi = 'pulvinar'


sub_list = pd.read_csv(f'{out_dir}/participants.csv')
sub_list = sub_list[sub_list[f'{seed_atlas}_ts'] == 1]
sub_list = sub_list[sub_list[f'{target_roi}_reg'] == 1]

#load atlas info
atlas_name, roi_labels = params.load_atlas_info(seed_atlas)

#load target atlas info
try:
    target_name, target_labels = params.load_atlas_info(target_roi)
    target_dir = f'atlas/{target_name}_epi.nii.gz'
except:
    target_name = target_roi
    target_name = params.load_roi_info(target_roi)
    target_dir = f'rois/{target_roi}/hemi_{target_roi}_epi.nii.gz'

def compute_indiv_correlations(sub, ses):
    print(f'Computing second order correlations for {sub}')
    sub_dir = f'{out_dir}/{sub}/{ses}'
    data_dir = f'{sub_dir}/derivatives/{analysis_name}'
    timseries_dir = f'{sub_dir}/derivatives/timeseries'
    roi_dir = f'{sub_dir}/rois'
    for hemi in params.hemis:
        #load roi mask
        target_mask = image.load_img(f'{roi_dir}/{target_roi}/{hemi}_{target_roi}_epi.nii.gz')

        #create masker object
        masker = NiftiMasker(mask_img=target_mask, standardize=False, detrend=False)  

        #load similarity RDM for seed_atlas
        seed_ts = np.load(f'{timseries_dir}/{sub}_{ses}_{seed_atlas}_{hemi}_ts.npy').T

        #create seed_rdm
        seed_rdm = np.corrcoef(seed_ts)

        #subtract .001 from diagonal, so fisher z transform doesn't break
        np.fill_diagonal(seed_rdm, seed_rdm.diagonal() - .001)

        
        #fisher z transform
        seed_rdm = np.arctanh(seed_rdm)


        #loop through rois
        all_rois = []
        for roi in roi_labels['label']:
            #load data for each ROI
            roi_img = image.load_img(f'{data_dir}/{hemi}_{roi}_corr.nii.gz')

            #extract data
            roi_data = masker.fit_transform(roi_img)
            
            #flatten
            #roi_data = roi_data.flatten()

            #append to list
            all_rois.append(roi_data)


        #convert to array
        all_rois = np.array(all_rois)

        #fisher z transform
        all_rois = np.arctanh(all_rois)

        #create zero array with shape of all_rois
        second_order_rdm = np.zeros(all_rois.shape)
        

        for rn,roi in enumerate(roi_labels['label']):
            
            
            #compute correlation between seed and roifor each voxel
            for vox in range(0,all_rois.shape[2]):
                
                second_order_rdm[rn,0, vox] = np.corrcoef(seed_rdm[rn,:], all_rois[:, 0,vox])[0,1]

            #extract data for current roi
            curr_roi = second_order_rdm[rn,0,:]

            #reshape it to match roi_data
            curr_roi = curr_roi.reshape(roi_data.shape)
            

            #transform it back to brain space
            curr_roi = masker.inverse_transform(curr_roi)

            #drop last dimension
            curr_roi = curr_roi.slicer[:,:,:,0]
            
        
            #save it
            curr_roi.to_filename(f'{data_dir}/{hemi}_{roi}_second_order.nii.gz')

        #remove middle dimension
        second_order_rdm = second_order_rdm.squeeze()
        #save second order rdm
        np.save(f'{data_dir}/{hemi}_second_order_rdm.npy', second_order_rdm)

def register_to_template(sub, ses):
    '''
    Use ANTS to register map to template
    '''
    print(f'Registering {sub} {analysis_name} to {template}')
    sub_dir = f'{out_dir}/{sub}/{ses}'

    results_dir = f'{sub_dir}/derivatives/{analysis_name}'
    for hemi in params.hemis:
        for roi in roi_labels['label']:

            curr_map = f'{results_dir}/{hemi}_{roi}_second_order'

            #apply transformations to roi
            bash_cmd = f"antsApplyTransforms \
                -d 3 \
                    -i {curr_map}.nii.gz \
                        -r  {out_dir}/templates/{template}.nii.gz \
                            -t {sub_dir}/xfm/{template_name}2anat1InverseWarp.nii.gz \
                                -t [{sub_dir}/xfm/{template_name}2anat0GenericAffine.mat, 1] \
                                    -o {curr_map}_{template_name}.nii.gz \
                                        -n NearestNeighbor"
            subprocess.run(bash_cmd, shell=True)  


        
def create_group_map():
    '''
    Create group map by loading each subject's map and taking the median
    '''
    print(f'Creating group map for {group}')
    #load template
    template_file = f'{out_dir}/templates/{template}.nii.gz'
    affine = image.load_img(template_file).affine
    header = image.load_img(template_file).header


    results_dir = f'{out_dir}/derivatives/{analysis_name}'
    #create results dir
    os.makedirs(f'{results_dir}/{analysis_name}', exist_ok = True)

    #loop through hemis
    for hemi in params.hemis:
        #load roi mask
        target_name = params.load_roi_info(target_roi)
        curr_target = f'{out_dir}/atlases/{target_name}.nii.gz'

        curr_target = curr_target.replace('hemi', hemi)
        #create masker
        brain_masker = NiftiMasker(curr_target)

        for roi in roi_labels['label']:

            all_maps = []
            for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
                sub_dir = f'{out_dir}/{sub}/{ses}'
                data_dir = f'{sub_dir}/derivatives/{analysis_name}'

                curr_map = image.load_img(f'{data_dir}/{hemi}_{roi}_second_order_{template_name}.nii.gz')
                #apply mask

                curr_map = curr_map.get_fdata()

                #fisher z transform
                curr_map = np.tanh(curr_map)
                all_maps.append(curr_map)

            #convert to numpy array
            all_maps = np.array(all_maps)

            #take median across subjects
            group_map = np.mean(all_maps, axis = 0)

            #save
            group_map = nib.Nifti1Image(group_map, affine, header)
            group_map.to_filename(f'{results_dir}/{hemi}_{roi}_second_order_corrs_{template_name}.nii.gz')


#loop through subjects
for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
    
    #compute_indiv_correlations(sub, ses)

    register_to_template(sub, ses)

create_group_map()