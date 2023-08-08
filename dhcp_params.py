git_dir = '/mnt/c/Users/ArcaroLab/Desktop/git_repos/dhcp'

import pandas as pd
#set directories
raw_data_dir = '/mnt/e/dHCP_raw'

raw_anat_dir = f'{raw_data_dir}/rel3_dhcp_anat_pipeline'
raw_func_dir = f'{raw_data_dir}/rel3_dhcp_fmri_pipeline'
out_dir = '/mnt/e/dhcp_analysis_full'
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


    return atlas_name, roi_labels