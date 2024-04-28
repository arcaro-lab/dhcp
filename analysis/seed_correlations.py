'''
whole brain correlations between atlas and brain
'''
project_name = 'dhcp'
import os
#get current working directory
cwd = os.getcwd()
git_dir = cwd.split(project_name)[0] + project_name
import sys

#add git_dir to path

sys.path.append(git_dir)

import pandas as pd
from nilearn import image, plotting, masking
#from nilearn.glm import threshold_stats_img
import numpy as np

from nilearn.maskers import NiftiMasker

import nibabel as nib
import os

import pdb

import warnings
warnings.filterwarnings("ignore")

import dhcp_params as params
import subprocess

group = 'infant'

raw_data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf, brain_mask_suf, group_template,template_name = params.load_group_params(group)


analysis_name = 'whole_brain'
seed_atlas = 'wang'
target_roi = 'brain'

#analysis_name = 'thalmocortical'
#seed_atlas = 'wang'
#target_roi = 'pulvinar'
#load subject list
#load subject list
sub_list = pd.read_csv(f'{git_dir}/participants.csv')
sub_list = sub_list[sub_list[f'{seed_atlas}_ts'] == 1]
sub_list = sub_list[sub_list[f'{target_roi}_reg'] == 1]

#load atlas info
#atlas_name, roi_labels = params.load_atlas_info(seed_atlas)

roi_name, roi_labels = params.load_atlas_info(seed_atlas)
'''
#load target atlas info
try:
    target_name, target_labels = params.load_atlas_info(target_roi)
    target_dir = f'atlas/{target_name}_epi.nii.gz'
except:
    target_name = target_roi
    target_name = params.load_roi_info(target_roi)
    target_dir = f'rois/{target_roi}/hemi_{target_roi}_epi.nii.gz'
'''
#sub = sys.argv[1]
#ses = sys.argv[2]
#atlas = sys.argv[3]
#target = sys.argv[4]
target_name = target_roi
target_dir = f'rois/{target_roi}/hemi_{target_roi}.nii.gz' #THIS NEEDS TO BE _epi EVENTUALLY!!



#results_dir = f'{out_dir}/derivatives/retinotopy'
#create results dir


def compute_correlations(sub, ses, func_dir, seed_file, target_file):
    print(f'Computing correlations for {sub} {ses}')
    os.makedirs(f'{results_dir}/{analysis_name}', exist_ok = True)

    #load func data
    func_img = image.load_img(f'{func_dir}/{sub}/{ses}/func/{sub}_{ses}_{params.func_suf}.nii.gz')
    affine = func_img.affine
    header = func_img.header

    #index first image of func
    dummy_img = func_img.slicer[:,:,:,0]

    for hemi in params.hemis:
        curr_seed = seed_file.replace('hemi', hemi)
        curr_target = target_file.replace('hemi', hemi)

        #load data from seed
        seed_ts = np.load(curr_seed)
        seed_ts = seed_ts.T

        #load target atlas
        target_atlas = image.load_img(curr_target)
        #binarize target atlas
        target_atlas = image.math_img('img>0', img = target_atlas)

        #set masker
        brain_masker = NiftiMasker(target_atlas, standardize=True)

        #Extract brain data
        brain_time_series = brain_masker.fit_transform(func_img)


        '''
        Run correlations for individual ROI maps
        '''
        all_maps = []
        for n, ts in enumerate(seed_ts):
            #get roi label
            roi = roi_labels['label'][n]

            #compute correlation between seed and brain
            seed_to_voxel_correlations = (np.dot(brain_time_series.T, ts) /
                                        ts.shape[0])
            
            #save correlation map
            seed_to_voxel_correlations_img = brain_masker.inverse_transform(seed_to_voxel_correlations.T)

            #set all 0s to nan
            seed_to_voxel_correlations_img = image.math_img('np.where(img == 0, np.nan, img)', img = seed_to_voxel_correlations_img)

            #save correlation map
            seed_to_voxel_correlations_img.to_filename(f'{results_dir}/{analysis_name}/{hemi}_{roi}_corr.nii.gz')

            #convert to numpy array
            seed_to_voxel_correlations_img = seed_to_voxel_correlations_img.get_fdata()
            
            all_maps.append(seed_to_voxel_correlations_img)

            
        '''
        Create single map with max val for each voxel
        '''
        #create a zeros array with the same shape as the functional image
        zero_imgs = np.zeros(seed_to_voxel_correlations_img.shape)  
        #insert zeros array as the first element of the roi_imgs list
        all_maps.insert(0, zero_imgs)

        #convert to numpy array
        all_maps = np.array(all_maps)

        #for each voxel, find the roi with the highest correlation
        max_map = np.argmax(all_maps, axis = 0)

        #convert back to nifti
        max_map = nib.Nifti1Image(max_map, affine, header)

        #apply mask
        brain_masker = NiftiMasker(target_atlas, smoothing_fwhm=0)
        smoothed_map = brain_masker.fit_transform(max_map)

        #convert back to nifti
        smoothed_map = brain_masker.inverse_transform(smoothed_map)

        #save map
        nib.save(smoothed_map, f'{results_dir}/{analysis_name}/{hemi}_{analysis_name}_map.nii.gz')

def register_to_template(sub, ses,analysis_name, template,template_name):
    '''
    Use ANTS to register map to template
    '''
    print(f'Registering {sub} {analysis_name} to {template}')
    sub_dir = f'{out_dir}/{sub}/{ses}'
    results_dir = f'{sub_dir}/derivatives/{analysis_name}'

    warp = f'{params.raw_func_dir}/{sub}/{ses}/xfm/{sub}_{ses}_from-bold_to-extdhcp40wk_mode-image.nii.gz'
    for hemi in params.hemis:
        curr_map = f'{results_dir}/{hemi}_{analysis_name}_map'
        '''
        #apply transformations to roi
        bash_cmd = f"antsApplyTransforms \
            -d 3 \
                -i {curr_map}.nii.gz \
                    -r  {out_dir}/templates/{template}.nii.gz \
                        -t {sub_dir}/xfm/{template_name}2anat1InverseWarp.nii.gz \
                            -t [{sub_dir}/xfm/{template_name}2anat0GenericAffine.mat, 1] \
                                -o {curr_map}_{template_name}.nii.gz \
                                    -n NearestNeighbor"
        
        '''
        bash_cmd = f'applywarp -i {curr_map}.nii.gz -r {out_dir}/templates/{template}.nii.gz -w {warp} -o {curr_map}_{template_name}.nii.gz'
        subprocess.run(bash_cmd, shell=True)



def create_group_map(group, sub_list,  analysis_name, template_name, roi_name):
    '''
    Create group map by loading each subject's map and taking the median
    '''
    print(f'Creating group map for {group}')
    #load template
    template_file = f'{out_dir}/templates/{group_template}.nii.gz'
    affine = image.load_img(template_file).affine
    header = image.load_img(template_file).header

    

    results_dir = f'{out_dir}/derivatives/{analysis_name}'
    #create results dir
    os.makedirs(f'{results_dir}/{analysis_name}', exist_ok = True)

    #loop through hemis
    for hemi in params.hemis:
        #load roi mask
        '''
        NEED TO MAKE THIS WORK FOR THE GROUP
        '''
        roi_name = params.load_roi_info(roi)
        curr_roi = f'{out_dir}/atlases/{roi_name}.nii.gz'
        #replace hemi in curr_roi
        curr_roi = curr_roi.replace('hemi', hemi)
        #create masker
        brain_masker = NiftiMasker(curr_roi)

        all_maps = []
        for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
            sub_dir = f'{out_dir}/{sub}/{ses}'

            curr_map = image.load_img(f'{sub_dir}/derivatives/{analysis_name}/{hemi}_{analysis_name}_map_{template_name}.nii.gz')
            #apply mask
            curr_map = brain_masker.fit_transform(curr_map)
            #convert back to nifti
            curr_map = brain_masker.inverse_transform(curr_map)
            curr_map = curr_map.get_fdata()
            all_maps.append(curr_map)

        #convert to numpy array
        all_maps = np.array(all_maps)

        #take median across subjects
        group_map = np.median(all_maps, axis = 0)

        #save
        group_map = nib.Nifti1Image(group_map, affine, header)
        group_map.to_filename(f'{results_dir}/{hemi}_{analysis_name}_map_{template_name}.nii.gz')

    





#loop through subjects
for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
    #set seed dir
    seed_file = f'{out_dir}/{sub}/{ses}/derivatives/timeseries/{sub}_{ses}_{seed_atlas}_hemi_ts.npy'
    target_file = f'{out_dir}/{sub}/{ses}/{target_dir}'
    results_dir = f'{out_dir}/{sub}/{ses}/derivatives'

    
    #compute seed to roi correlations
    compute_correlations(sub, ses,raw_func_dir, seed_file, target_file)

    #register correlations to template
    register_to_template(sub, ses,analysis_name, group_template, template_name)




#create_group_map(group, sub_list,  analysis_name, template_name,target_name)


