git_dir = '/mnt/c/Users/ArcaroLab/Desktop/git_repos/dhcp'

import pandas as pd
#set directories

#how much to smooth functional data
smooth_mm = 4

group= 'infant'

def load_group_params(group):
    '''
    Define directories based on age group
    '''
    if group == 'infant':
            
        #dhcp data directories
        raw_data_dir = '/mnt/e/dHCP_raw'
        raw_anat_dir = f'{raw_data_dir}/rel3_dhcp_anat_pipeline'
        raw_func_dir = f'{raw_data_dir}/rel3_dhcp_fmri_pipeline'
        out_dir = '/mnt/e/dhcp_analysis_full'
        anat_suf = f'desc-restore_T2w' 
        func_suf = f'task-rest_desc-preproc_bold'

    elif group == 'adult':
        #7T hcp data directories
        raw_data_dir = '/mnt/f/7T_HCP'
        raw_anat_dir = f'{raw_data_dir}'
        raw_func_dir = f'{raw_data_dir}'
        out_dir = '/mnt/f/7T_HCP'
        anat_suf = f'restore-1.60_T1w'
        func_suf = f'task-rest_run-01_preproc_bold'

    return raw_data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf


raw_data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf = load_group_params(group)


atlas_dir = f'{out_dir}/atlases'
derivatives_dir = f'{out_dir}/derivatives'

hemis = ['lh','rh']

#sub-CC00056XX07 ses-10700 wang

def load_roi_info(atlas):
    '''
    Load roi info from atlas
    '''
    if atlas == 'wang':
        atlas_name = f'Wang_maxprob_surf_hemi_edits'
        roi_labels = pd.read_csv(f'{atlas_dir}/Wang_labels.csv')

    elif atlas == 'object':
        atlas_name  = 'objectareas_fullnode_hemi'
        roi_labels = pd.read_csv(f'{atlas_dir}/object_labels.csv')


    return atlas_name, roi_labels