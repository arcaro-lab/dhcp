'''
whole brain correlations between atlas and brain
'''
git_dir = '/mnt/c/Users/ArcaroLab/Desktop/git_repos/dhcp'
import sys
#add git_dir to path
sys.path.append(git_dir)
import pandas as pd
from nilearn import image, plotting
#from nilearn.glm import threshold_stats_img
import numpy as np

from nilearn.maskers import NiftiMasker
import nibabel as nib
import os

import pdb

import warnings
import dhcp_params as params

#sub = sys.argv[1]
#ses = sys.argv[2]
#atlas = sys.argv[3]
#target = sys.argv[4]



#results_dir = f'{out_dir}/derivatives/retinotopy'
#create results dir


def compute_correlations(sub, ses, func_dir, seed_file, target_file):
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
        brain_masker = NiftiMasker(target_atlas,
        smoothing_fwhm=4, standardize=True)

        

        #Extract brain data
        brain_time_series = brain_masker.fit_transform(func_img)

        
        all_maps = []
        for n, ts in enumerate(seed_ts):
            #get roi label
            roi = roi_labels['label'][n]

            #compute correlation between seed and brain
            seed_to_voxel_correlations = (np.dot(brain_time_series.T, ts) /
                                        ts.shape[0])
            
            #save correlation map
            seed_to_voxel_correlations_img = brain_masker.inverse_transform(seed_to_voxel_correlations.T)

            #save correlation map
            seed_to_voxel_correlations_img.to_filename(f'{results_dir}/{analysis_name}/{hemi}_{roi}_corr.nii.gz')

            #convert to numpy array
            seed_to_voxel_correlations_img = seed_to_voxel_correlations_img.get_fdata()
            
            all_maps.append(seed_to_voxel_correlations_img)

            

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

        #smooth map
        max_map = image.smooth_img(max_map, 4)

        #save map
        nib.save(max_map, f'{results_dir}/{analysis_name}/{hemi}_{analysis_name}_map.nii.gz')


    
group = 'infant'

raw_data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf, brain_mask_suf = params.load_group_params(group)


analysis_name = 'thalmocortical'

seed_atlas = 'wang'
target_roi = 'pulvinar'
#load subject list
#load subject list
sub_list = pd.read_csv(f'{out_dir}/participants.csv')
sub_list = sub_list[sub_list[f'{seed_atlas}_ts'] == 1]
sub_list = sub_list[sub_list[f'{seed_atlas}_ts'] == 1]

#load atlas info
atlas_name, roi_labels = params.load_atlas_info(seed_atlas)

#load target atlas info
try:
    target_name, target_labels = params.load_atlas_info(target_roi)
    target_dir = f'atlas/{target_name}_epi.nii.gz'
except:
    target_name = target_roi
    target_name, _, _ = params.load_roi_info(target_roi)
    target_dir = f'rois/{target_roi}/hemi_{target_roi}_epi.nii.gz'

#loop through subjects
for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
    print(f'Computing correlations for {sub} {seed_atlas} {target_roi}')
    #set seed dir
    seed_file = f'{out_dir}/{sub}/{ses}/derivatives/timeseries/{sub}_{ses}_{seed_atlas}_hemi_ts.npy'
    target_file = f'{out_dir}/{sub}/{ses}/{target_dir}'
    results_dir = f'{out_dir}/{sub}/{ses}/derivatives/{analysis_name}'

    

    compute_correlations(sub, ses,raw_func_dir, seed_file, target_file)





