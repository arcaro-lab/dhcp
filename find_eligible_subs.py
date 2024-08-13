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




'''
Pre-registration phase: Check which subjects have all scans

Create new participant list with eligible subjects
'''
raw_sub_list = pd.read_csv(f'{git_dir}/participants_dhcp_full.csv')
sub_list = pd.DataFrame(columns=raw_sub_list.columns)

for sub in raw_sub_list['participant_id']:
    
    #load sessions file
    ses_file = pd.read_csv(f'{raw_anat_dir}/{sub}/{sub}_sessions.tsv', sep='\t')
    sess = ses_file['session_id'].values
    pdb.set_trace()
    for ses in sess:
        #check if subject has all scans
        anat_files = glob(f'{raw_anat_dir}/{sub}/ses-{ses}/anat/*{anat_suf}.nii.gz')
        func_files = glob(f'{raw_func_dir}/{sub}/ses-{ses}/func/*{func_suf}.nii.gz')



        
        #if subject has all scans, add to new list
        if len(anat_files) > 0 and len(func_files) > 0:
            #add subject and ses to new final_sub_list
            sub_list = pd.concat([sub_list, raw_sub_list[raw_sub_list['participant_id']==sub]], ignore_index=True)
            sub_list.loc[sub_list['participant_id']==sub, 'ses'] = ses


    #check if subject has all scans
    anat_files = glob(f'{raw_anat_dir}/{sub}/*/anat/*{anat_suf}.nii.gz')
    func_files = glob(f'{raw_func_dir}/{sub}/*/func/*{func_suf}.nii.gz')



    
    #if subject has all scans, add to new list
    if len(anat_files) > 0 and len(func_files) > 0:
        #add subject and ses to new final_sub_list
        sub_list = pd.concat([sub_list, raw_sub_list[raw_sub_list['participant_id']==sub]], ignore_index=True)
        sub_list.loc[sub_list['participant_id']==sub, 'ses'] = ses

        
    
#append sub- to participant_id
sub_list['participant_id'] = 'sub-' + sub_list['participant_id']

#add columns for phase 1-4 as empty
sub_list['phase_1'] = ''
sub_list['phase_2'] = ''
sub_list['phase_3'] = ''
sub_list['phase_4'] = ''

#save new list
sub_list.to_csv(f'{out_dir}/{group_info.participants_file}.csv', index=False)

#print total number of subjects
print(f'Total usable of participants: {len(sub_list)}')