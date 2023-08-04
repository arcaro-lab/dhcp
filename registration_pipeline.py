git_dir = '/mnt/c/Users/ArcaroLab/Desktop/git_repos/dhcp'

import os
import sys
#add curr_dir to path
sys.path.append(git_dir)

import numpy as np  
import pandas as pd
from glob import glob as glob
import pdb
import dhcp_params as params
import subprocess

#set directories
raw_data_dir = params.raw_data_dir

raw_anat_dir = params.raw_anat_dir
raw_func_dir = params.raw_func_dir
out_dir = params.out_dir

#load subject list for funcs
raw_sub_list = pd.read_csv(f'{raw_func_dir}/participants.tsv', sep='\t')


anat_suf = 'desc-restore_T2w'
func_suf = 'task-rest_desc-preproc_bold'


def find_eligble_subs():

    '''
    Pre-registration phase: Check which subjects have all scans

    Create new participant list with eligible subjects
    '''
    #create new sub list
    sub_list = pd.DataFrame(columns=raw_sub_list.columns.to_list() + ['ses'])

    for sub in raw_sub_list['participant_id']:
        #check if subject has all scans
        anat_files = glob(f'{raw_anat_dir}/sub-{sub}/*/anat/*{anat_suf}.nii.gz')
        func_files = glob(f'{raw_func_dir}/sub-{sub}/*/func/*{func_suf}.nii.gz')

        #determine session number
        ses = glob(f'{raw_anat_dir}/sub-{sub}/ses-*')
        ses = ses[0].split('/')[-1]

        
        #if subject has all scans, add to new list
        if len(anat_files) > 0 and len(func_files) > 0:
            #add subject and ses to new final_sub_list
            sub_list = pd.concat([sub_list, raw_sub_list[raw_sub_list['participant_id']==sub]], ignore_index=True)
            sub_list.loc[sub_list['participant_id']==sub, 'ses'] = ses

            
        
    #append sub- to participant_id
    sub_list['participant_id'] = 'sub-' + sub_list['participant_id']

    #save new list
    sub_list.to_csv(f'{out_dir}/participants.csv', index=False)

    #print total number of subjects
    print(f'Total usable of participants: {len(sub_list)}')


#load subject list
sub_list = pd.read_csv(f'{out_dir}/participants.csv')
sub_list = sub_list.head(1)
run_phase1 = False
run_phase2 = False
run_phase3 = False
run_phase4 = True

if run_phase1:
    '''
    Phase 1: Convert GIFTI files to surf
    '''
    
    for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
        print(f'Running phase 1 registration for {sub}')
        try:
            bash_cmd = f'python {git_dir}/registration/phase1_registration.py {sub} {ses}'
            subprocess.run(bash_cmd, check=True, shell=True)
        except:
            #open log file
            log_file = open(f'{out_dir}/registration_log.txt', 'a')
            #write error to log file
            log_file.write(f'Error in phase1_registration.py for {sub} {ses}')
            #close log file
            log_file.close()


if run_phase2:
    '''
    Phase 2: Write curv and sulc data to txt in matlab

    Note: subject loop and error logging is done in matlab script
    '''
    print('Running phase 2 registration')
    bash_cmd = "matlab.exe -batch \"run('registration/phase2_registration.m')\""
    subprocess.run(bash_cmd, check=True, shell=True)
    

if run_phase3:
    '''
    Phase 3 of registration pipeline: Creates final surfaces and registers to fsaverage
    '''

    for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
        print(f'Running phase 3 registration for {sub}')
        try:

            bash_cmd = f'python {git_dir}/registration/phase3_registration.py {sub} {ses}'
            subprocess.run(bash_cmd, check=True, shell=True)
        except:
            #open log file
            log_file = open(f'{out_dir}/logs/registration_log.txt', 'a')
            #write error to log file
            log_file.write(f'Error in phase3_registration.py for {sub}')
            #close log file
            log_file.close()


if run_phase4:
    '''
    Phase 4 of registration pipeline: Registers anat to EPI
    '''

    for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
        print(f'Running phase 4 registration for {sub}')


        bash_cmd = f'python {git_dir}/registration/phase4_registration.py {sub} {ses}'
        subprocess.run(bash_cmd, check=True, shell=True)
