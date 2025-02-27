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
dhcp_raw = f'{group_params.raw_data_dir}/dhcp_dmri_eddy_pipeline'
dhcp_preproc = f'{group_params.out_dir}'

target_folders = ['dtifit', 'dwi_bedpostx.bedpostX', 'xfm', 'dwi/nodif.nii.gz', 'dwi/nodif_brain_mask.nii.gz', 'dwi/nodif_brain.nii.gz', 'dwi/nodif_all.nii.gz']


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

        #if target folder exists, delte it

        #os.makedirs(dest, exist_ok=True)
        try:
            #copy source to dest
            shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
            print(f'Copied {source_dir} to {dest_dir}')

        except:
            #copy file
            try:
                shutil.copy(source_dir, dest_dir, dirs_exist_ok=True)
                print(f'Copied {source_dir} to {dest_dir}')

            except:
                print(f'Failed to move {source_dir} to {dest_dir}')
            

        
