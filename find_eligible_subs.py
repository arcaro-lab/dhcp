project_name = 'dhcp'
import os
#get current working directory
cwd = os.getcwd()
git_dir = cwd.split(project_name)[0] + project_name
import sys

#add git_dir to path
sys.path.append(git_dir)


import numpy as np  
import pandas as pd
from glob import glob as glob
import pdb
import dhcp_params as params #loads group parameters
import subprocess #used to run individual phases
import time
import warnings
warnings.filterwarnings("ignore")
#print date and time
print(time.strftime("%d/%m/%Y %H:%M:%S"))

group = 'infant'
group_info = params.load_group_params(group)

#set directories
raw_data_dir = group_info.raw_data_dir

raw_anat_dir = group_info.raw_anat_dir
raw_func_dir = group_info.raw_func_dir
out_dir = group_info.out_dir


#set suffixes for anat and func files
anat_suf = group_info.anat_suf
func_suf = group_info.func_suf


atlas = 'wang'
atlas_info = params.load_atlas_info(atlas)


'''
Create new participant list with eligible subjects
'''
raw_sub_list = pd.read_csv(f'{git_dir}/participants_dhcp_full.csv')

final_sub_list = pd.DataFrame(columns=raw_sub_list.columns)

for sub in raw_sub_list['participant_id']:
    
    #load sessions file
    ses_file = pd.read_csv(f'{raw_anat_dir}/{sub}/{sub}_sessions.tsv', sep='\t')
    sess = ses_file['session_id'].values
    
    for ses in sess:
        scan_age = ses_file.loc[ses_file['session_id']==ses, 'scan_age'].values[0]
        ses = 'ses-'+str(ses)
        #check if subject has all scans
        anat_files = glob(f'{raw_anat_dir}/{sub}/{ses}/anat/*{anat_suf}.nii.gz')
        func_files = glob(f'{raw_func_dir}/{sub}/{ses}/func/*{func_suf}.nii.gz')

        
        
        #if subject has all scans, add to new list
        if len(anat_files) > 0 and len(func_files) > 0:
            sub_list = pd.DataFrame(columns=raw_sub_list.columns)
            #add subject and ses to new final_sub_list
            sub_list = pd.concat([sub_list, raw_sub_list[raw_sub_list['participant_id']==sub]], ignore_index=True)
            

            #add session and scan to new sub_list
            sub_list.loc[sub_list['participant_id']==sub, 'ses'] = ses
            sub_list.loc[sub_list['participant_id']==sub, 'scan_age'] = scan_age

            

            '''check if they have completed all registration phases'''
            #check if extract_brain has been completed
            if os.path.exists(f'{out_dir}/{sub}/{ses}/rois/brain/rh_brain.nii.gz'):
                
                sub_list.loc[sub_list['participant_id']==sub, 'extract_brain'] = '1'
            else:
                sub_list.loc[sub_list['participant_id']==sub, 'extract_brain'] = ''

            #check if phase 1 files exist
            if os.path.exists(f'{out_dir}/{sub}/{ses}/surf/lh.white'):
                
                sub_list.loc[sub_list['participant_id']==sub, 'phase_1'] = '1'
            else:
                sub_list.loc[sub_list['participant_id']==sub, 'phase_1'] = ''

            #check if phase 3 files exist
            #*note phase 3 is not used anymore
            if os.path.exists(f'{out_dir}/{sub}/{ses}/SUMA/std.141.{sub}_both.spec'):
                
                sub_list.loc[sub_list['participant_id']==sub, 'phase_3'] = '1'
            else:
                sub_list.loc[sub_list['participant_id']==sub, 'phase_3'] = ''

            #check if phase 4 files exist
            if os.path.exists(f'{out_dir}/{sub}/{ses}/func/{sub}_{ses}_{func_suf}_1vol_reg.nii.gz'):
                
                sub_list.loc[sub_list['participant_id']==sub, 'phase_4'] = '1'
            else:
                sub_list.loc[sub_list['participant_id']==sub, 'phase_4'] = ''


            '''check if atlas registration has been completed'''

            curr_atlas = atlas_info.atlas_name.replace('hemi', 'lh')
            #check if atlas files exist
            if os.path.exists(f'{out_dir}/{sub}/{ses}/atlas/{curr_atlas}_anat.nii.gz'):
                
                sub_list.loc[sub_list['participant_id']==sub, f'{atlas}_reg'] = '1'
            else:
                sub_list.loc[sub_list['participant_id']==sub, f'{atlas}_reg'] = ''

            #check if atlas has been split
            if os.path.exists(f'{out_dir}/{sub}/{ses}/atlas/{curr_atlas}_epi.nii.gz'):
                
                sub_list.loc[sub_list['participant_id']==sub, f'{atlas}_split'] = '1'
            else:
                sub_list.loc[sub_list['participant_id']==sub, f'{atlas}_split'] = ''

            #check if timeseries have been extracted
            if os.path.exists(f'{out_dir}/{sub}/{ses}/derivatives/timeseries/{sub}_{ses}_{atlas}_lh_ts.npy'):
                
                sub_list.loc[sub_list['participant_id']==sub, f'{atlas}_ts'] = '1'
            else:
                sub_list.loc[sub_list['participant_id']==sub, f'{atlas}_ts'] = ''

            #add to final_sub_list
            final_sub_list = pd.concat([final_sub_list, sub_list], ignore_index=True)
    
    
        
#remove duplicate rows
final_sub_list = final_sub_list.drop_duplicates()

#save new list
final_sub_list.to_csv(f'{git_dir}/participants_dhcp_new.csv', index=False)

#print total number of subjects
print(f'Total usable of participants: {len(final_sub_list)}')