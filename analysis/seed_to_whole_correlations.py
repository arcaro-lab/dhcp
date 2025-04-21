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


import pdb

import warnings
warnings.filterwarnings("ignore")

import dhcp_params as params
import subprocess
from glob import glob as glob
import shutil


#read atlas and group info as args

group = sys.argv[1]
seed_atlas = sys.argv[2]
target_roi = sys.argv[3]

#group = 'infant'
#seed_atlas = 'wang'
#target_roi = 'brain'

#load atlast name and roi labels
atlas_info = params.load_atlas_info(seed_atlas)

atlas_name, roi_labels = atlas_info.atlas_name, atlas_info.roi_labels


group_params = params.load_group_params(group)
#load individual infant data
sub_info = group_params.sub_list
sub_info = sub_info[(sub_info[f'{seed_atlas}_ts'] == 1) & (sub_info[f'{seed_atlas}_exclude'] != 1)]

#add age
sub_info['age'] = (sub_info['scan_age'] - sub_info['birth_age'])*7

age_bins = [26,33, 38,42,46]
age_groups = ['pre','early','term','post']

#add age group to sub_info
for i in range(len(age_bins)-1):
    sub_info.loc[(sub_info['scan_age'] >= age_bins[i]) & (sub_info['scan_age'] < age_bins[i+1]), 'age_group'] = age_groups[i]

#load only subs with two sessions
#sub_info = sub_info[sub_info.duplicated(subset = 'participant_id', keep = False)]
#sub_info = sub_info.reset_index()

#invert order of sub_info
#sub_info = sub_info.iloc[::-1]

#sub_info = sub_info.iloc[70:len(sub_info)]

out_dir = group_params.out_dir


#load roi info
roi_info = params.load_roi_info(target_roi)

#sub = sys.argv[1]
#ses = sys.argv[2]
#atlas = sys.argv[3]
#target = sys.argv[4]
target_name = roi_info.roi_name
target_dir = f'rois/{target_roi}/hemi_{target_roi}.nii.gz' 

analysis_name = target_roi

results_dir = f'{out_dir}/derivatives/{target_roi}'
#create results dir

#Flag for checking whether to rerun the analysis
rerun = True

def compute_correlations(sub, ses, func_dir, seed_file):
    '''
    Computes seed-to-whole brain correlations
    '''

    print(f'Computing correlations for {sub} {ses}')


    results_dir = f'{out_dir}/{sub}/{ses}/derivatives'
    os.makedirs(f'{results_dir}/{analysis_name}', exist_ok = True)

    if rerun == False:
        if os.path.exists(f'{results_dir}/{analysis_name}/{group_params.hemis[0]}_{analysis_name}_map.nii.gz') == True:
            print(f'{sub} {ses} seed to whole already computed')
            return


    func_files =  glob(f'{func_dir}/{sub}/{ses}/func/*_bold.nii.gz')

    
    #func_img = image.load_img(f'{func_dir}/{sub}/{ses}/func/{sub}_{ses}_{group_params.func_suf}.nii.gz')

    #check if brain mask exists
    if os.path.exists(f'{out_dir}/{sub}/{ses}/anat/{sub}_{ses}_{group_params.brain_mask_suf}_epi.nii.gz'):
        brain_roi = image.load_img(f'{out_dir}/{sub}/{ses}/anat/{sub}_{ses}_{group_params.brain_mask_suf}_epi.nii.gz')
        brain_masker = NiftiMasker(brain_roi, standardize=True)
    elif os.path.exists(f'{out_dir}/{sub}/{ses}/anat/{sub}_{ses}_desc_brain_mask_epi.nii.gz'):
        brain_roi = image.load_img(f'{out_dir}/{sub}/{ses}/anat/{sub}_{ses}_desc_brain_mask_epi.nii.gz')
        brain_masker = NiftiMasker(brain_roi, standardize=True)
    else:
        print(f'No brain mask found for {sub}')
        return


    
    for hemi in group_params.hemis:
        curr_seed = seed_file.replace('hemi', hemi)
        

        #load data from seed
        seed_ts = np.load(curr_seed)
        seed_ts = seed_ts.T

        curr_target = target_file.replace('hemi', hemi)
        all_funcs = []
        #load func data
        for n, func_file in enumerate(func_files):
            
            #load func
            try:

                func_img = image.load_img(func_file)
                
                
            except:
                print(f'Error loading {func_file}')
                continue


            run_ts = brain_masker.fit_transform(func_img)

            all_funcs.append(run_ts)

        target_ts = np.concatenate(all_funcs, axis = 0)

        affine = func_img.affine
        header = func_img.header

        #index first image of func
        dummy_img = func_img.slicer[:,:,:,0]


        '''
        Run correlations for individual ROI maps
        '''
        all_maps = []
        for n, ts in enumerate(seed_ts):
            #get roi label
            roi = roi_labels['label'][n]

            #standardize ts
            ts = (ts - np.mean(ts)) / np.std(ts)
            
            #compute correlation between seed and brain
            seed_to_voxel_correlations = (np.dot(target_ts.T, ts) /
                                        ts.shape[0])
            
            #target_ts.shape = 4600,28807
            #ts.shape = 4600
            
            
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
        #roi_masker = NiftiMasker(target_roi, smoothing_fwhm=0)
        #smoothed_map = brain_masker.fit_transform(max_map)

        #convert back to nifti
        #smoothed_map = brain_masker.inverse_transform(smoothed_map)

        #save map
        nib.save(max_map, f'{results_dir}/{analysis_name}/{hemi}_{analysis_name}_map.nii.gz')



def compute_2ndorder_correlations(sub, ses):
    '''
    Computes 2nd order correlations between seed-to-roi correlations
    '''

    print(f'Computing second order correlations for {sub}')
    sub_dir = f'{out_dir}/{sub}/{ses}'
    results_dir = f'{sub_dir}/derivatives/{analysis_name}'
    #create results dir
    os.makedirs(results_dir, exist_ok = True)

    timseries_dir = f'{sub_dir}/derivatives/timeseries'



    brain_mask = f'{params.atlas_dir}/templates/mni_icbm152_t1_tal_nlin_asym_09a_brain_binary.nii.gz'
    brain_masker = NiftiMasker(brain_mask, standardize = False)

    #check if first roi exists

    
    for hemi in params.hemis:
        #load roi mask

        data_dir = f'{sub_dir}/derivatives/brain'
       

        #check if whole_brain image exists        
        if not os.path.exists(f'{data_dir}/{params.hemis[0]}_{roi_labels["label"][0]}_corr_MNI.nii.gz'):
            print(f'No first order correlations found for {sub}')
            return
            
        
        
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

            roi_img = image.load_img(f'{data_dir}/{hemi}_{roi}_corr_MNI.nii.gz')

            #extract data
            roi_data = brain_masker.fit_transform(roi_img)
            
            #flatten
            #roi_data = roi_data.flatten()

            #append to list
            all_rois.append(roi_data)


        #convert to array
        all_rois = np.array(all_rois)
        #pdb.set_trace()
        #fisher z transform
        all_rois = np.arctanh(all_rois)

        #squeeze
        all_rois = all_rois.squeeze()

        #create zero array with shape of all_rois
        second_order_rdm = np.zeros(all_rois.shape)
        

        for rn,roi in enumerate(roi_labels['label']):
            #remove current roi from rdm
            curr_seed_rdm = np.delete(seed_rdm[rn,:], rn)
            curr_roi_rdms = np.delete(all_rois, rn, axis = 0)

            #zscore curr_seed_rdm and curr_roi_rdms
            curr_seed_rdm = (curr_seed_rdm - np.mean(curr_seed_rdm)) / np.std(curr_seed_rdm)
            curr_roi_rdms = (curr_roi_rdms - np.mean(curr_roi_rdms, axis = 0)) / np.std(curr_roi_rdms, axis = 0)

            
            seed_to_roi_correlation = (np.dot(curr_roi_rdms.T, curr_seed_rdm) / curr_seed_rdm.shape[0])
            second_order_rdm[rn,:] = seed_to_roi_correlation
            
            #reshape to match roi_data
            curr_roi_corr = seed_to_roi_correlation.reshape(roi_data.shape)

            #transform it back to brain space
            curr_roi_img = brain_masker.inverse_transform(curr_roi_corr)

            #drop last dimension
            #curr_roi = curr_roi.slicer[:,:,:,0]
            
            #make 0s nans
            curr_roi_img = image.math_img('np.where(img == 0, np.nan, img)', img = curr_roi_img)
            
        
            #save it
            curr_roi_img.to_filename(f'{results_dir}/{hemi}_{roi}_second_order_MNI.nii.gz')
            

        #remove middle dimension
        second_order_rdm = second_order_rdm.squeeze()
        #save second order rdm
        np.save(f'{results_dir}/{hemi}_{seed_atlas}_second_order_rdm.npy', second_order_rdm)
#        pdb.set_trace()

def register_indiv_map_to_template(group, sub, ses):
    '''
    Loop through rois of atlas and register to template
    
    '''
    print(f'Registering indiv maps {sub} {analysis_name} to template')
    sub_dir = f'{out_dir}/{sub}/{ses}'
    results_dir = f'{sub_dir}/derivatives/{analysis_name}'

    #check if files already exist
    if rerun == False:
        if os.path.exists(f'{results_dir}/lh_SPL1_corr_{group_params.template_name}.nii.gz') == True:
            print(f'{sub} {ses} already registered to template')
            return



    template_img = image.load_img(group_params.group_template + '.nii.gz')
    template_affine = template_img.affine

    xfm = group_params.func2template.replace('*SUB*', sub).replace('*SES*', ses)
    for hemi in group_params.hemis:
        for n, roi in enumerate(roi_labels['label']):
            curr_map = f'{results_dir}/{hemi}_{roi}_corr'

            curr_map_img = image.load_img(f'{curr_map}.nii.gz')
            curr_map_affine = curr_map_img.affine

            #check if they are identical
            if np.array_equal(curr_map_affine, template_affine):
                pass
            else:

                if group == 'infant':
                    #apply transformations to roi
                    bash_cmd = f'applywarp -i {curr_map}.nii.gz -r {group_params.group_template} -w {xfm} -o {curr_map}_{group_params.template_name}.nii.gz'
                    subprocess.run(bash_cmd, shell=True)

                elif group == 'adult':
                    #check if xfm already exists
                    if os.path.exists(xfm) == False:
                        #create transformation by inverting template2anat
                        bash_cmd = f'convert_xfm -omat {sub_dir}/xfm/anat2template.mat -inverse {sub_dir}/xfm/template2anat.mat'
                        subprocess.run(bash_cmd, shell=True)

                        #copy xfm as template2func
                        shutil.copy(f'{sub_dir}/xfm/anat2template.mat', f'{sub_dir}/xfm/func2template.mat')

                    #pdb.set_trace()
                    bash_cmd = f'flirt -in {curr_map}.nii.gz -ref {group_params.group_template}.nii.gz -applyxfm -init {xfm} -out {curr_map}_{group_params.template_name}.nii.gz'
                    subprocess.run(bash_cmd, shell=True)

def register_40wk_to_mni(sub, ses):
    '''
    Register 40wk to MNI
    '''
    print(f'Registering 40wk to MNI {sub}')
    
    sub_dir = f'{out_dir}/{sub}/{ses}'
    results_dir = f'{sub_dir}/derivatives/{analysis_name}'

    #check if files already exist
    if rerun == False:
        if os.path.exists(f'{results_dir}/lh_SPL1_corr_MNI.nii.gz') == True:
            print(f'{sub} {ses} already registered to MNI')
            return

    mni = f'{params.atlas_dir}/templates/mni_icbm152_t1_tal_nlin_asym_09a_brain.nii.gz'
    xfm = f'{params.atlas_dir}/templates/xfm/extdhcp40wk_to_MNI152NLin2009aAsym_warp.nii.gz'

    for hemi in group_params.hemis:
        for n, roi in enumerate(roi_labels['label']):
            curr_map = f'{results_dir}/{hemi}_{roi}_corr'

    
            
            bash_cmd = f'applywarp -i {curr_map}_40wk.nii.gz -r {mni} -w {xfm} -o {curr_map}_MNI.nii.gz'
            subprocess.run(bash_cmd, shell=True)

def register_max_to_template(group, sub, ses,analysis_name, template,template_name):
    '''
    Register max map to template
    '''
    print(f'Registering max map {sub} {analysis_name} to {template}')
    sub_dir = f'{out_dir}/{sub}/{ses}'
    results_dir = f'{sub_dir}/derivatives/{analysis_name}'

    warp = f'{group_params.raw_func_dir}/{sub}/{ses}/xfm/{sub}_{ses}_from-bold_to-extdhcp40wk_mode-image.nii.gz'
    for hemi in group_params.hemis:
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


            


def create_group_map(group, sub_list, suf ='_corr_40wk',out_suf ='_day1'):
    '''
    Create group map by loading each subject's map and taking the mean 
    '''
    print(f'Creating group map for {group}')
    
    group_params = params.load_group_params(group)
    #roi_info = params.load_roi_info(roi_name)
    #load template
    template_file = group_params.group_template + '.nii.gz'
    #roi_name = f'{params.atlas_dir}/{roi_info.roi_name}.nii.gz'

    brain_mask = group_params.group_template + '_brain_mask.nii.gz'
    brain_masker = NiftiMasker(brain_mask, standardize = False)

    #load roi mask
    

    affine = image.load_img(template_file).affine
    header = image.load_img(template_file).header

    

    results_dir = f'{out_dir}/derivatives/{analysis_name}'
    #create results dir
    os.makedirs(f'{results_dir}/{analysis_name}', exist_ok = True)
    

    #loop through hemis
    for hemi in group_params.hemis:
        #replace hemi in curr_roi
        #curr_roi = roi_name.replace('hemi', hemi)
        #create masker
        #roi_masker = NiftiMasker(curr_roi,standardize = standardize)
                                 
        #load roi mask
        for n, roi in enumerate(roi_labels['label']):
            print(f'Creating group map for {hemi} {roi} {n}/{len(roi_labels)}')          
        
        
            all_maps = []
            for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
                sub_dir = f'{out_dir}/{sub}/{ses}'
           
                curr_map = f'{sub_dir}/derivatives/brain/{hemi}_{roi}{suf}.nii.gz'

                #check if file exists
                if os.path.exists(curr_map) == False:
                    print(f'No map found for {sub} {ses} {hemi} {roi}')
                    continue

                curr_map = image.load_img(curr_map)
                #apply mask
                curr_map = brain_masker.fit_transform(curr_map)
                #convert back to nifti
                #curr_map = roi_masker.inverse_transform(curr_map)

                #fisher z transform
                curr_map = np.arctanh(curr_map)
                #standardize
                #curr_map = (curr_map - np.mean(curr_map)) / np.std(curr_map)
                
                all_maps.append(curr_map)

            #convert to numpy array
            all_maps = np.array(all_maps)

            #take median across subjects
            group_map = np.median(all_maps, axis = 0)

            #save as numpy array
            np.save(f'{results_dir}/{hemi}_{roi}.npy', group_map)

            #inverse transform to nifti
            group_img = brain_masker.inverse_transform(group_map)
            group_img.to_filename(f'{results_dir}/{hemi}_{roi}{suf}{out_suf}.nii.gz')

        




n = 0 
#loop through subjects
for sub, ses in zip(sub_info['participant_id'], sub_info['ses']):
    break
    #print progress
    n += 1
    print(f'{n}/{len(sub_info)}')

    #set seed dir
    seed_file = f'{out_dir}/{sub}/{ses}/derivatives/timeseries/{sub}_{ses}_{seed_atlas}_hemi_ts.npy'
    target_file = f'{out_dir}/{sub}/{ses}/{target_dir}'
    results_dir = f'{out_dir}/{sub}/{ses}/derivatives'

  
    try: 
        #compute seed to roi correlations
        compute_correlations(sub, ses,group_params.raw_func_dir, seed_file)
    except:
        print(f'Error computing correlations for {sub} {ses}')
    
    try:
        #register correlations to template group-specific template
        register_indiv_map_to_template(group, sub, ses)
    except:
        print(f'Error registering {sub} {ses} to template')
        
    #register correlations to mni
    #register_40wk_to_mni(sub, ses)

    #compute 2nd order corr
    #compute_2ndorder_correlations(sub, ses)

    

    
#create group map for day 1 sub
day1_subs = sub_info[(sub_info['age'] <= 1) & (sub_info['age_group'] == 'term') | (sub_info['age'] <= 1) & (sub_info['age_group'] == 'post')]
#pdb.set_trace()
create_group_map(group, day1_subs,  '_corr_40wk', '_day1')


#create group map by age group
for i, age_group in enumerate(age_groups):
    #get subs in age group
    age_subs = sub_info[sub_info['age_group'] == age_group]
    #create group map
    create_group_map(group, age_subs,  '_corr_40wk', f'_{age_group}')


