'''
Calculate second-order-correlation between infants and adults for all rois
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

from sklearn.manifold import MDS
import pdb

import warnings
warnings.filterwarnings("ignore")

atlas = 'wang'

summary_type = 'fc'

#load atlast name and roi labels
atlas_info = params.load_atlas_info(atlas)

roi_labels = atlas_info.roi_labels


infant_params = params.load_group_params('infant')
adult_params = params.load_group_params('adult')
#load individual infant data

os.makedirs(f'{infant_params.out_dir}/derivatives/{atlas}', exist_ok=True)

#infant_fc = infant_fc[0:30,:,:]

sub_info = infant_params.sub_list
sub_info = sub_info[(sub_info[f'{atlas}_ts'] == 1) & (sub_info[f'{atlas}_exclude'] != 1)]

infant_data = pd.read_csv(f'{infant_params.out_dir}/derivatives/{atlas}/infant_{atlas}_roi_similarity.csv')
#sub_info = sub_info.head(30)

age_groups = ['infant', 'adult']

networks = ['Occipital', 'Ventral', 'Lateral', 'Dorsal']

#expand roi labels to include hemis
all_rois = []
all_networks = []

#flag whether to rerun correlations
re_run = False

all_rois = []
all_networks = []
for roi in roi_labels['label']:
    for hemi in params.hemis:
        all_rois.append(f'{hemi}_{roi}')
        all_networks.append(roi_labels[roi_labels['label'] == roi]['network'].values[0])



''' 
Load and organize group adult fc matrix
'''

#load median fc matrix for adults
adult_data = pd.read_csv(f'{adult_params.out_dir}/derivatives/{atlas}/adult_{atlas}_roi_similarity.csv')

adult_df = adult_data.groupby(by=['hemi1', 'network1','roi1', 'hemi2','network2','roi2']).median(numeric_only=True).reset_index()

#sort adult data by hemi2, roi2
adult_df = adult_df.sort_values(by=['hemi2', 'roi2'])


'''Compare all ROIs between infants and adults'''

summary_df = pd.DataFrame(columns = ['sub', 'ses','sex','birth_age', 'scan_age', 'hemi', 'infant_roi','infant_network','adult_roi','adult_network', 'hemi_similarity', 'roi_similarity','network_similarity','corr' ])

n=1
for sub,ses in zip(sub_info['participant_id'], sub_info['ses']):
    print(sub, n , f'of {len(sub_info)}')
    n +=1
    

    sex = sub_info.loc[(sub_info['participant_id'] == sub) & (sub_info['ses'] == ses), 'sex'].values[0]
    birth_age = sub_info.loc[(sub_info['participant_id'] == sub) & (sub_info['ses'] == ses), 'birth_age'].values[0]
    scan_age = sub_info.loc[(sub_info['participant_id'] == sub) & (sub_info['ses'] == ses), 'scan_age'].values[0]
    
    #set sub directory
    sub_dir = f'{infant_params.out_dir}/{sub}/{ses}'

    #make correlation_dir 
    os.makedirs(f'{sub_dir}/derivatives/infant_adult_correlations', exist_ok=True)

    #check if sub and ses exists in infant_data df
    if sub in infant_data['sub'].values and ses in infant_data['ses'].values:
        print(sub, ses, 'exists')
    else:
        print(sub, ses, 'doesnt exist')
        continue

    #extract subject data
    curr_df = infant_data[(infant_data['sub'] == sub) & (infant_data['ses'] == ses)]

    

    #check if final file already exists and you dont want to overwrite it 
    if os.path.isfile(f'{sub_dir}/derivatives/{sub}_adult_{atlas}_correlations.csv') and os.path.isfile(f'{sub_dir}/derivatives/fc_matrix/{sub}_{atlas}_correlations.csv') and re_run == False:
        print(sub, ses, 'exists')
        #load indvidiaul sub fc file
        #curr_df = pd.read_csv(f'{sub_dir}/derivatives/fc_matrix/{sub}_{atlas}_correlations.csv')
        #all_sub_df = pd.concat([all_sub_df,curr_df])

        #load individual sub-adult correlation
        sub_df = pd.read_csv(f'{sub_dir}/derivatives/{sub}_adult_{atlas}_correlations.csv')
        summary_df = pd.concat([summary_df, sub_df])
        continue

    
    #add sex,birth_age, scan_age
    curr_df['sub'] = sub
    curr_df['ses'] = ses
    curr_df['sex'] = sex
    curr_df['birth_age'] = birth_age
    curr_df['scan_age'] = scan_age
    
    
    try: 
            
        sub_df = pd.DataFrame(columns=summary_df.columns)
        for infant_hemi in ['lh','rh']:
            #loop through rois and calculate correlation
            for infant_roi, infant_network in zip(roi_labels['label'], roi_labels['network']):
                
                for adult_hemi in ['lh','rh']:
                    for adult_roi, adult_network in zip(roi_labels['label'], roi_labels['network']):
                        #get infant roi data
                        infant_roi_df = curr_df[(curr_df['roi1'] == infant_roi) & + (curr_df['hemi1'] == infant_hemi)]

                        #sort by hemi2 and roi2
                        infant_roi_df = infant_roi_df.sort_values(by=['hemi2', 'roi2'])


                        adult_roi_df = adult_df[(adult_df['roi1'] == adult_roi) & (adult_df['hemi1'] == adult_hemi)]
                        

                        #check if order of rois is the same
                        rois_to_include = infant_roi_df['roi2'].values == adult_roi_df['roi2'].values
                        
                        infant_roi_df = infant_roi_df[rois_to_include]
                        adult_roi_df = adult_roi_df[rois_to_include]
                        

                        #calculate correlation
                        corr = np.corrcoef(infant_roi_df['fc'], adult_roi_df['fc'])[0,1]

                        if infant_roi == adult_roi:
                            roi_sim = 'same'
                        else:
                            roi_sim = 'diff'

                        if infant_network == adult_network:
                            net_sim = 'same'
                        else:
                            net_sim = 'diff'

                        if infant_hemi == adult_hemi:
                            hemi_sim = 'same'
                        else:
                            hemi_sim = 'diff'

                        
                        #add to sub_df
                        curr_data = [sub, ses, sex, birth_age, scan_age, hemi, infant_roi, infant_network, adult_roi, adult_network,hemi_sim, roi_sim, net_sim, corr]
                        
                        sub_df.loc[len(sub_df)] = curr_data

        #save sub_df
        sub_df.to_csv(f'{sub_dir}/derivatives/{sub}_adult_{atlas}_correlations.csv', index=False)
        
        #add to summary_df
        summary_df = pd.concat([summary_df, sub_df])
    except:
        print('error', sub, ses)
    

summary_df.to_csv(f'{infant_params.out_dir}/derivatives/{atlas}/infant_adult_{atlas}_correlations.csv', index = False)


