'''
This analysis conducts necessary preprocesing steps in prep for analysis including:

Computing reigstration between individual anat to fsaverage via afni and freesurfer
Registering atlases to the individual
Extracting timeseries data from each roi of an atlast
'''



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

#print date and time
print(time.strftime("%d/%m/%Y %H:%M:%S"))

#set directories
raw_data_dir = params.raw_data_dir

raw_anat_dir = params.raw_anat_dir
raw_func_dir = params.raw_func_dir
out_dir = params.out_dir


#set suffixes for anat and func files
anat_suf = params.anat_suf
func_suf = params.func_suf



#directory with preprocessing scripts
script_dir = f'{git_dir}/fmri'

#load subject list
full_sub_list = pd.read_csv(f'{out_dir}/participants.csv')
#limit to first 30 subjects
sub_list = full_sub_list.head(2)


#set atlas
atlas = 'calcsulc'
roi = 'pulvinar'

'''
Flags to determine which preprocessing steps to run
'''
#finds eligible subjects based on having all scans
find_eligible_subs = False

#Reg-phase1-4 : Register individual anat to fsaverage
reg_phase1 = False
reg_phase2 = False
reg_phase3 = False
reg_phase4 = False

#Registers atlas to individual anat
register_rois = False
#split atlas into individual rois
split_rois = False

#extracts timeseries from each roi
extract_ts = False

#extract brain
extract_brain = True

#Registrer volumetric roi to individual anat
register_vol_roi = True

def find_eligble_subs():

    '''
    Pre-registration phase: Check which subjects have all scans

    Create new participant list with eligible subjects
    '''
    raw_sub_list = pd.read_csv(f'{raw_func_dir}/participants.tsv', sep='\t')
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

    for sub, ses in zip(curr_subs['participant_id'], curr_subs['ses']):
        print(f'Running {analysis_name} for {sub}')

        try:
            #run script
            bash_cmd = f'python {script_dir}/{script_name} {sub} {ses} {atlas}'
            subprocess.run(bash_cmd, check=True, shell=True)

            #set analysis_name to 1
            sub_list.loc[sub_list['participant_id']==sub, analysis_name] = 1

            #update the full_sub_list and save it
            #note: full_sub_list is kept outside of the function so its not overwritten
            full_sub_list.update(sub_list)
            full_sub_list.to_csv(f'{out_dir}/participants.csv', index=False)
            
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
            
if reg_phase1:
    '''
    Phase 1: Converts GIFTI files to surf
    '''
    
    launch_script(sub_list = sub_list,script_name='phase1_registration.py',analysis_name='phase_1')

if reg_phase2:
    '''
    Phase 2: Write curv and sulc data to txt in matlab

    Note: subject loop and error logging is done in matlab script
    '''
    print('Running phase 2 registration')
    bash_cmd = "matlab.exe -batch \"run('fmri/phase2_registration.m')\""
    subprocess.run(bash_cmd, check=True, shell=True)

    #load updated sub list
    #this needs to be reloaded because matlab script updates it
    full_sub_list = pd.read_csv(f'{out_dir}/participants.csv')
    #
    full_sub_list[full_sub_list == 'NaN'] = ''
    #save updated sub list
    full_sub_list.to_csv(f'{out_dir}/participants.csv', index=False)



if reg_phase3:
    '''
    Phase 3 of registration pipeline: Creates final surfaces and registers to fsaverage
    '''
    launch_script(sub_list = sub_list,script_name='phase3_registration.py',analysis_name='phase_3',pre_req='phase_2')

if reg_phase4:
    '''
    Phase 4 of registration pipeline: Creates final surfaces and registers to fsaverage
    '''
    launch_script(sub_list = sub_list,script_name='phase4_registration.py',analysis_name='phase_4',pre_req='phase_3')

if register_rois:
    '''
    Register atlas to individual anat
    '''
    launch_script(sub_list = sub_list,script_name='register_atlas.py',analysis_name=f'{atlas}_reg',pre_req='phase_4', atlas = atlas)

if split_rois:
    '''
    Split atlas into individual rois
    '''
    launch_script(sub_list = sub_list,script_name='split_atlas.py',analysis_name=f'{atlas}_split',pre_req=f'{atlas}_reg', atlas = atlas)

if extract_ts:
    '''
    Extract time series from atlas
    '''
    launch_script(sub_list = sub_list,script_name='extract_ts.py',analysis_name=f'{atlas}_ts',pre_req=f'{atlas}_split', atlas = atlas)


if extract_brain:
    '''
    Extract brain
    *this is mainly needed for volumetric ROI registration
    '''
    launch_script(sub_list = sub_list,script_name='extract_brain.py',analysis_name=f'extract_brain',pre_req=f'phase_4')


if register_vol_roi:
    '''
    Register volumetric roi to individual anat
    '''
    launch_script(sub_list = sub_list,script_name='register_vol_roi.py',analysis_name=f'{roi}_reg',pre_req=f'extract_brain', atlas = roi)

#end time
end = time.time()
print(f'Total time: {(end-start)/60}')