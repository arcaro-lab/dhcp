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


group= 'infant'
group_params = params.load_group_params(group)
#load individual infant data

os.makedirs(f'{group_params.out_dir}/derivatives/{atlas}', exist_ok=True)

#infant_fc = infant_fc[0:30,:,:]

sub_info = group_params.sub_list
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
adult_fc = pd.read_csv(f'{params.results_dir}/group_fc/adult_{atlas}_median_{summary_type}.csv', header = None).values

#set diagonal to nan
np.fill_diagonal(adult_fc, np.nan)

#convert to pandas dataframe and melt
adult_df = pd.DataFrame(adult_fc, index = all_rois, columns = all_rois)


#melt so that you have an roi1 and roi1 column
adult_df = adult_df.melt(var_name = 'roi2', value_name = 'fc', ignore_index = False).reset_index().rename(columns = {'index':'roi1'})
adult_df = adult_df.dropna()

#add network labels
adult_df['network1'] = [all_networks[all_rois.index(roi)] for roi in adult_df['roi1']]
adult_df['network2'] = [all_networks[all_rois.index(roi)] for roi in adult_df['roi2']]

if summary_type == 'fc':
    #split roi into hemi and roi
    adult_df['hemi1'] = adult_df['roi1'].apply(lambda x: x.split('_')[0])
    adult_df['roi1'] = adult_df['roi1'].apply(lambda x: x.split('_')[1])

    adult_df['hemi2'] = adult_df['roi2'].apply(lambda x: x.split('_')[0])
    adult_df['roi2'] = adult_df['roi2'].apply(lambda x: x.split('_')[1])





'''Compare all ROIs between infants and adults'''

summary_df = pd.DataFrame(columns = ['sub', 'ses','sex','birth_age', 'scan_age', 'hemi', 'infant_roi','infant_network','adult_roi','adult_network', 'hemi_similarity', 'roi_similarity','network_similarity','corr' ])
all_sub_df = pd.DataFrame(columns = ['sub', 'ses','sex','birth_age', 'scan_age', 'hemi1', 'roi1','network1','hemi2','roi2','network2', 'hemi_similarity', 'roi_similarity','network_similarity','fc' ])
n=1
for sub,ses in zip(sub_info['participant_id'], sub_info['ses']):
    print(sub, n , f'of {len(sub_info)}')
    n +=1
    

    sex = sub_info.loc[(sub_info['participant_id'] == sub) & (sub_info['ses'] == ses), 'sex'].values[0]
    birth_age = sub_info.loc[(sub_info['participant_id'] == sub) & (sub_info['ses'] == ses), 'birth_age'].values[0]
    scan_age = sub_info.loc[(sub_info['participant_id'] == sub) & (sub_info['ses'] == ses), 'scan_age'].values[0]
    
    #set sub directory
    sub_dir = f'{group_params.out_dir}/{sub}/{ses}'

    #make correlation_dir 
    os.makedirs(f'{sub_dir}/derivatives/infant_adult_correlations', exist_ok=True)
    


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

        #load individual sub-adult correlation
        sub_df = pd.read_csv(f'{sub_dir}/derivatives/{sub}_adult_{atlas}_correlations.csv')
        summary_df = pd.concat([summary_df, sub_df])
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
    
    try: 
            
        sub_df = pd.DataFrame(columns=summary_df.columns)
        for infant_hemi in ['lh','rh']:
            #loop through rois and calculate correlation
            for infant_roi, infant_network in zip(roi_labels['label'], roi_labels['network']):
                infant_data = curr_df[(curr_df['roi1'] == infant_roi) & + (curr_df['hemi1'] == infant_hemi)]
                for adult_hemi in ['lh','rh']:
                    for adult_roi, adult_network in zip(roi_labels['label'], roi_labels['network']):
                        adult_data = adult_df[(adult_df['roi1'] == adult_roi) & (adult_df['hemi1'] == adult_hemi)]
                        

                        #calculate correlation
                        corr = np.corrcoef(infant_data['fc'], adult_data['fc'])[0,1]

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
    

summary_df.to_csv(f'{group_params.out_dir}/derivatives/{atlas}/infant_adult_{atlas}_similarity.csv', index = False)
all_sub_df.to_csv(f'{group_params.out_dir}/derivatives/{atlas}/infant_{atlas}_roi_similarity.csv', index = False)

