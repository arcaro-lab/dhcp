'''
Phase 1 of registration pipeline: Creates relevant directories and converts giftis to surf
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

#take subjectand session as command line argument
sub = sys.argv[1]
ses = sys.argv[2]
group = sys.argv[3]

group_info = dhcp_params.load_group_params(group)



#create sub directories
os.makedirs(f'{group_info.out_dir}/{sub}/{ses}/anat', exist_ok=True)
os.makedirs(f'{group_info.out_dir}/{sub}/{ses}/func', exist_ok=True)
os.makedirs(f'{group_info.out_dir}/{sub}/{ses}/surf', exist_ok=True)
os.makedirs(f'{group_info.out_dir}/{sub}/{ses}/xfm', exist_ok=True)

#set sub dir
input_dir = f'{group_info.raw_anat_dir}/{sub}/{ses}'
out_dir = f'{group_info.out_dir}/{sub}/{ses}'

hemi_labels = ['left', 'right']


for lrn,lr in enumerate(['lh','rh']):
    #convert curv files to surf
    print(f'Converting {sub} {ses} {lr} curv and sulc to txt')
    bash_cmd = f'wb_command -gifti-convert ASCII {input_dir}/anat/{sub}_{ses}_hemi-{hemi_labels[lrn]}_curv.shape.gii {out_dir}/surf/{lr}.curv'
    subprocess.run(bash_cmd.split(), check = True)

    #convert sulc 
    print(f'Converting {sub} {ses} {lr} curv and sulc to txt')
    bash_cmd = f'wb_command -gifti-convert ASCII {input_dir}/anat/{sub}_{ses}_hemi-{hemi_labels[lrn]}_sulc.shape.gii {out_dir}/surf/{lr}.sulc'
    subprocess.run(bash_cmd.split(), check = True)

    #convert curv to txt
    print(f'Converting {sub} {ses} {lr} curv to txt')
    bash_cmd = f'wb_command -gifti-convert ASCII {input_dir}/anat/{sub}_{ses}_hemi-{hemi_labels[lrn]}_curv.shape.gii {out_dir}/surf/{lr}_curv.txt'
    subprocess.run(bash_cmd.split(), check = True)

    #convert sulc to txt
    print(f'Converting {sub} {ses} {lr} sulc to txt')
    bash_cmd = f'wb_command -gifti-convert ASCII {input_dir}/anat/{sub}_{ses}_hemi-{hemi_labels[lrn]}_sulc.shape.gii {out_dir}/surf/{lr}_sulc.txt'
    subprocess.run(bash_cmd.split(), check = True)
    

    #convert pial
    print(f'Converting {sub} {ses} {lr} pial  to surf')
    bash_cmd = f'mris_convert {input_dir}/anat/{sub}_{ses}_hemi-{hemi_labels[lrn]}_pial.surf.gii {out_dir}/surf/{lr}.pial'
    subprocess.run(bash_cmd.split(), check = True)

    #convert white matter
    print(f'Converting {sub} {ses} {lr}  white matter to surf')
    bash_cmd = f'mris_convert {input_dir}/anat/{sub}_{ses}_hemi-{hemi_labels[lrn]}_wm.surf.gii {out_dir}/surf/{lr}.white'
    subprocess.run(bash_cmd.split(), check = True)





