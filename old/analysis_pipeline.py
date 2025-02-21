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

anat_suf = 'desc-restore_T2w'
func_suf = 'task-rest_desc-preproc_bold'

#load subject list
full_sub_list = pd.read_csv(f'{out_dir}/participants.csv')
sub_list = full_sub_list.head(30)

atlas = 'wang'
atlas_name, roi_labels = params.load_roi_info(atlas)

'''
Flags on what analysis steps to run
'''

compute_fc = True


#time it 
start = time.time()

if compute_fc:
    '''
    Compute functional connectivity between each roi pair
    '''
    #create new column for the fc_analysis if it doesn't already exist
    if f'{atlas}_fc' not in full_sub_list.columns:
        full_sub_list[f'{atlas}_fc'] = ''

    #extract subject list where roi_reg has been run but roi_split has not
    sub_list = full_sub_list[(full_sub_list[f'{atlas}_split']==1)& (full_sub_list[f'{atlas}_fc']!=1)]
    
    for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
        print(f'Computing FC for {sub} on {atlas}')
        try:
            bash_cmd = f'python {git_dir}/analysis/compute_fc.py {sub} {ses} {atlas}'
            subprocess.run(bash_cmd, check=True, shell=True)

            #set phase 1 to 1
            sub_list.loc[sub_list['participant_id']==sub,f'{atlas}_fc'] = 1

        except:
            #open log file
            log_file = open(f'{git_dir}/analysis/analysis_log.txt', 'a')
            #write error to log file
            log_file.write(f'Error in compute_fc.py for {sub}\n')
            #close log file
            log_file.close()

