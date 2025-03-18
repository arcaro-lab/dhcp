'''
ROI correlations between infants and adult group map

This version uses diffusion data for the pulvinar
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
from glob import glob as glob
import shutil

atlas = 'wang'
target_roi = 'pulvinar'
#load atlast name and roi labels
atlas_info = params.load_atlas_info(atlas)

atlas_name, roi_labels = atlas_info.atlas_name, atlas_info.roi_labels

#load infant info
group_params = params.load_group_params('infant')
#load individual infant data
sub_info = group_params.sub_list
sub_info = sub_info[(sub_info[f'{atlas}_ts'] == 1) & (sub_info[f'{atlas}_exclude'] != 1)]

#load data wang_probtrackx
sub_info = sub_info[(sub_info['wang_probtrackx'] == 1)]

#load only subs with two sessions
sub_info = sub_info[sub_info.duplicated(subset = 'participant_id', keep = False)]

#load infant adult cortical correlations
sub_data = pd.read_csv(f'{group_params.out_dir}/derivatives/{atlas}/infant_adult_wang_correlations.csv')

#set up adult directories
adult_params = params.load_group_params('adult')

adult_data_dir = f'{adult_params.out_dir}/derivatives/dwi_seeds'

roi_info = params.load_roi_info(f'{target_roi}_40wk')
roi_name = f'{params.atlas_dir}/{roi_info.roi_name}.nii.gz'
roi_name = f'{params.atlas_dir}/{roi_info.roi_name}.nii.gz'

summary_df = pd.DataFrame(columns = ['sub', 'roi','network','t1_age','t2_age','age_diff','t1_cortex_corr','t2_cortex_corr', f't1_{target_roi}_corr', f't2_{target_roi}_corr'])

#set up maskers
lh_masker = NiftiMasker(roi_name.replace('hemi','lh'),standardize = True)
rh_masker = NiftiMasker(roi_name.replace('hemi','rh'),standardize = True)
                        
#target suffix
suf = '_corr_MNI'
#suf = '_second_order_MNI'

rerun = True


#loop through ROIs in atlas
for roi, network in zip(roi_labels['label'], roi_labels['network']):
    print(roi)

    #load adult group map
    lh_adult_map_img = image.load_img(f'{group_dir}/lh_{roi}{suf}.nii.gz')
    rh_adult_map_img = image.load_img(f'{group_dir}/rh_{roi}{suf}.nii.gz')

    lh_adult_map = lh_masker.fit_transform(lh_adult_map_img)
    rh_adult_map = rh_masker.fit_transform(rh_adult_map_img)

    #loop through unique subs in sub_info
    for sub in sub_info['participant_id'].unique():
            #curr_sub data
        curr_sub = sub_data[sub_data['sub'] == sub]

        #determine which ses is first using scan_age
        ses1 = curr_sub[curr_sub['scan_age'] == np.min(curr_sub['scan_age'])]['ses'].values[0]
        ses2 = curr_sub[curr_sub['scan_age'] == np.max(curr_sub['scan_age'])]['ses'].values[0]

        ses1_dir = f'{group_params.out_dir}/{sub}/{ses1}/derivatives/pulvinar_adult'
        ses2_dir = f'{group_params.out_dir}/{sub}/{ses2}/derivatives/pulvinar_adult'

        #get ages from ses1 and ses2
        t1_age = curr_sub[curr_sub['ses'] == ses1]['scan_age'].values[0]
        t2_age = curr_sub[curr_sub['ses'] == ses2]['scan_age'].values[0]
        age_diff = t2_age - t1_age
        hemi_data1 = []
        hemi_data2 = [] 

        
        
        #extract data from each session
        lh_t1_cortex_corr = curr_sub[(curr_sub['sub'] == sub) & (curr_sub['ses'] == ses1) & (curr_sub['infant_roi'] == roi) & (curr_sub['hemi'] == 'lh') & (curr_sub['roi_similarity'] == 'same') & (curr_sub['hemi_similarity'] == 'same')]['corr']
        

        rh_t1_cortex_corr = curr_sub[(curr_sub['sub'] == sub) & (curr_sub['ses'] == ses1) & (curr_sub['infant_roi'] == roi) & (curr_sub['hemi'] == 'rh') & (curr_sub['roi_similarity'] == 'same')& (curr_sub['hemi_similarity'] == 'same')]['corr']
        lh_t2_cortex_corr = curr_sub[(curr_sub['sub'] == sub) & (curr_sub['ses'] == ses2) & (curr_sub['infant_roi'] == roi) & (curr_sub['hemi'] == 'lh') & (curr_sub['roi_similarity'] == 'same')& (curr_sub['hemi_similarity'] == 'same')]['corr'].values[0]
        rh_t2_cortex_corr = curr_sub[(curr_sub['sub'] == sub) & (curr_sub['ses'] == ses2) & (curr_sub['infant_roi'] == roi) & (curr_sub['hemi'] == 'rh') & (curr_sub['roi_similarity'] == 'same')& (curr_sub['hemi_similarity'] == 'same')]['corr'].values[0]
        
        t1_cortex_corr = np.mean([lh_t1_cortex_corr, rh_t1_cortex_corr])
        t2_cortex_corr = np.mean([lh_t2_cortex_corr, rh_t2_cortex_corr])
        
        #loop through hemis
        for hemi in ['lh', 'rh']:

            if hemi == 'lh':
                roi_masker = lh_masker
                adult_map = lh_adult_map
            else:
                roi_masker = rh_masker
                adult_map = rh_adult_map
            
            adult_map = np.squeeze(adult_map)
            
            
            
            #check if numpy array of data exists
            if os.path.exists(f'{ses2_dir}/{hemi}_{roi}{suf}.npy' and rerun == False):
                #load data
                ses1_data = np.load(f'{ses1_dir}/{hemi}_{roi}{suf}.npy').flatten()
                ses2_data = np.load(f'{ses2_dir}/{hemi}_{roi}{suf}.npy').flatten()
            else:

                ses1_map = image.load_img(f'{group_params.out_dir}/{sub}/{ses1}/derivatives/pulvinar_adult/{hemi}_{roi}{suf}.nii.gz')
                ses2_map = image.load_img(f'{group_params.out_dir}/{sub}/{ses2}/derivatives/pulvinar_adult/{hemi}_{roi}{suf}.nii.gz')

                #extract data from each
                ses1_data = roi_masker.fit_transform(ses1_map)
                ses2_data = roi_masker.fit_transform(ses2_map)

                #save as numpy array
                np.save(f'{group_params.out_dir}/{sub}/{ses1}/derivatives/pulvinar_adult/{hemi}_{roi}{suf}.npy', ses1_data)
                np.save(f'{group_params.out_dir}/{sub}/{ses2}/derivatives/pulvinar_adult/{hemi}_{roi}{suf}.npy', ses2_data)
            
            #correlate with adult group map
            #include values that are greater than 0 in infant map
            ses1_ind = np.where(ses1_data > 0)
            ses2_ind = np.where(ses2_data > 0)
            corr1 = np.corrcoef(adult_map[ses1_ind], ses1_data[ses1_ind])[0,1]
            corr2 = np.corrcoef(adult_map[ses2_ind], ses2_data[ses2_ind])[0,1]

            hemi_data1.append(corr1)
            hemi_data2.append(corr2)
        

        #compute mean correlation across hemis for each session
        t1_corr = np.mean(hemi_data1)
        t2_corr = np.mean(hemi_data2)


        #add to summary_df using concat
        summary_df = pd.concat([summary_df, pd.DataFrame({'sub':sub,
                                                        'roi':roi,
                                                        'network':network,
                                                        't1_age':t1_age,
                                                        't2_age':t2_age,
                                                        'age_diff':age_diff,
                                                        't1_cortex_corr':t1_cortex_corr,
                                                        't2_cortex_corr':t2_cortex_corr,
                                                        f't1_{target_roi}_corr':t1_corr,
                                                        f't2_{target_roi}_corr':t2_corr}, index = [0])])



    #save summary_df
    summary_df.to_csv(f'{git_dir}/results/roi_corrs/pulvinar_session_correlations{suf}.csv', index = False)




