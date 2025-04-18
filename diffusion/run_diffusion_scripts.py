'''
Script to run multiple diffusion jobs
'''


project_name = 'dhcp'
import os
#get current working directory
cwd = os.getcwd()
git_dir = cwd.split(project_name)[0] + project_name
import sys

#add git_dir to path
sys.path.append(git_dir)

import subprocess
import numpy as np
import pandas as pd
from glob import glob as glob
import dhcp_params
import pdb
#add wait
import time


group = 'infant'
seed = 'pulvinar'
target = 'wang'
group_info = dhcp_params.load_group_params(group)

sub_list = group_info.sub_list
#limit to subs with 1 in to_run col
sub_list = sub_list[sub_list['to_run']==1]
#only grab subs with two sessions
sub_list = sub_list[sub_list.duplicated(subset = 'participant_id', keep = False)]


#of those grab only the subs with the atlas_probtrackx col set to '' and atlas_dwi col set to 1
sub_list = sub_list[(sub_list[f'{target}_dwi'] == 1)]
#reset index
sub_list.reset_index(drop=True, inplace=True)

'''
sub_list = ['chon', 'droy','gcap','jmcg','jmei','ksei',
            'lsut','marc','mjon',
            'msco','rili','rmru','sget','smcm','wkoo']
'''

script_name = 'probtrackx_roi_to_atlas.py'

n_jobs = 50 #number of jobs to run at once
job_time = 200 #amount of time in minutes to run job

n = 0 #track number of jobs run
for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
#for sub in sub_list:
    print(sub)

    #run job
    bash_cmd = f'python {git_dir}/diffusion/{script_name} --sub {sub} --ses {ses} --group {group} --seed {seed} --target {target} &'
    #bash_cmd = f'python {git_dir}/diffusion/{script_name} --sub {sub} --group {group} --seed {seed} --target {target} &'
    print(bash_cmd)
    subprocess.run(bash_cmd, shell=True)

    n += 1

    if n == n_jobs:
        #load sub_list
        #wait for jobs to finish
        time.sleep(job_time*60)
        print('waiting for jobs to finish')
        full_sub_list = pd.read_csv(f'{git_dir}/participants_dhcp.csv')

        
        #loop through all subs and check whether ifnal file exists
        for check_sub, check_ses in zip(full_sub_list['participant_id'], full_sub_list['ses']):
            check_file = f'{group_info.out_dir}/{check_sub}/{check_ses}/derivatives/dwi_seeds/{seed}_seeds_to_rh_SPL1_40wk.nii.gz'
            if os.path.exists(check_file):
                #set atlas_probtrackx col to 1
                full_sub_list.loc[(full_sub_list['participant_id'] == check_sub) & (full_sub_list['ses'] == check_ses), f'{seed}_to_{target}_probtrackx'] = 1
            else:
                #set atlas_probtrackx col to ''
                full_sub_list.loc[(full_sub_list['participant_id'] == check_sub) & (full_sub_list['ses'] == check_ses), f'{seed}_to_{target}_probtrackx'] = ''
        
        #save full_sub_list
        full_sub_list.to_csv(f'{git_dir}/participants_dhcp.csv', index = False)
        
        
        
        #