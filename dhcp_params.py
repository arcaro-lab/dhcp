project_name = 'dhcp'
import os
#get current working directory
cwd = os.getcwd()
git_dir = cwd.split(project_name)[0] + project_name
import sys

#add git_dir to path
sys.path.append(git_dir)
import pandas as pd
#set directories

#how much to smooth functional data
smooth_mm = 4
vols = 2300

group= 'infant'

results_dir = f'{git_dir}/results'
fig_dir = f'{git_dir}/figures'

def load_group_params(group):
    '''
    Define directories based on age group
    '''
    if group == 'infant':
            
        #dhcp data directories
        raw_data_dir = '/mnt/DataDrive1/data_raw/human_mri/dhcp_raw/'
        raw_anat_dir = f'{raw_data_dir}/rel3_dhcp_anat_pipeline'
        raw_func_dir = f'{raw_data_dir}/rel3_dhcp_fmri_pipeline'
        out_dir = '/mnt/DataDrive1/data_preproc/human_mri/dhcp_preprocessed'
        anat_suf = f'desc-restore_T2w' 
        func_suf = f'task-rest_desc-preproc_bold'

        brain_mask_suf = 'desc-ribbon_dseg'
        group_template = 'week40_T2w'
        template_name = '40wk'

        

    elif group == 'adult':
        #7T hcp data directories
        raw_data_dir = '/mnt/f/7T_HCP'
        raw_anat_dir = f'{raw_data_dir}'
        raw_func_dir = f'{raw_data_dir}'
        out_dir = '/mnt/f/7T_HCP'
        anat_suf = f'restore-1.60_T1w'
        func_suf = f'task-rest_run-01_preproc_bold'

        brain_mask_suf = None
        group_template = 'MNI152_2009_SurfVol'
        template_name = 'MNI152'


    elif group == 'diffusion':
         #7T hcp data directories
        raw_data_dir = '/mnt/e/diffusion/FinalData'
        raw_anat_dir = f'{raw_data_dir}/rel3_dhcp_anat_pipeline'
        raw_func_dir = f'{raw_data_dir}/rel3_dhcp_fmri_pipeline'
        out_dir = {raw_data_dir}
        anat_suf = f'desc-restore_T2w' 
        func_suf = f'task-rest_desc-preproc_bold'

        brain_mask_suf = 'desc-brain_mask'

        group_template = 'MNI152_2009_SurfVol'
        template_name = 'MNI152'


    return raw_data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf, brain_mask_suf, group_template, template_name


raw_data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf, brain_mask_suf, group_template,template_name = load_group_params(group)


atlas_dir = f'{out_dir}/atlases'
derivatives_dir = f'{out_dir}/derivatives'

hemis = ['lh','rh']


def load_atlas_info(atlas):
    '''
    Load atlas info 
    '''
    if atlas == 'wang':
        atlas_name = f'Wang_maxprob_surf_hemi_edits'
        roi_labels = pd.read_csv(f'{atlas_dir}/Wang_labels.csv')

        #remove FEF from roi_labels
        roi_labels = roi_labels[roi_labels['label'] != 'FEF']

    elif atlas == 'object':
        atlas_name  = 'objectareas_fullnode_hemi'
        roi_labels = pd.read_csv(f'{atlas_dir}/object_labels.csv')

    elif atlas == 'calcsulc':
        atlas_name  = 'calcsulc_binnedroi_hemi'
        roi_labels = pd.read_csv(f'{atlas_dir}/calcsulc_labels.csv')

    return atlas_name, roi_labels

def load_roi_info(roi):
    '''
    Load ROI info
    '''

    if roi == 'pulvinar':
        roi_name = 'rois/pulvinar/40wk/pulvinar_hemi'
        template = 'templates/week40_T2w'
        template_name = '40wk'

        roi_labels = pd.read_csv(f'{atlas_dir}/pulvinar_labels.csv')
        
        '''
        NEED TO MAKE THIS WORK FOR THE GROUP
        '''
    if roi == 'wang': 
        roi_name = 'wang'
        template = 'wang'
        template_name = 'wang'


    if roi == 'brain':
        roi_name = 'anat/brain'
        template = 'brain'
        template_name = 'brain'

    return roi_name, roi_labels, template, template_name