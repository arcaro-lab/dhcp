'''
Incorporate DTI files from dhcp raw to dhcp_preproc
'''


project_name = 'dhcp'
import os
#get current working directory
cwd = os.getcwd()
git_dir = cwd.split(project_name)[0] + project_name
import sys

#add git_dir to path

sys.path.append(git_dir)

from glob import glob as glob
import shutil
import dhcp_params as params
import pdb
import natsort

group_params = params.load_group_params('infant')

#set up directories
#dhcp_raw = f'{group_params.raw_data_dir}/dhcp_dmri_eddy_pipeline'
dhcp_raw = '/mnt/DataDrive1_backup/DataDrive1/data_raw/human_mri/dhcp_raw/dhcp_dmri_eddy_pipeline'
dhcp_preproc = f'{group_params.out_dir}'

target_folders = ['dtifit', 'dwi_bedpostx.bedpostX', 'xfm', 'dwi/nodif.nii.gz', 'dwi/nodif_brain_mask.nii.gz', 'dwi/nodif_brain.nii.gz', 'dwi/nodif_all.nii.gz']
target_folders = ['dwi/nodif.nii.gz', 'dwi/nodif_brain_mask.nii.gz', 'dwi/nodif_brain.nii.gz', 'dwi/nodif_all.nii.gz']


#glob all subject directories in dhcp_raw
subject_dirs = glob(f'{dhcp_raw}/sub-*/ses-*')

#sort subject directories
subject_dirs = natsort.natsorted(subject_dirs)

for sub_dir in subject_dirs:
    sub = sub_dir.split('/')[-2]
    ses = sub_dir.split('/')[-1]
    
    #loop through target folders and copy to dhcp_preproc
    for target_folder in target_folders:
        source_dir = f'{sub_dir}/{target_folder}'
        dest_dir = f'{dhcp_preproc}/{sub}/{ses}/{target_folder}'

        #

        #check if target folder exists
        if os.path.exists(dest_dir):
            print(f'{dest_dir} already exists')

            #if target_folder ends in .nii.gz, delete it
            if target_folder.endswith('.nii.gz'):
                try:
                    shutil.rmtree(dest_dir)
                    print(f'Deleted {dest_dir}')
                except:
                    #remove file
                    os.remove(dest_dir)
                    print(f'Removed {dest_dir}')
            

            
    
        print(f'{dest_dir} does not exist')

        #if target_folder ends in .nii.gz, create parent folder for file
        if target_folder.endswith('.nii.gz'):
            
            #create parent folder
            os.makedirs(os.path.dirname(dest_dir), exist_ok=True)
            print(f'Created {os.path.dirname(dest_dir)}')

            shutil.copy(source_dir, dest_dir)
            print(f'Copied {source_dir} to {dest_dir}')
        else:
            #create target folder
            os.makedirs(dest_dir, exist_ok=True)
            print(f'Created {dest_dir}')

            shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
            print(f'Copied {source_dir} to {dest_dir}')
            

        
