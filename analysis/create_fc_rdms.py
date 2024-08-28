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

atlas = 'wang'


#load atlast name and roi labels
atlas_info = params.load_atlas_info(atlas)
roi_labels = atlas_info.roi_labels


age_groups= ['infant', 'adult']
age_groups= ['infant']

extract_group = True
extract_by_age = False

extract_indiv = True
extract_cross_hemi = False
extract_within_hemi = False


#age_groups = ['adult']

def create_indiv_rdm(group, sub_list, data_dir, atlas,suffix = ''):
    
    atlas_info = params.load_atlas_info(atlas)
    roi_labels = atlas_info.roi_labels

    #Create fc matrix for each subject
    

    all_subs = []
    #for each subject looop through wang labels and load timeseries
    for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
        all_ts = []

        
        #check if file exists
        #if not, skip
        if os.path.exists(f'{data_dir}/{sub}/{ses}/derivatives/timeseries/{sub}_{ses}_{atlas}_lh_ts.npy'):

            for hemi in params.hemis:
                #load timeseries
                #this is all ROIs for a given hemisphere

                #check if file exists
                
                ts = np.load(f'{data_dir}/{sub}/{ses}/derivatives/timeseries/{sub}_{ses}_{atlas}_{hemi}_ts.npy')

                
                #if ts is longer than params.vols, truncate
                #this is to equalize the number of volumes across groups
                if ts.shape[0] > group_info.vols:
                    ts = ts[:group_info.vols,:]

                #append to all_ts
                all_ts.append(ts)
                
            
            #intersperse hemis so it goes lh->rh->lh->rh for each rois
            full_ts = np.zeros((all_ts[0].shape[1] * 2, all_ts[0].shape[0]))
            full_ts[0::2] = all_ts[0].T
            full_ts[1::2] = all_ts[1].T
        

            #compute correlation matrix across all rois
            corr_mat = np.corrcoef(full_ts)

            all_subs.append(corr_mat)

            #save
            np.save(f'{data_dir}/{sub}/{ses}/derivatives/fc_matrix/{sub}_{ses}_{atlas}_fc.npy', corr_mat)

        #else:
        #    print(f'{sub} does not have timeseries file')

    #convert to numpy array
    all_subs = np.array(all_subs)

    

    np.save(f'{data_dir}/derivatives/fc_matrix/{group}_{atlas}_fc{suffix}.npy', all_subs)
    
    

    return all_subs





def compute_cross_hemi_rdm(group, sub_list, data_dir, atlas, suffix = ''):

    ''' 
    create assymmetric RDM by correlating timeseries from one hemisphere with the other hemisphere
    '''
    atlas_info = params.load_atlas_info(atlas)
    roi_labels = atlas_info.roi_labels
    

    all_rdms = []
    #for each subject looop through wang labels and load timeseries
    for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
        if os.path.exists(f'{data_dir}/{sub}/{ses}/derivatives/timeseries/{sub}_{ses}_{atlas}_lh_ts.npy'):
            #create empty RDM size of number of rois
            rdm = np.zeros((len(roi_labels), len(roi_labels)))
            
        
            #load timeseries
            #this is all ROIs for a given hemisphere
            lh_ts = np.load(f'{data_dir}/{sub}/{ses}/derivatives/timeseries/{sub}_{ses}_{atlas}_lh_ts.npy')
            rh_ts = np.load(f'{data_dir}/{sub}/{ses}/derivatives/timeseries/{sub}_{ses}_{atlas}_rh_ts.npy')

            
            #if ts is longer than params.vols, truncate
            if lh_ts.shape[0] > params.vols:
                lh_ts = lh_ts[:params.vols,:]
                rh_ts = rh_ts[:params.vols,:]

            #correlate each roi in lh with each roi in rh
            for x, ts1 in enumerate(lh_ts.T):
                for y, ts2 in enumerate(rh_ts.T):
                    
                    r = np.corrcoef(ts1,ts2)[0,1]
                    rdm[x,y] = r

    
                    #append to all_ts
            all_rdms.append(rdm)

            #save 
            np.save(f'{data_dir}/derivatives/fc_matrix/{sub}_{atlas}_cross_hemi_fc.npy', rdm)

    #convert to numpy array
    all_rdms = np.array(all_rdms)
    #save all subs
    np.save(f'{data_dir}/derivatives/fc_matrix/{group}_{atlas}_cross_hemi_fc.npy{suffix}', all_rdms)

    
    return all_rdms
            

def compute_within_hemi_rdm(group, sub_list, data_dir, atlas, suffix = ''):

    ''' 
    create symmetric RDM by correlating timeseries only within hemisphere
    '''
    atlas_info = params.load_atlas_info(atlas)
    roi_labels = atlas_info.roi_labels
    

    all_rdms = []
    all_lh_rdms = []
    all_rh_rdms = []
    #for each subject looop through wang labels and load timeseries
    for sub, ses in zip(sub_list['participant_id'], sub_list['ses']):
        if os.path.exists(f'{data_dir}/{sub}/{ses}/derivatives/timeseries/{sub}_{ses}_{atlas}_lh_ts.npy'):
            #create empty RDM size of number of rois
            rdm = np.zeros((len(roi_labels), len(roi_labels)))
            lh_rdm = rdm
            rh_rdm = rdm
            
        
            #load timeseries
            #this is all ROIs for a given hemisphere
            lh_ts = np.load(f'{data_dir}/{sub}/{ses}/derivatives/timeseries/{sub}_{ses}_{atlas}_lh_ts.npy')
            rh_ts = np.load(f'{data_dir}/{sub}/{ses}/derivatives/timeseries/{sub}_{ses}_{atlas}_rh_ts.npy')

            
            #if ts is longer than params.vols, truncate
            if lh_ts.shape[0] > params.vols:
                lh_ts = lh_ts[:params.vols,:]
                rh_ts = rh_ts[:params.vols,:]

            
            #correlate each roi in lh with each roi in rh
            for (x, lh_ts1), (_, rh_ts1) in zip(enumerate(lh_ts.T), enumerate(rh_ts.T)):
                
                for (y, lh_ts2), (_,rh_ts2) in zip(enumerate(lh_ts.T), enumerate(rh_ts.T)):
                    
                    lh_r = np.corrcoef(lh_ts1,lh_ts2)[0,1]
                    rh_r = np.corrcoef(rh_ts1,rh_ts2)[0,1]
                    rdm[x,y] = np.mean([lh_r, rh_r]).round(4)

                    lh_rdm[x,y] = lh_r
                    rh_rdm[x,y] = rh_r

            
            
            #append to all_ts
            all_rdms.append(rdm)
            all_lh_rdms.append(lh_rdm)
            all_rh_rdms.append(rh_rdm)

            #save 
            #np.save(f'{data_dir}/derivatives/fc_matrix/{sub}_{atlas}_within_hemi_fc.npy', rdm)

    #convert to numpy array
    all_rdms = np.array(all_rdms)
    all_lh_rdms = np.array(all_lh_rdms)
    all_rh_rdms = np.array(all_rh_rdms)



    #save all subs
    np.save(f'{data_dir}/derivatives/fc_matrix/{group}_{atlas}_within_hemi_fc{suffix}.npy', all_rdms)

    np.save(f'{data_dir}/derivatives/fc_matrix/{group}_{atlas}_lh_within_hemi_fc{suffix}.npy', all_lh_rdms)
    np.save(f'{data_dir}/derivatives/fc_matrix/{group}_{atlas}_rh_within_hemi_fc{suffix}.npy', all_rh_rdms)

    
    return all_rdms

if extract_group == True:
    print('Extracting group RDMs...')
    #create indiv rdm for each subject
    for group in age_groups:
        #extract group data
        group_info = params.load_group_params(group)

        #load subject list
        sub_list= group_info.sub_list
        sub_list = sub_list[sub_list[f'{atlas}_ts'] == 1]

        #sort by participant_id
        sub_list = sub_list.sort_values(by = 'participant_id')
        #select top 100
        #sub_list = sub_list.head(100)

        suf = ''
        
        

        if extract_indiv == True:
            print(f'Extracting individual {group} RDMs...', len(sub_list)) 
            #create indiv rdm
            all_rdms = create_indiv_rdm(group, sub_list, group_info.out_dir, atlas)
            out_dir = group_info.out_dir

            #compute median rdm
            median_fc = np.median(all_rdms, axis = 0)

            
            #save median rdm to results dir as csv
            median_fc = pd.DataFrame(median_fc)
            median_fc.to_csv(f'{params.results_dir}/group_fc/{group}_{atlas}_median_fc{suf}.csv', header = False, index = False)
        

        if extract_cross_hemi == True:
            print(f'Extracting cross-hemi {group} RDMs ...')
            #compute cross hemi rdm
            cross_hemi_rdms = compute_cross_hemi_rdm(group, sub_list, out_dir, atlas)

            #compute median cross hemi rdm
            median_cross_hemi_fc = np.median(cross_hemi_rdms, axis = 0)

            #save median rdm to results dir as csv
            median_cross_hemi_fc = pd.DataFrame(median_cross_hemi_fc)
            median_cross_hemi_fc.to_csv(f'{params.results_dir}/group_fc/{group}_{atlas}_median_cross_hemi_fc{suf}.csv', header = False, index = False)

        if extract_within_hemi == True:
            
            print(f'Extracting within-hemi {group} RDMs ...')
            #compute within hemi rdm
            within_hemi_rdms = compute_within_hemi_rdm(group, sub_list, group_info.out_dir, atlas)

            #compute median within hemi rdm
            median_within_hemi_fc = np.median(within_hemi_rdms, axis = 0)

            #save median rdm to results dir as csv
            median_within_hemi_fc = pd.DataFrame(median_within_hemi_fc)
            median_within_hemi_fc.to_csv(f'{params.results_dir}/group_fc/{group}_{atlas}_median_within_hemi_fc{suf}.csv', header = False, index = False)

