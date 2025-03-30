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
sub_info = sub_info[(sub_info['pulvinar_to_wang_probtrackx'] == 1)]

#load only subs with two sessions
sub_info = sub_info[sub_info.duplicated(subset = 'participant_id', keep = False)]

#reset index
sub_info = sub_info.reset_index(drop = True)



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
suf = '_40wk'
#suf = '_second_order_MNI'

rerun = True


for hemi in ['lh', 'rh']:

    masker = NiftiMasker(roi_name.replace('hemi', hemi), standardize = True)

    #loop through ROIs in atlas
    for roi, network in zip(roi_labels['label'], roi_labels['network']):
        print(roi)
        adult_roi = roi

        #replace names to match adult data
        adult_roi = adult_roi.replace('hMT', 'TO1').replace('MST','TO2')
        adult_roi= adult_roi.replace('V1v','V1').replace('V1d','V1').replace('V2v','V2').replace('V2d','V2')
        adult_roi = adult_roi.replace('V3v','V3').replace('V3d','V3').replace('SPL1','SPL')

        #load adult group mapGroup_dtihV4_rh_groupmax_pulvinar_zscore.nii.gz
        adult_map_img = image.load_img(f'{adult_data_dir}/Group_dti{adult_roi}_{hemi}_groupmax_pulvinar_40wk.nii.gz')


        adult_map = masker.fit_transform(adult_map_img)
        adult_map = np.squeeze(adult_map)
        

        #loop through unique subs in sub_info
        for sub in sub_info['participant_id'].unique():
                #curr_sub data
            curr_sub = sub_data[sub_data['sub'] == sub]

            #get ses1 and ses2 for sub from sub_info
            curr_sub_info = sub_info[sub_info['participant_id'] == sub]
            ses1 = curr_sub_info['ses'].values[0]
            ses2 = curr_sub_info['ses'].values[1]

            #check if sub_data has both ses
            if (curr_sub['ses'] == ses1).sum() == 0 or (curr_sub['ses'] == ses2).sum() == 0:
                continue

            #pdb.set_trace()
            #determine which ses is first using scan_age
            #ses1 = curr_sub[curr_sub['scan_age'] == np.min(curr_sub['scan_age'])]['ses'].values[0]
            #ses2 = curr_sub[curr_sub['scan_age'] == np.max(curr_sub['scan_age'])]['ses'].values[0]

            #pdb.set_trace()
            ses1_dir = f'{group_params.out_dir}/{sub}/{ses1}/derivatives/dwi_seeds'
            ses2_dir = f'{group_params.out_dir}/{sub}/{ses2}/derivatives/dwi_seeds'

            #get ages from ses1 and ses2
            t1_age = curr_sub[curr_sub['ses'] == ses1]['scan_age'].values[0]
            t2_age = curr_sub[curr_sub['ses'] == ses2]['scan_age'].values[0]
            age_diff = t2_age - t1_age
  
            
            
            #extract data from each session
            t1_cortex_corr = curr_sub[(curr_sub['sub'] == sub) & (curr_sub['ses'] == ses1) & (curr_sub['infant_roi'] == roi) & (curr_sub['hemi'] == hemi) & (curr_sub['roi_similarity'] == 'same') & (curr_sub['hemi_similarity'] == 'same')]['corr']
                        
            t2_cortex_corr = curr_sub[(curr_sub['sub'] == sub) & (curr_sub['ses'] == ses2) & (curr_sub['infant_roi'] == roi) & (curr_sub['hemi'] == hemi) & (curr_sub['roi_similarity'] == 'same')& (curr_sub['hemi_similarity'] == 'same')]['corr']
            
            


            '''
            Compute correlation between adult group map and infant data for pulvinar
            '''

            
            
            
            
            
            #check if numpy array of data exists
            if os.path.exists(f'{ses2_dir}/{hemi}_{roi}{suf}.npy') and rerun == False:
                #load data
                ses1_data = np.load(f'{ses1_dir}/{hemi}_{roi}{suf}.npy').flatten()
                ses2_data = np.load(f'{ses2_dir}/{hemi}_{roi}{suf}.npy').flatten()
            else:

                ses1_map = image.load_img(f'{group_params.out_dir}/{sub}/{ses1}/derivatives/dwi_seeds/pulvinar_seeds_to_{hemi}_{roi}{suf}.nii.gz')
                ses2_map = image.load_img(f'{group_params.out_dir}/{sub}/{ses2}/derivatives/dwi_seeds/pulvinar_seeds_to_{hemi}_{roi}{suf}.nii.gz')

                #extract data from each
                ses1_data = masker.fit_transform(ses1_map)
                ses2_data = masker.fit_transform(ses2_map)

                #save as numpy array
                np.save(f'{group_params.out_dir}/{sub}/{ses1}/derivatives/dwi_seeds/pulvinar_to_{hemi}_{roi}{suf}.npy', ses1_data)
                np.save(f'{group_params.out_dir}/{sub}/{ses2}/derivatives/dwi_seeds/pulvinar_to_{hemi}_{roi}{suf}.npy', ses2_data)
            
                
                #correlate with adult group map
                #include values that are greater than 0 in infant map
                #ses1_ind = np.where(ses1_data > 0)
                #ses2_ind = np.where(ses2_data > 0)
            t1_corr = np.corrcoef(adult_map, ses1_data)[0,1]
            t2_corr = np.corrcoef(adult_map, ses2_data)[0,1]


            



            #add to summary_df using concat
            summary_df = pd.concat([summary_df, pd.DataFrame({'sub':sub,
                                                            'roi':roi,
                                                            'network':network,
                                                            't1_age':t1_age,
                                                            't2_age':t2_age,
                                                            'age_diff':age_diff,
                                                            't1_cortex_corr':t1_cortex_corr.values[0],
                                                            't2_cortex_corr':t2_cortex_corr.values[0],
                                                            f't1_{target_roi}_corr':t1_corr,
                                                            f't2_{target_roi}_corr':t2_corr}, index = [0])])



            #save summary_df
            summary_df.to_csv(f'{git_dir}/results/roi_corrs/pulvinar_dwi_session_correlations{suf}.csv', index = False)

            


