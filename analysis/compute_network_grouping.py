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
from scipy import stats
import statsmodels.api as sm

from sklearn.manifold import MDS
#run repeated measures ANOVA
import pingouin as pg
import pdb

import warnings
warnings.filterwarnings("ignore")

group = sys.argv[1]
atlas = 'wang'
suf = ''

age_bins = [26,33, 38,42,46]
age_groups = ['pre','early','term','post']
group_names = ['Pre-Term','Early-Term','Term','Post-Term']
networks = ['Occipital', 'Ventral', 'Lateral', 'Dorsal']

#load atlast name and roi labels
atlas_info = params.load_atlas_info(atlas)
group_params = params.load_group_params(group)

sub_list = group_params.sub_list
#only keep if atlas_ts == 1 and atlas_exclude == ''
sub_list = sub_list[(sub_list[f'{atlas}_ts'] == 1) & (sub_list[f'{atlas}_exclude'] != 1)]

roi_labels = atlas_info.roi_labels

#expand roi labels to include hemis
all_rois = []
all_networks = []


all_rois = []
all_networks = []
for roi in roi_labels['label']:
    for hemi in params.hemis:
        all_rois.append(f'{hemi}_{roi}')
        all_networks.append(roi_labels[roi_labels['label'] == roi]['network'].values[0])

#load group data
group_df = pd.read_csv(f'{group_params.out_dir}/derivatives/{atlas}/{group}_{atlas}_roi_similarity.csv')

if group == 'infant':
    suf = '_test'
    #add age and age group columns
    group_df['age'] = (group_df['scan_age'] - group_df['birth_age'])*7
    group_df['age_group'] = np.nan
    for i in range(len(age_bins)-1):
        group_df.loc[(group_df['scan_age'] >= age_bins[i]) & (group_df['scan_age'] < age_bins[i+1]), 'age_group'] = age_groups[i]

    #extract only term and post term infants scanned within a day of birth
    #group_df = group_df[(group_df['age'] <= 1) & (group_df['age_group'] == 'term') | (group_df['age'] <= 1) & (group_df['age_group'] == 'post')]


def create_mat(df,col = 'fc'):
    #create empty matrix to store infant data
    mat = np.zeros((len(all_rois), len(all_rois)))

    #fill in infant matrix with infant data
    for i, roi1 in enumerate(all_rois):
        for j, roi2 in enumerate(all_rois):
            if roi1 == roi2:
                mat[i,j] = 1
            else:
                mat[i,j] = df[(df['roi1'] == roi1) & (df['roi2'] == roi2)][col].values[0]
                #print(roi1, roi2, df[(df['roi1'] == roi1) & (df['roi2'] == roi2)][col].values[0])

    return mat



#average by hemi sub and roi
#group_df = sub_df.groupby(['sub', 'ses',  'roi1', 'roi2']).mean(numeric_only=True).reset_index()


#combine hemi and roi into one column


group_df['roi1'] = group_df['hemi1'] + '_' + group_df['roi1']
group_df['roi2'] = group_df['hemi2'] + '_' + group_df['roi2']



#pivot so that sub and roi1 are indices and roi2 is columns
#group_df = group_df.pivot_table(index = ['sub', 'ses', 'roi1'], columns = 'roi2', values = 'fc').reset_index()

#mds_results = mds.fit(fc_mat).embedding_


subn = 0
for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
    print(sub,subn, len(sub_list))
    mds = MDS(n_components = 2, dissimilarity = 'euclidean')
   
        
    

    #extract sub_df
    sub_df = group_df[(group_df['sub'] == sub) & (group_df['ses'] == ses)]

    

    #extract fc matrix from sub_df
    fc_mat = create_mat(sub_df, col = 'fc')

    #set diagonal to 1
    #np.fill_diagonal(fc_mat, 1)
    
    #extract birth_age, scan_age, age_group for sub
    birth_age = group_df[(group_df['sub'] == sub) & (group_df['ses'] == ses)]['birth_age'].values[0]
    scan_age = group_df[(group_df['sub'] == sub) & (group_df['ses'] == ses)]['scan_age'].values[0]
    age_group = group_df[(group_df['sub'] == sub) & (group_df['ses'] == ses)]['age_group'].values[0]
    


    mds_results = mds.fit(fc_mat).embedding_
    
    #add roi and network to mds_results
    mds_results = pd.DataFrame(mds_results, columns = ['x', 'y'])
    mds_results['roi1'] = all_rois
    #add network from roi_labels
    mds_results['network1'] = all_networks

    #compute euclidean distance between each roi and all other rois
    #roi_dist = pd.DataFrame(columns= ['network1','roi1','network2', 'roi2', 'dist'])
    curr_summary = pd.DataFrame(columns= ['sub','ses','birth_age','scan_age','age_group','network1','hemi1','roi1','network2', 'hemi2','roi2', 'hemi_similarity','network_similarity', 'roi_similarity', 'dist'])
    for i, roi1 in enumerate(all_rois):
        hemi1 = roi1.split('_')[0]
        roi_name1 = roi1.split('_')[1]
        network1 = all_networks[all_rois.index(roi1)]
        for j, roi2 in enumerate(all_rois):
            #compute distance and then concat
            dist = np.sqrt((mds_results['x'][i] - mds_results['x'][j])**2 + (mds_results['y'][i] - mds_results['y'][j])**2)
           
            hemi2 = roi2.split('_')[0]           
            roi_name2 = roi2.split('_')[1]
            network2 = all_networks[all_rois.index(roi2)]
            

            roi_similarity = 'same' if roi_name1 == roi_name2 else 'diff'
            network_similarity = 'same' if network1 == network2 else 'diff'
            hemi_similarity = 'same' if hemi1 == hemi2 else 'diff'

            #concat to dist_summary
            curr_summary =  pd.concat([curr_summary, pd.DataFrame([[sub,ses,birth_age, scan_age,age_group, network1, hemi1, roi_name1, network2, hemi2, roi_name2,hemi_similarity, network_similarity, roi_similarity, dist]], columns = ['sub','ses','birth_age','scan_age','age_group','network1','hemi1','roi1','network2', 'hemi2','roi2', 'hemi_similarity','network_similarity', 'roi_similarity', 'dist'])], ignore_index=True)

            

    if subn != 0:
        #load dist_summary
        dist_summary = pd.read_csv(f'{git_dir}/results/clustering/{group}{suf}_{atlas}_roi_distance.csv')
    else: 
        dist_summary = pd.DataFrame(columns= ['sub','ses','birth_age','scan_age','age_group','network1','hemi1','roi1','network2', 'hemi2','roi2', 'hemi_similarity','network_similarity', 'roi_similarity', 'dist'])

    #concat to dist_summary
    dist_summary = pd.concat([dist_summary, curr_summary], ignore_index=True)
            
    #print(subn, len(group_df['sub'].unique()))
    #plot_mds(fc_mat,  roi_labels['label'], roi_labels['network'])
    #plot_mds(fc_mat,  all_rois, all_networks)


    #save
    dist_summary.to_csv(f'{git_dir}/results/clustering/{group}{suf}_{atlas}_roi_distance.csv', index = False)
    
    #delete mds_results
    del dist_summary
    del mds_results
    del fc_mat
    subn += 1
    
