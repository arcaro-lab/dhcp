'''
Converts HCP to BIDS
'''
git_dir = '/mnt/c/Users/ArcaroLab/Desktop/git_repos/dhcp'
import os
import sys
import shutil

import glob
import pdb

sub = sys.argv[1]
ses = '01'

#if sub contains sub- remove it
if 'sub-' in sub:
    sub = sub.replace('sub-', '')

sub_dir = f'/mnt/f/7T_HCP/sub-{sub}'

#create ses dir
os.makedirs(f'{sub_dir}/ses-01', exist_ok=True)

#move files to ses dir
for file in glob.glob(f'{sub_dir}/*'):
    if 'ses-01' not in file:
        shutil.move(file, f'{sub_dir}/ses-{ses}')

sub_dir = f'{sub_dir}/ses-01'

target_dir = f'{sub_dir}/MNINonLinear'
target_files = [f'T1w_restore.1.60.nii.gz', f'T2w_restore.1.60.nii.gz', 
                f'Results/rfMRI_REST1_7T_PA/rfMRI_REST1_7T_PA.nii.gz', f'Results/rfMRI_REST2_7T_AP/rfMRI_REST2_7T_AP.nii.gz',f'Results/rfMRI_REST3_7T_PA/rfMRI_REST3_7T_PA.nii.gz', f'Results/rfMRI_REST4_7T_AP/rfMRI_REST4_7T_AP.nii.gz',
                f'fsaverage_LR59k/{sub}.hemi*.curvature.59k_fs_LR.shape.gii', f'fsaverage_LR59k/{sub}.hemi*.sulc.59k_fs_LR.shape.gii',
                f'fsaverage_LR59k/{sub}.hemi*.pial_1.6mm_MSMAll.59k_fs_LR.surf.gii', f'fsaverage_LR59k/{sub}.hemi*.white_1.6mm_MSMAll.59k_fs_LR.surf.gii']

out_dir =f'{sub_dir}'
out_files = [f'anat/sub-{sub}_ses-{ses}_restore-1.60_T1w.nii.gz', f'anat/sub-{sub}_ses-{ses}_restore-1.60_T2w.nii.gz',
                f'func/sub-{sub}_ses-{ses}_task-rest_run-01_preproc_bold.nii.gz', f'func/sub-{sub}_ses-{ses}_task-rest_run-02_preproc_bold.nii.gz', f'func/sub-{sub}_ses-{ses}_task-rest_run-03_preproc_bold.nii.gz', f'func/sub-{sub}_ses-{ses}_task-rest_run-04_preproc_bold.nii.gz',
                f'anat/sub-{sub}_ses-{ses}_hemi-hemi*_curv.shape.gii', f'anat/sub-{sub}_ses-{ses}_hemi-hemi*_sulc.shape.gii',
                f'anat/sub-{sub}_ses-{ses}_hemi-hemi*_pial.surf.gii', f'anat/sub-{sub}_ses-{ses}_hemi-hemi*_white.surf.gii']

#loop through target files and copy to out_dir
for tf, of in zip(target_files, out_files):
    
    #check if tf contains hemi*
    if 'hemi*' in tf:
        for hemi in zip(['L', 'R'], ['left','right']):
            #rename 
            target_file  = tf.replace('sub*', sub)
            target_file = target_file.replace('hemi*', hemi[0])

            out_file = of.replace('sub*', f'sub-{sub}')
            out_file = out_file.replace('hemi*', hemi[1])

            #copy file
            shutil.copy(f'{target_dir}/{target_file}', f'{out_dir}/{out_file}')
    else:
        #rename 
        target_file  = tf.replace('sub*', sub)

        out_file = of.replace('sub*', f'sub-{sub}')

        #copy file
        shutil.copy(f'{target_dir}/{target_file}', f'{out_dir}/{out_file}')

