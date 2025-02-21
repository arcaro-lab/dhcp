'''
Compute second-order similarity for a region

e.g., create a voxel x network map for the pulvinar of each subject
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

analysis_name = 'pulvinar'
seed_atlas = 'wang'
target_roi = 'pulvinar'


sub_list = pd.read_csv(f'{git_dir}/participants_dhcp.csv')
sub_list = sub_list[sub_list[f'{seed_atlas}_ts'] == 1]
#sub_list = sub_list[sub_list[f'{target_roi}_reg'] == 1]

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



def compute_indiv_correlations(sub, ses,img_space):
    print(f'Computing second order correlations for {sub}')
    sub_dir = f'{out_dir}/{sub}/{ses}'
    results_dir = f'{sub_dir}/derivatives/{analysis_name}'
    timseries_dir = f'{sub_dir}/derivatives/timeseries'

    #check if first roi exists

    
    for hemi in params.hemis:
        #load roi mask
        if img_space == 'epi':
            data_dir = f'{sub_dir}/derivatives/whole_brain'
            roi_dir = f'{sub_dir}/rois'
            target_mask = image.load_img(f'{roi_dir}/{target_roi}/{hemi}_{target_roi}_epi.nii.gz')
            #img_space=''
        else:
            data_dir = f'{sub_dir}/derivatives/whole_brain'
            roi_dir = f'{out_dir}/atlases/rois/{target_roi}/{img_space}'
            target_mask = image.load_img(f'{roi_dir}/{target_roi}_{hemi}.nii.gz')

        

        #check if whole_brain image exists

        
        if not os.path.exists(f'{data_dir}/{params.hemis[0]}_{roi_labels["label"][0]}_corr.nii.gz'):
            print(f'No first order correlations found for {sub}')
            return
            
        
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
            if img_space == 'epi':
                roi_img = image.load_img(f'{data_dir}/{hemi}_{roi}_corr.nii.gz')
            else:
                roi_img = image.load_img(f'{data_dir}/{hemi}_{roi}_corr_{img_space}.nii.gz')

            #extract data
            roi_data = masker.fit_transform(roi_img)
            
            #flatten
            #roi_data = roi_data.flatten()

            #append to list
            all_rois.append(roi_data)


        #convert to array
        all_rois = np.array(all_rois)
        #pdb.set_trace()
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
            
            #make 0s nans
            curr_roi = image.math_img('np.where(img == 0, np.nan, img)', img = curr_roi)
            

        
            #save it
            curr_roi.to_filename(f'{results_dir}/{hemi}_{roi}_second_order_{img_space}.nii.gz')
            

        #remove middle dimension
        second_order_rdm = second_order_rdm.squeeze()
        #save second order rdm
        np.save(f'{results_dir}/{hemi}_second_order_rdm.npy', second_order_rdm)

def register_to_template(sub, ses, in_space, out_space):
    '''
    Use ANTS to register map to template
    '''
    
    sub_dir = f'{out_dir}/{sub}/{ses}'
    ref, warp, method = params.transform_map(in_space, out_space)
    print(f'Registering {sub} {analysis_name} to {out_space}')

    #warp = f'{params.raw_func_dir}/{sub}/{ses}/xfm/{xfm.replace('*SUB*', sub).replace('*SES*', ses)}.nii.gz'

    results_dir = f'{sub_dir}/derivatives/{analysis_name}'
    for hemi in params.hemis:
        for roi in roi_labels['label']:

            curr_map = f'{results_dir}/{hemi}_{roi}_second_order_epi_{in_space}'

            if method == 'ants':

                #register to anat using flirt
                bash_cmd = f'flirt -in {curr_map}.nii.gz -ref {sub_dir}/anat/{sub}_{ses}_{anat_suf}_brain.nii.gz -out {curr_map}_anat.nii.gz -applyxfm -init {sub_dir}/xfm/func2anat.mat -interp trilinear'
                subprocess.run(bash_cmd, shell=True)


                #apply transformations to roi
                bash_cmd = f"antsApplyTransforms \
                    -d 3 \
                        -i {curr_map}_anat.nii.gz \
                            -r  {out_dir}/templates/{template}.nii.gz \
                                -t {sub_dir}/xfm/{template_name}2anat1InverseWarp.nii.gz \
                                    -t [{sub_dir}/xfm/{template_name}2anat0GenericAffine.mat, 1] \
                                        -o {curr_map}_{template_name}.nii.gz \
                                            -n Linear"
                subprocess.run(bash_cmd, shell=True)  

            elif method == 'applywarp':
                
                bash_cmd = f'applywarp -i {curr_map}.nii.gz -r {ref}.nii.gz -w {warp} -o {curr_map.replace(in_space,out_space)}.nii.gz --interp=trilinear'
                
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
        #brain_masker = image.load_img(curr_target)
        #binarize it
        #brain_masker = image.math_img('img > 0', img = brain_masker)
        

        for roi in roi_labels['label']:

            all_maps = []
            for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
                sub_dir = f'{out_dir}/{sub}/{ses}'
                data_dir = f'{sub_dir}/derivatives/{analysis_name}'

                #check if map exists
                if not os.path.exists(f'{data_dir}/{hemi}_{roi}_second_order{template_name}.nii.gz'):
                    print(f'No second order correlation found for {sub}')
                    continue

                curr_map = image.load_img(f'{data_dir}/{hemi}_{roi}_second_order{template_name}.nii.gz')
                #apply mask

                curr_map = curr_map.get_fdata()

                #fisher z transform
                #curr_map = np.tanh(curr_map)
                all_maps.append(curr_map)

            #convert to numpy array
            all_maps = np.array(all_maps)

            #take mean across subjects
            #group_map = np.mean(all_maps, axis = 0)

            #take median across subjects
            group_map = np.median(all_maps, axis = 0)

            #convert to nifti
            group_map = nib.Nifti1Image(group_map, affine, header)

            #apply mask
            #group_map = image.math_img('img * mask', img = group_map, mask = brain_masker)
            #make 0s nans
            group_map = image.math_img('np.where(img == 0, np.nan, img)', img = group_map)

            #save
            group_map.to_filename(f'{results_dir}/{hemi}_{roi}_second_order_corrs_{template_name}.nii.gz')


#loop through subjects
for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
    
    #compute_indiv_correlations(sub, ses,'epi')

    register_to_template(sub, ses,'40wk', 'MNI152')
    

#create_group_map()