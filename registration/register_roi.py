'''
Register atlas to subject
'''

it_dir = '/mnt/c/Users/ArcaroLab/Desktop/git_repos/dhcp'

import os
import sys
#add git_dir to path
sys.path.append(git_dir)

import subprocess
import numpy as np
import pandas as pd
from glob import glob as glob
import dhcp_params as params
import pdb

#take subjectand session as command line argument
sub = sys.argv[1]
ses = sys.argv[2]
hemi = sys.argv[3]
atlas = sys.argv[4]

#set sub dir
anat_input = f'{params.raw_anat_dir}/{sub}/{ses}'
func_input = f'{params.raw_func_dir}/{sub}/{ses}'
out_dir = f'{params.out_dir}/{sub}/{ses}'
atlas_dir = params.atlas_dir


#register atlas to subject with afni
bash_cmd = f"""3dSurf2Vol \\
-spec {out_dir}/SUMA/std.141.{sub}_{hemi}.spec \\
-surf_A std.141.{hemi}.white.asc \\
-surf_B std.141.{hemi}.pial.asc \\
-sv {anat_input}/anat/${sub}_${ses}_desc-restore_T2w.nii.gz \\
-grid_parent {func_input}/func/{sub}_{ses}_task-rest_desc-preproc_bold_1vol_reg.nii.gz \\
-sdata {atlas_dir}/{atlas}.1D.dset \\
-map_func mode \\
-f_steps 500 \\
-f_p1_mm -0.5 \\
-f_pn_mm 0.5 \\
-prefix {atlas}/{atlas}_epi"""

subprocess.run(bash_cmd.split(), check = True)

