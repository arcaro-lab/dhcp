import os
import sys
import shutil
from glob import glob as glob
import natsort
import pdb


data_dir = '/mnt/d/3T_HCP'
target_dir = '/mnt/f/7T_HCP'


#unzip anat files
zip_suf = '*1.6mm_preproc.zip'
target_file = 'MNINonLinear/T1w_restore.1.60.nii.gz'


#glob all anat zip files in the data_dir
zip_files = glob(f'{data_dir}/{zip_suf}')

#sort zip files
zip_files = natsort.natsorted(zip_files)

#make target_dir if it doesn't exist
os.makedirs(target_dir, exist_ok=True)

n = 0
#unzip all zip files into target_dir
for zip_file in zip_files:
    print(f'unzipping {n} of {len(zip_files)}')
    n += 1
    sub = os.path.basename(zip_file).split('_')[0]
    #check if file already exists
    
    
    if os.path.exists(f'{target_dir}/{sub}/{target_file}'):
        print(f'{sub} already exists')
        
    else:
        try:
            shutil.unpack_archive(zip_file, target_dir, 'zip')
        except:
            print(f'error unzipping {zip_file}')
            
        
    

#unzip functional files
zip_suf = '*7T_REST_preproc_extended.zip'
target_file = 'MNINonLinear/Results/rfMRI_REST4_7T_AP/rfMRI_REST4_7T_AP.nii.gz'


#glob all anat zip files in the data_dir
zip_files = glob(f'{data_dir}/{zip_suf}')

#sort zip files
zip_files = natsort.natsorted(zip_files)

#make target_dir if it doesn't exist
os.makedirs(target_dir, exist_ok=True)

n = 0
#unzip all zip files into target_dir
for zip_file in zip_files:
    print(f'unzipping {n} of {len(zip_files)}')
    n += 1
    sub = os.path.basename(zip_file).split('_')[0]
    #check if file already exists
    
    if os.path.exists(f'{target_dir}/{sub}/{target_file}'):
        print(f'{sub} already exists')
        
    else:
        try:
            shutil.unpack_archive(zip_file, target_dir, 'zip')
        except:
            print(f'error unzipping {zip_file}')