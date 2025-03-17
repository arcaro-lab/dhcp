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
atlas = 'wang'
group_info = dhcp_params.load_group_params(group)

sub_list = group_info.sub_list
#limit to subs with 1 in to_run col
sub_list = sub_list[sub_list['to_run']==1]
#only grab subs with two sessions
sub_list = sub_list[sub_list.duplicated(subset = 'participant_id', keep = False)]
#reset index
sub_list.reset_index(drop=True, inplace=True)

script_dir = git_dir + '/run_probtrackx'

n_jobs = 5
job_time = 150 #amount of time in minutes to run job

n = 0 #track number of jobs run
for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
    print(sub, ses)

    #run job
    bash_cmd = f'python {git_dir}/diffusion/run_probtrackx.py {sub} {ses} {group} {atlas} &'
    print(bash_cmd)
    subprocess.run(bash_cmd, shell=True)

    n += 1

    if n == n_jobs:
        #wait for jobs to finish
        print('waiting for jobs to finish')
        time.sleep(job_time*60)
        



