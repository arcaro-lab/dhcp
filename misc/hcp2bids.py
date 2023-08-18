'''
Converts HCP to BIDS
'''
git_dir = '/mnt/c/Users/ArcaroLab/Desktop/git_repos/dhcp'
import os
import sys
import shutil

from glob import glob as glob
import pdb
import pandas as pd

#glob all subs in raw_anat_dir
sub_list = glob('/mnt/f/7T_HCP/sub-*')

#Extract just subs from sub_list
sub_list = [sub.split('/')[-1] for sub in sub_list]


ses = '01'

#create participants.csv
sub_info = pd.DataFrame(columns = ['participant_id', 'ses', 'age','sex','phase_1', 'phase_2', 'phase_3', 'phase_4'])


for sub in sub_list:
     #if sub contains sub- remove it
    if 'sub-' in sub:
        sub = sub.replace('sub-', '')

    #check if sub has already has anat and func in right place
    if os.path.exists(f'/mnt/f/7T_HCP/sub-{sub}/ses-{ses}/anat/sub-{sub}_ses-{ses}_restore-1.60_T1w.nii.gz') and os.path.exists(f'/mnt/f/7T_HCP/sub-{sub}/ses-{ses}/func/sub-{sub}_ses-{ses}_task-rest_run-01_preproc_bold.nii.gz'):
        print(f'{sub} already has anat and func files')
        #check if sub has already been added to sub_info
        if sub in sub_info['participant_id'].values:
            print(f'{sub} already in sub_info')
            
        else:
            #append sub to sub_info
            sub_info = pd.concat([sub_info, pd.DataFrame({'participant_id': f'sub-{sub}', 'ses': f'sub-{ses}'}, index=[0])], ignore_index=True)
            
        
        continue
        #if it does, continue
        
    print(f'Converting {sub} to BIDS')

    


    sub_dir = f'/mnt/f/7T_HCP/sub-{sub}'

    #create ses dir
    os.makedirs(f'{sub_dir}/ses-01', exist_ok=True)

    #move files to ses dir
    for file in glob(f'{sub_dir}/*'):
        #check if file is already in ses-01
        if 'ses-01' not in file:
            shutil.move(file, f'{sub_dir}/ses-{ses}')

    sub_dir = f'{sub_dir}/ses-01'


    #setup target files and out files
    target_dir = f'{sub_dir}/MNINonLinear'
    target_files = [f'T1w_restore.1.60.nii.gz', f'T2w_restore.1.60.nii.gz', 
                    f'fsaverage_LR59k/{sub}.hemi*.curvature.59k_fs_LR.shape.gii', f'fsaverage_LR59k/{sub}.hemi*.sulc.59k_fs_LR.shape.gii',
                    f'fsaverage_LR59k/{sub}.hemi*.pial_1.6mm_MSMAll.59k_fs_LR.surf.gii', f'fsaverage_LR59k/{sub}.hemi*.white_1.6mm_MSMAll.59k_fs_LR.surf.gii',
                    f'Results/rfMRI_REST1_7T_PA/rfMRI_REST1_7T_PA.nii.gz', f'Results/rfMRI_REST2_7T_AP/rfMRI_REST2_7T_AP.nii.gz',f'Results/rfMRI_REST3_7T_PA/rfMRI_REST3_7T_PA.nii.gz', f'Results/rfMRI_REST4_7T_AP/rfMRI_REST4_7T_AP.nii.gz']

    out_dir =f'{sub_dir}'
    out_files = [f'anat/sub-{sub}_ses-{ses}_restore-1.60_T1w.nii.gz', f'anat/sub-{sub}_ses-{ses}_restore-1.60_T2w.nii.gz',
                    f'anat/sub-{sub}_ses-{ses}_hemi-hemi*_curv.shape.gii', f'anat/sub-{sub}_ses-{ses}_hemi-hemi*_sulc.shape.gii',
                    f'anat/sub-{sub}_ses-{ses}_hemi-hemi*_pial.surf.gii', f'anat/sub-{sub}_ses-{ses}_hemi-hemi*_wm.surf.gii',
                    f'func/sub-{sub}_ses-{ses}_task-rest_run-01_preproc_bold.nii.gz', f'func/sub-{sub}_ses-{ses}_task-rest_run-02_preproc_bold.nii.gz', f'func/sub-{sub}_ses-{ses}_task-rest_run-03_preproc_bold.nii.gz', f'func/sub-{sub}_ses-{ses}_task-rest_run-04_preproc_bold.nii.gz']
    
    #check if sub has anat and func files
    if not os.path.exists(f'{target_dir}/T1w_restore.1.60.nii.gz'):
        print(f'{sub} missing anat files')
        continue

    if not os.path.exists(f'{target_dir}/Results/rfMRI_REST1_7T_PA/rfMRI_REST1_7T_PA.nii.gz'):
        print(f'{sub} missing func files')
        continue

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

                try:
                    #copy file
                    shutil.copy(f'{target_dir}/{target_file}', f'{out_dir}/{out_file}')
                except:
                    print(f'error copying {target_file}')
        else:
            #rename 
            target_file  = tf.replace('sub*', sub)

            out_file = of.replace('sub*', f'sub-{sub}')

            try:
                #copy file
                shutil.copy(f'{target_dir}/{target_file}', f'{out_dir}/{out_file}')
            except:
                print(f'error copying {target_file}')

    #append sub to sub_info using pd.concat
    sub_info = pd.concat([sub_info, pd.DataFrame({'participant_id': f'sub-{sub}', 'ses': f'sub-{ses}'}, index=[0])], ignore_index=True)
    

    


    #save sub_info
    sub_info.to_csv(f'/mnt/f/7T_HCP/participants_new.csv', index=False)