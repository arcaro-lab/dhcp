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
smooth_mm = 0
vols = 2300

group= 'adult'

results_dir = f'{git_dir}/results'
fig_dir = f'{git_dir}/figures'
atlas_dir = '/mnt/DataDrive1/data_preproc/human_mri/dhcp_preprocessed/atlases'

class load_group_params():
    def __init__(self,group):

        '''
        Define directories based on age group
        '''
        if group == 'infant':
                
            #dhcp data directories
            self.raw_data_dir = '/mnt/DataDrive1/data_raw/human_mri/dhcp_raw'
            self.raw_anat_dir = f'{self.raw_data_dir}/rel3_dhcp_anat_pipeline'
            self.raw_func_dir = f'{self.raw_data_dir}/rel3_dhcp_fmri_pipeline'
            self.out_dir = '/mnt/DataDrive1/data_preproc/human_mri/dhcp_preprocessed'
            self.anat_suf = f'desc-restore_T2w' 
            self.func_suf = f'task-rest_desc-preproc_bold'

            self.brain_mask_suf = 'desc-ribbon_dseg'
            self.group_template = 'week40_T2w'
            self.template_name = '40wk'

            self.sub_file = f'{git_dir}/participants_dhcp.csv'


            self.sub_list = pd.read_csv(f'{git_dir}/participants_dhcp.csv')

            self.func2anat_xfm = f'{self.raw_func_dir}/*SUB*/*SES*/xfm/*SUB*_*SES*_from-bold_to-T2w_mode-image.mat'
            self.anat2func_xfm = f'{self.raw_func_dir}/*SUB*/*SES*/xfm/*SUB*_*SES*_from-T2w_to-bold_mode-image.mat'

            self.func240wk = f'{self.raw_func_dir}/*SUB*/*SES*/xfm/*SUB*_*SES*_from-bold_to-extdhcp40wk_mode-image.nii.gz'
            self.anat240wk = f'{self.raw_func_dir}/*SUB*/*SES*/xfm/*SUB*_*SES*_from-extdhcp40wk_to-bold_mode-image.nii.gz'

        elif group == 'adult':
            #7T hcp data directories
            self.raw_data_dir = '/mnt/DataDrive1/data_preproc/human_mri/7T_HCP'
            self.raw_anat_dir = f'{self.raw_data_dir}'
            self.raw_func_dir = f'{self.raw_data_dir}'
            self.out_dir = '/mnt/DataDrive1/data_preproc/human_mri/7T_HCP'
            self.anat_suf = f'restore-1.60_T1w'
            self.func_suf = f'task-rest_run-01_preproc_bold'

            self.brain_mask_suf =self.anat_suf + '_mask'
            self.group_template = 'MNI152_2009_SurfVol'
            self.template_name = 'MNI152'

            self.sub_file = f'{git_dir}/participants_7T.csv'

            
        self.sub_list = pd.read_csv(self.sub_file)

    #return raw_data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf, brain_mask_suf, group_template, template_name


#raw_data_dir, raw_anat_dir, raw_func_dir, out_dir, anat_suf, func_suf, brain_mask_suf, group_template,template_name = load_group_params('infant')


hemis = ['lh','rh']

class load_atlas_info():
    def __init__(self,atlas):

        

        '''
        Load atlas info 
        '''
        if atlas == 'wang':
            self.atlas_name = f'Wang_maxprob_surf_hemi_edits'
            self.roi_labels = pd.read_csv(f'{atlas_dir}/Wang_labels.csv')

            #remove FEF from roi_labels
            self.roi_labels = self.roi_labels[self.roi_labels['label'] != 'FEF']

        elif atlas == 'object':
            self.atlas_name  = 'objectareas_fullnode_hemi'
            self.roi_labels = pd.read_csv(f'{atlas_dir}//object_labels.csv')

        elif atlas == 'calcsulc':
            self.atlas_name  = 'calcsulc_binnedroi_hemi'
            self.roi_labels = pd.read_csv(f'{atlas_dir}/calcsulc_labels.csv')



def load_roi_info(roi):
    '''
    Load ROI info
    '''

    if roi == 'pulvinar':
        roi_name = 'rois/pulvinar/40wk/hemi_pulvinar'
        template = 'templates/week40_T2w'
        template_name = '40wk'

        roi_labels = pd.read_csv(f'atlases/pulvinar_labels.csv')

        xfm = '*SUB*_*SES*_from-bold_to-extdhcp40wk_mode-image'
        #xfm = '*SUB*_*SES*_from-extdhcp40wk_to-bold_mode-image'
        method = 'applywarp'
        
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

    return roi_name, roi_labels, template, template_name, xfm, method

def transform_map(in_space,out_space):
    if in_space == 'dchp_bold' and out_space == '40wk':
        ref = 'templates/week40_T2w'
        xfm = '*SUB*_*SES*_from-bold_to-extdhcp40wk_mode-image'
        method = 'applywarp'

    elif in_space == '40wk' and out_space == 'dchp_bold':
        ref = '*SUB*_*SES*_task-rest_desc-preproc_bold'
        xfm = '*SUB*_*SES*_from-extdhcp40wk_to-bold_mode-image'
        method = 'applywarp'

    elif in_space == '40wk' and out_space == 'MNI152':
        ref = f'{atlas_dir}/templates/mni_icbm152_t1_tal_nlin_asym_09a_brain'
        xfm = f'{atlas_dir}/templates/xfm/extdhcp40wk_to_MNI152NLin2009aAsym_warp'
        method = 'applywarp'
    
    elif in_space == 'MNI152' and out_space == '40wk':
        ref = f'{atlas_dir}/templates/week40_T2w'
        xfm = f'{atlas_dir}/templates/xfm/extdhcp40wk_to_MNI152NLin2009aAsym_invwarp.nii.gz'
        method = 'applywarp'

    return ref, xfm, method
