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

#load atlast name and roi labels
atlas_info = params.load_atlas_info(atlas)
group_params = params.load_group_params(group)

roi_labels = atlas_info.roi_labels

#load group data
group_df = pd.read_csv(f'{group_params.out_dir}/derivatives/{atlas}/{group}_{atlas}_roi_similarity.csv')

network_rois = [['V1v', 'V2v','V3v', ''],['V1d', 'V2d','V3d', ''],['V1v', 'V2v','V3v', 'hV4','VO1','VO2','PHC1','PHC2',''], ['V1d', 'V2d','V3d', 'V3a','V3b','IPS0','IPS1','IPS2','IPS3', 'IPS4', 'IPS5', 'SPL1',''], ['V1d', 'V2d','V3d' ,'LO1','LO2','hMT','MST','']]
networks = ['Occipital_v', 'Occipital_d', 'Ventral', 'Dorsal', 'Lateral']

if group == 'infant':
    suf = '_all'

dist_summary = pd.read_csv(f'{git_dir}/results/clustering/{group}{suf}_{atlas}_roi_distance.csv')


#average by hemi sub and roi
#remove rows where roi_similarity is same
df_roi_summary = dist_summary[dist_summary['roi_similarity'] == 'diff']

#group by roi1 and roi2
hierarchy_summary = pd.DataFrame(columns = ['sub', 'network', 'corr'])

for sub in dist_summary['sub'].unique():
    sub_summary = dist_summary[dist_summary['sub'] == sub]

    sub_summary = sub_summary[sub_summary['roi_similarity'] == 'diff']
    sub_summary = sub_summary.groupby(['network1', 'roi1', 'network2', 'roi2', 'network_similarity']).mean(numeric_only=True).reset_index()

    for network, rois in zip(networks, network_rois):

        #extract only rows where roi1 and roi2 is in rois
        network_df = sub_summary[sub_summary['roi1'].isin(rois)]
        network_df = network_df[network_df['roi2'].isin(rois)]

        #only define if network is not occipital_d
        if network != 'Occipital_d':

            temp_hierarchy_summary = pd.DataFrame(columns = ['network', 'curr_roi1', 'anat_roi2','actual_roi2', 'anat_rank','actual_rank'])

        
        roi_index = []
        tested_rois = []
        for n, roi in enumerate(rois):
            if n == 0:
                curr_roi = roi
            
            curr_df = network_df[network_df['roi1'] == curr_roi]

            tested_rois.append(curr_roi)


            if n !=0:
                #remove tested rois from curr_df
                curr_df = curr_df[~curr_df['roi2'].isin(tested_rois)]
            
            #skip if last roi
            if n == len(rois)-2:
                
                break
        
            #find the next closest roi
            next_roi = curr_df[curr_df['dist'] == np.min(curr_df['dist'])]['roi2'].values[0]

            #this is the roi that should be next
            anat_roi = rois[rois.index(curr_roi)+1]
            anat_rank = rois.index(anat_roi)

            actual_roi = next_roi
            actual_rank = rois.index(next_roi)

            #add to hierarchy_summary
            temp_hierarchy_summary = pd.concat([temp_hierarchy_summary, pd.DataFrame([[network, curr_roi, anat_roi, actual_roi, anat_rank, actual_rank]], columns = ['network', 'curr_roi1', 'anat_roi2','actual_roi2', 'anat_rank','actual_rank'])])

            #add index of next_roi to roi_index
            roi_index.append(rois.index(next_roi))

            #set curr_roi to next_roi
            curr_roi = next_roi
        
        if network == 'Occipital_v':
            continue
        elif network == 'Occipital_d':
            #rename network to occipital
            temp_hierarchy_summary['network'] = 'Occipital'
            network = 'Occipital'

        

        if network != 'Occipital':
            #remove rows with V1v,V2v, V1d, V2d
            temp_hierarchy_summary = temp_hierarchy_summary[~temp_hierarchy_summary['curr_roi1'].isin(['V1v', 'V2v', 'V1d', 'V2d'])]

        
        #compute the rank correlation between anat_rank and actual_rank for this network
        corr = stats.pearsonr(temp_hierarchy_summary['anat_rank'], temp_hierarchy_summary['actual_rank'])[0]

        #add to hierarchy_summary
        hierarchy_summary = pd.concat([hierarchy_summary, pd.DataFrame([[sub, network, corr]], columns = ['sub', 'network', 'corr'])])


#save hierarchy_summary
hierarchy_summary.to_csv(f'{git_dir}/results/clustering/{group}{suf}_{atlas}_roi_hierarchy.csv', index = False)


    