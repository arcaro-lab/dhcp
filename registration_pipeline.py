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
import time

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

    #add columns for phase 1-4 as empty
    sub_list['phase_1'] = ''
    sub_list['phase_2'] = ''
    sub_list['phase_3'] = ''
    sub_list['phase_4'] = ''

    #save new list
    sub_list.to_csv(f'{out_dir}/participants.csv', index=False)

    #print total number of subjects
    print(f'Total usable of participants: {len(sub_list)}')

#find_eligble_subs()

#load subject list
full_sub_list = pd.read_csv(f'{out_dir}/participants.csv')
sub_list = full_sub_list.head(30)


run_phase1 = False
run_phase2 = False
run_phase3 = False
run_phase4 = True
register_rois = False



#time it 
start = time.time()

if run_phase1:
    '''
    Phase 1: Convert GIFTI files to surf
    '''
    #extract subject list where phase 1 has not been run
    sub_list = sub_list[sub_list['phase_1']!=1]
    
    for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
        print(f'Running phase 1 registration for {sub}')
        try:
            bash_cmd = f'python {git_dir}/registration/phase1_registration.py {sub} {ses}'
            subprocess.run(bash_cmd, check=True, shell=True)

            #set phase 1 to 1
            sub_list.loc[sub_list['participant_id']==sub, 'phase_1'] = 1
            

        except:
            #open log file
            log_file = open(f'{git_dir}/registration/qc/registration_log.txt', 'a')
            #write error to log file
            log_file.write(f'Error in phase1_registration.py for {sub} {ses}\n')
            #close log file
            log_file.close()

    #add updated sub list to full sub list
    full_sub_list.update(sub_list)
    
    #save updated subject list
    full_sub_list.to_csv(f'{out_dir}/participants.csv', index=False)


if run_phase2:
    '''
    Phase 2: Write curv and sulc data to txt in matlab

    Note: subject loop and error logging is done in matlab script
    '''
    print('Running phase 2 registration')
    bash_cmd = "matlab.exe -batch \"run('registration/phase2_registration.m')\""
    subprocess.run(bash_cmd, check=True, shell=True)

    #load updated sub list
    #this needs to be reloaded because matlab script updates it
    full_sub_list = pd.read_csv(f'{out_dir}/participants.csv')

    

if run_phase3:
    '''
    Phase 3 of registration pipeline: Creates final surfaces and registers to fsaverage
    '''
    #extract subject list where phase 2 has been run but phase 3 has not
    sub_list = full_sub_list[(full_sub_list['phase_2']==1)& (full_sub_list['phase_3']!=1)]

    for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
        print(f'Running phase 3 registration for {sub}')
        try:

            bash_cmd = f'python {git_dir}/registration/phase3_registration.py {sub} {ses}'
            subprocess.run(bash_cmd, check=True, shell=True)
            
            #set phase 3 to 1
            sub_list.loc[sub_list['participant_id']==sub, 'phase_3'] = 1
        except:
            #open log file
            log_file = open(f'{git_dir}/registration/qc/registration_log.txt', 'a')
            #write error to log file
            log_file.write(f'Error in phase3_registration.py for {sub}\n')
            #close log file
            log_file.close()

    #add updated sub list to full sub list
    full_sub_list.update(sub_list)

    #save updated subject list
    full_sub_list.to_csv(f'{out_dir}/participants.csv', index=False)



if run_phase4:
    '''
    Phase 4 of registration pipeline: Registers anat to EPI
    '''
    #extract subject list where phase 3 has been run but phase 4 has not
    sub_list = full_sub_list[(full_sub_list['phase_3']==1)& (full_sub_list['phase_4']!=1)]

    for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
        print(f'Running phase 4 registration for {sub}')

        try:
            bash_cmd = f'python {git_dir}/registration/phase4_registration.py {sub} {ses}'
            subprocess.run(bash_cmd, check=True, shell=True)

            #set phase 4 to 1
            sub_list.loc[sub_list['participant_id']==sub, 'phase_4'] = 1
        except:
            #open log file
            log_file = open(f'{git_dir}/registration/qc/registration_log.txt', 'a')
            #write error to log file
            log_file.write(f'Error in phase4_registration.py for {sub}\n')
            #close log file
            log_file.close()

    #add updated sub list to full sub list
    full_sub_list.update(sub_list)

    #save updated subject list
    full_sub_list.to_csv(f'{out_dir}/participants.csv', index=False)


if register_rois:
    '''
    Register ROIs to anat and EPI
    '''

    atlas = 'wang'
    
    #create new column for the atlas registration if it doesn't already exist
    if f'{atlas}_reg' not in full_sub_list.columns:
        full_sub_list[f'{atlas}_reg'] = ''
    

    #extract subject list where phase 4 has been run but roi_reg has not
    sub_list = full_sub_list[(full_sub_list['phase_4']==1)& (full_sub_list[f'{atlas}_reg']!=1)]
    

    for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
        print(f'Running ROI registration for {sub}')

        try:
            bash_cmd = f'python {git_dir}/registration/register_rois.py {sub} {ses} {atlas}'
            subprocess.run(bash_cmd, check=True, shell=True)

            #set roi_reg to 1
            sub_list.loc[sub_list['participant_id']==sub, f'{atlas}_reg'] = 1
        except:
            #open log file
            log_file = open(f'{git_dir}/registration/qc/registration_log.txt', 'a')
            #write error to log file
            log_file.write(f'Error in register_rois.py for {sub}\n')
            #close log file
            log_file.close()



    #add updated sub list to full sub list
    full_sub_list.update(sub_list)

    #save updated subject list
    full_sub_list.to_csv(f'{out_dir}/participants.csv', index=False)


#end time
end = time.time()
print(f'Total time: {(end-start)/60}')