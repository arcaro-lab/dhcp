'''
compute noise cieling
'''

git_dir = '/mnt/c/Users/ArcaroLab/Desktop/git_repos/dhcp'

import os
import sys
#add git_dir to path
sys.path.append(git_dir)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import dhcp_params as params

import pdb


def compute_noise_ceiling(all_mats):

    '''
    Compute the noise ceiling by using leave one out cross validation
    
    '''
    #create list of indices with length of number of subjects
    sub_idx = np.arange(all_mats.shape[0])

    #create empty list to store noise ceiling values
    noise_ceiling = []

    #loop through indices and remove one subject at a time
    #calcualte median rdm for remaining subjects
    #compute correlation between median rdm and removed subject
    for idx in sub_idx:
        #remove subject
        sub_removed = np.delete(all_mats, idx, axis = 0)

        #compute median rdm
        median_rdm = np.median(sub_removed, axis = 0)

        #extract upper triangle of median rdm
        median_rdm = np.triu(median_rdm, k = 1)

        #extract upper triangle of removed subject
        curr_sub = np.triu(all_mats[idx], k = 1)

        #compute correlation between median rdm and removed subject
        r = np.corrcoef(median_rdm, curr_sub[idx])[0,1]

        #append to noise_ceiling
        noise_ceiling.append(r)

    return noise_ceiling