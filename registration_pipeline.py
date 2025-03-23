'''
This analysis conducts necessary preprocesing steps in prep for analysis including:

Computing reigstration between individual anat to fsaverage via afni and freesurfer
Registering atlases to the individual
Extracting timeseries data from each roi of an atlast
'''



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

group = 'adult'
group_info = params.load_group_params(group)

#set directories
raw_data_dir = group_info.raw_data_dir

raw_anat_dir = group_info.raw_anat_dir
raw_func_dir = group_info.raw_func_dir
out_dir = group_info.out_dir


#set suffixes for anat and func files
anat_suf = group_info.anat_suf
func_suf = group_info.func_suf



#directory with preprocessing scripts
script_dir = f'{git_dir}/fmri'

#participants_file = 'participants_dhcp'

#load subject list
full_sub_list = group_info.sub_list

#limit to subs with 1 in to_run col
sub_list = full_sub_list[full_sub_list['to_run']==1]
#only grab subs with two sessions
#sub_list = sub_list[sub_list.duplicated(subset = 'participant_id', keep = False)]
#reset index
#sub_list.reset_index(drop=True, inplace=True)

#limit to first 30 subjects
#sub_list = full_sub_list.head(200)


#set atlas
atlas = 'wang'

roi = 'pulvinar'

'''
Flags to determine which preprocessing steps to run
'''
#finds eligible subjects based on having all scans
find_eligible_subs = False

#extract brain
extract_brain = False

#Reg-phase1-3 : Register individual anat to fsaverage
reg_phase1 = False
reg_phase2 = False
reg_phase3 = False

#Registers atlas to individual anat
register_atlas = False
#split atlas into individual rois
split_atlas = True

#extracts mean timeseries from each roi of atlas
extract_ts_roi = True

#Register volumetric roi to individual anat
register_vol_roi = False

#extract voxel-wise timeseries from rois
extract_ts_voxel = False

#reg atlas rois to dwi
reg_atlas2dwi = False

#run_probtrackx
run_probtrackx = False




def launch_script(sub_list,script_name, analysis_name,pre_req='', atlas = ''):
    '''
    Launches preprocessing script and checks for errors
    '''
    
    
    #create new column if analysis_name doesn't exist
    if analysis_name not in sub_list.columns:
        sub_list[analysis_name] = ''
        full_sub_list[analysis_name] = ''

    #check if script has already been run and whether pre-reqs have been met
    curr_subs = sub_list[sub_list[analysis_name]!=1]

    #if pre-reqs is not None, check if pre-reqs have been met
    if pre_req != '':
        curr_subs = curr_subs[curr_subs[pre_req]==1]
    
    n = 1
    for sub, ses in zip(curr_subs['participant_id'], curr_subs['ses']):
        print(f'Running {analysis_name} for {sub}', f'{n} of {len(curr_subs)}' )
        n += 1

        try:
            #run script
            bash_cmd = f'python {script_dir}/{script_name} {sub} {ses} {group} {atlas}'
            subprocess.run(bash_cmd, check=True, shell=True)
            

            
            #set analysis_name to 1
            sub_list.loc[(sub_list['participant_id']==sub) & (sub_list['ses'] == ses), analysis_name] = 1

            #update the full_sub_list for this participant and ses
            full_sub_list.loc[(full_sub_list['participant_id']==sub) & (full_sub_list['ses'] == ses), analysis_name] = 1
            
            #reset index
            full_sub_list.reset_index(drop=True, inplace=True)
            full_sub_list.to_csv(f'{group_info.sub_file}', index=False)
            
        except Exception as e:
            #open log file
            log_file = open(f'{script_dir}/qc/preproc_log.txt', 'a')
            #write error to log file
            log_file.write(f'{time.strftime("%d/%m/%Y %H:%M:%S:")} Error in {script_name} for {sub}: {e}\n')
            log_file.close()



#time it 
start = time.time()


if find_eligible_subs:
    '''
    Pre-registration phase: Check which subjects have all scans

    Create new participant list with eligible subjects
    '''
    find_eligble_subs()


if extract_brain:
    '''
    Extract brain
    '''
    launch_script(sub_list = sub_list,script_name='extract_brain.py',analysis_name=f'extract_brain')
            
if reg_phase1:
    '''
    Phase 1: Converts GIFTI files to surf
    '''
    
    launch_script(sub_list = sub_list,script_name='phase1_registration.py',analysis_name='phase_1',pre_req='extract_brain')


if reg_phase2:
    '''
    Phase 3 of registration pipeline: Creates final surfaces and registers to fsaverage
    '''
    launch_script(sub_list = sub_list,script_name='phase2_registration.py',analysis_name='phase_2',pre_req='phase_1')

if reg_phase3:
    '''
    Phase 4 of registration pipeline: Registers anat to EPI
    '''
    launch_script(sub_list = sub_list,script_name='phase3_registration.py',analysis_name='phase_3',pre_req='phase_2')

if register_atlas:
    '''
    Register atlas to individual anat
    '''
    launch_script(sub_list = sub_list,script_name='register_atlas.py',analysis_name=f'{atlas}_reg',pre_req='phase_3', atlas = atlas)

if split_atlas:
    '''
    Split atlas into individual rois
    '''
    launch_script(sub_list = sub_list,script_name='split_atlas.py',analysis_name=f'{atlas}_split',pre_req=f'{atlas}_reg', atlas = atlas)

if extract_ts_roi:
    '''
    Extract mean timeseries from each roi of atlas
    '''
    launch_script(sub_list = sub_list,script_name='extract_ts_roi.py',analysis_name=f'{atlas}_ts',pre_req=f'{atlas}_split', atlas = atlas)



if register_vol_roi:
    '''
    Register volumetric roi to individual anat
    '''
    launch_script(sub_list = sub_list,script_name='register_vol_roi.py',analysis_name=f'{roi}_reg',pre_req=f'extract_brain', atlas = roi)

if extract_ts_voxel:
    '''
    Extract voxel-wise timeseries from all voxels of an roi

    *note: this is a very time and memory intensive if you have many ROIs
    '''
    launch_script(sub_list = sub_list,script_name='extract_ts_voxel.py',analysis_name=f'{roi}_ts',pre_req=f'{roi}_reg', atlas = roi)


if reg_atlas2dwi:
    '''
    Register atlas rois to dwi
    '''
    launch_script(sub_list = sub_list,script_name='reg_atlas2dwi.py',analysis_name=f'{atlas}_dwi',pre_req=f'{atlas}_split', atlas = atlas)

if run_probtrackx:
    '''
    Run probtrackx on all rois of the atlas
    '''
    launch_script(sub_list = sub_list,script_name='run_probtrackx.py',analysis_name=f'{atlas}_probtrackx',pre_req=f'{atlas}_dwi', atlas = atlas)

#end time
end = time.time()
print(f'Total time: {(end-start)/60}')