'''
Create infant and adult similarity files
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
import matplotlib.pyplot as plt
import seaborn as sns
import dhcp_params as params


import pdb

import warnings
import argparse

warnings.filterwarnings("ignore")

atlas = 'wang'

summary_type = 'fc'


#read atlas and group info as args

#group = sys.argv[1]

#atlas = sys.argv[2]
group = 'infant'
atlas = 'wang'

#load atlast name and roi labels
atlas_info = params.load_atlas_info(atlas)

roi_labels = atlas_info.roi_labels


group_params = params.load_group_params(group)
#load individual infant data
sub_info = group_params.sub_list

#remove rows where atlas_exclude is 1
sub_info = sub_info[(sub_info[f'{atlas}_ts'] == 1) & (sub_info[f'{atlas}_exclude'] != 1)]

results_dir = f'{group_params.out_dir}/derivatives/{atlas}'
os.makedirs(f'{group_params.out_dir}/derivatives/{atlas}', exist_ok=True)

networks = roi_labels['network'].unique()

#expand roi labels to include hemis
all_rois = []
all_networks = []

#flag whether to rerun correlations
re_run = True


'''
Create a list of all ROIs and networks for both hemis

The difference between infants and adults is that infant data was organized alternating hemi (lh_V1, rh_V1)

Adult data was organized by ROI then hemi (lhV1, lhV2 ... rhV1, rhV2)

'''
'''
if group == 'infant':
    all_rois = []
    all_networks = []
    for roi in roi_labels['label']:
        for hemi in params.hemis:
            all_rois.append(f'{hemi}_{roi}')
            all_networks.append(roi_labels[roi_labels['label'] == roi]['network'].values[0])
'''

all_rois = []
all_networks = []
for hemi in params.hemis:
    for roi in roi_labels['label']:
        all_rois.append(f'{hemi}_{roi}')
        all_networks.append(roi_labels[roi_labels['label'] == roi]['network'].values[0])


all_sub_df = pd.DataFrame(columns = ['sub', 'ses','sex','birth_age', 'scan_age', 'hemi1', 'roi1','network1','hemi2','roi2','network2', 'hemi_similarity', 'roi_similarity','network_similarity','fc' ])
n=1
for sub,ses in zip(sub_info['participant_id'], sub_info['ses']):
    print(sub, n , f'of {len(sub_info)}')
    #sub = 'sub-CC01025XX11'
    #ses = 'ses-50230'
    n +=1
    
    sex = sub_info.loc[(sub_info['participant_id'] == sub) & (sub_info['ses'] == ses), 'sex'].values[0]

    if group == 'infant':
    
        birth_age = sub_info.loc[(sub_info['participant_id'] == sub) & (sub_info['ses'] == ses), 'birth_age'].values[0]
        scan_age = sub_info.loc[(sub_info['participant_id'] == sub) & (sub_info['ses'] == ses), 'scan_age'].values[0]

    elif group == 'adult':
        #get age
        birth_age = sub_info.loc[(sub_info['participant_id'] == sub) & (sub_info['ses'] == ses), 'age'].values[0]
        scan_age = birth_age


    
    #set sub directory
    sub_dir = f'{group_params.out_dir}/{sub}/{ses}'

   

    #check if file exists; skip if not
    if not os.path.isfile(f'{sub_dir}//derivatives/fc_matrix/{sub}_{ses}_{atlas}_fc.npy'):
        print(sub, ses, 'doesnt exist')
        continue

    #check if final file already exists and you dont want to overwrite it 
    if os.path.isfile(f'{sub_dir}/derivatives/{sub}_adult_{atlas}_correlations.csv') and os.path.isfile(f'{sub_dir}/derivatives/fc_matrix/{sub}_{atlas}_correlations.csv') and re_run == False:
        print(sub, ses, 'exists')
        #load indvidiaul sub fc file
        curr_df = pd.read_csv(f'{sub_dir}/derivatives/fc_matrix/{sub}_{atlas}_correlations.csv')
        all_sub_df = pd.concat([all_sub_df,curr_df])

        continue

    
    curr_fc = np.load(f'{sub_dir}//derivatives/fc_matrix/{sub}_{ses}_{atlas}_fc.npy')
    
    np.fill_diagonal(curr_fc, np.nan)
    

    #melt so that you have an roi1 and roi1 column
    curr_df = pd.DataFrame(curr_fc, index = all_rois, columns = all_rois)
    curr_df = curr_df.melt(var_name = 'roi2', value_name = 'fc', ignore_index = False).reset_index().rename(columns = {'index':'roi1'})
    curr_df = curr_df.dropna()
    
    #add network labels
    curr_df['network1'] = [all_networks[all_rois.index(roi)] for roi in curr_df['roi1']]
    curr_df['network2'] = [all_networks[all_rois.index(roi)] for roi in curr_df['roi2']]
    
    #split roi1 
    curr_df[['hemi1','roi1']] = curr_df['roi1'].str.split('_',expand = True)
    curr_df[['hemi2','roi2']] = curr_df['roi2'].str.split('_',expand = True)
    

   
    #make similarity columns 
    curr_df['hemi_similarity'] = curr_df.apply(lambda x: 'same' if x['hemi1'] == x['hemi2'] else 'diff', axis=1)
    curr_df['roi_similarity'] = curr_df.apply(lambda x: 'same' if x['roi1'] == x['roi2'] else 'diff', axis=1)
    curr_df['network_similarity'] = curr_df.apply(lambda x: 'same' if x['network1'] == x['network2'] else 'diff', axis=1)

    #add sex,birth_age, scan_age
    curr_df['sub'] = sub
    curr_df['ses'] = ses
    curr_df['sex'] = sex
    curr_df['birth_age'] = birth_age
    curr_df['scan_age'] = scan_age
    

    #save curr_df 
    curr_df.to_csv(f'{sub_dir}/derivatives/fc_matrix/{sub}_{atlas}_correlations.csv')
    #add to all_sub_df
    all_sub_df = pd.concat([all_sub_df,curr_df])





all_sub_df.to_csv(f'{results_dir}/{group}_{atlas}_roi_similarity.csv', index = False)