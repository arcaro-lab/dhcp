#Convert curv files
wb_command -gifti-convert ASCII sub-CC00087AN14_ses-38800_hemi-R_space-T2w_curv.shape.gii rh_curv.txt
wb_command -gifti-convert ASCII sub-CC00087AN14_ses-38800_hemi-L_space-T2w_curv.shape.gii lh_curv.txt
wb_command -gifti-convert ASCII sub-CC00087AN14_ses-38800_hemi-R_space-T2w_sulc.shape.gii rh_sulc.txt
wb_command -gifti-convert ASCII sub-CC00087AN14_ses-38800_hemi-L_space-T2w_sulc.shape.gii lh_sulc.txt

# Convert gifti files
mris_convert sub-CC00087AN14_ses-38800_hemi-R_space-T2w_wm.surf.gii rh.white
mris_convert sub-CC00087AN14_ses-38800_hemi-R_space-T2w_pial.surf.gii rh.pial
mris_convert sub-CC00087AN14_ses-38800_hemi-L_space-T2w_wm.surf.gii lh.white
mris_convert sub-CC00087AN14_ses-38800_hemi-L_space-T2w_pial.surf.gii lh.pial

# Write curv and sulc files In Matlab:
clear all
rh_curv=gifti('rh_curv.txt');
lh_curv=gifti('lh_curv.txt');
rh_curv.cdata=-rh_curv.cdata;
lh_curv.cdata=-lh_curv.cdata;
write_curv(['rh.curv'],rh_curv.cdata,length(rh_curv.cdata));
write_curv(['lh.curv'],lh_curv.cdata,length(lh_curv.cdata));

rh_sulc=gifti('rh_sulc.txt');
lh_sulc=gifti('lh_sulc.txt');
rh_sulc.cdata=-rh_sulc.cdata;
lh_sulc.cdata=-lh_sulc.cdata;
write_curv(['rh.sulc'],rh_sulc.cdata,length(rh_sulc.cdata));
write_curv(['lh.sulc'],lh_sulc.cdata,length(lh_sulc.cdata));


# maks FS surfaces w/ curv info
# what we used previously # mris_smooth -n 50 -nw -seed 1234 rh.white rh.smoothwm
mris_smooth -n 5 -nw -seed 1234 rh.white rh.smoothwm
mris_inflate -n 2 rh.smoothwm rh.partinflated
mris_curvature -w rh.white
mris_curvature -thresh .999 -n -a 5 -w -distances 10 10 rh.inflated
mris_sphere rh.inflated rh.sphere

#mris_smooth -n 50 -nw -seed 1234 lh.white lh.smoothwm
mris_smooth -n 5 -nw -seed 1234 lh.white lh.smoothwm
mris_inflate -n 2 lh.smoothwm lh.partinflated
mris_curvature -w lh.white
mris_curvature -thresh .999 -n -a 5 -w -distances 10 10 lh.inflated
mris_sphere lh.inflated lh.sphere



# DRAW ROIS
1 calc
2 colat
3 parietal
4 lateral
5 frontal

# Convert .niml.rois to .label
# need allnode label from fs. make with freeview and remove the header!
# add header followed by node count on second line

#!ascii label  , from subject  vox2ras=TkReg


# Register to fsaverage sphere
mris_register -1 -dist 10 -spring 1 -L labels/rh_calc_fs.label ../../../fsaverage/rh.DKTatlas40.gcs pericalcarine -L labels/rh_colat_fs.label ../../../fsaverage/rh.destrieux.simple.2009-07-29.gcs S_oc-temp_med_and_Lingual  -L labels/rh_pariet_fs.label ../../../fsaverage/rh.destrieux.simple.2009-07-29.gcs S_oc_sup_and_transversal -L labels/rh_lat_fs.label ../../../fsaverage/rh.destrieux.simple.2009-07-29.gcs S_oc_middle_and_Lunatus -L labels/rh_front_fs.label ../../../fsaverage/rh.destrieux.simple.2009-07-29.gcs S_precentral-sup-part -inflated -curv rh.sphere ../../../fsaverage/rh.sphere rh.sphere.reg

mris_register -1 -dist 10 -spring 1 -L labels/lh_calc_fs.label ../../../fsaverage/lh.DKTatlas40.gcs pericalcarine -L labels/lh_colat_fs.label ../../../fsaverage/lh.destrieux.simple.2009-07-29.gcs S_oc-temp_med_and_Lingual  -L labels/lh_pariet_fs.label ../../../fsaverage/lh.destrieux.simple.2009-07-29.gcs S_oc_sup_and_transversal -L labels/lh_lat_fs.label ../../../fsaverage/lh.destrieux.simple.2009-07-29.gcs S_oc_middle_and_Lunatus -L labels/lh_front_fs.label ../../../fsaverage/lh.destrieux.simple.2009-07-29.gcs S_precentral-sup-part -inflated -curv lh.sphere ../../../fsaverage/lh.sphere lh.sphere.reg




# Convert to asc for AFNI
# Try this first. It might fail. In which case you run the remaining code
@SUMA_Make_Spec_FS -fid subjid
mris_convert rh.inflated rh.inflated.asc
mris_convert rh.sphere rh.sphere.asc
mris_convert rh.sphere.reg rh.sphere.reg.asc
mris_convert rh.pial rh.pial.asc
mris_convert rh.white rh.white.asc
mris_convert rh.smoothwm rh.smoothwm.asc

mris_convert lh.inflated lh.inflated.asc
mris_convert lh.sphere lh.sphere.asc
mris_convert lh.sphere.reg lh.sphere.reg.asc
mris_convert lh.pial lh.pial.asc
mris_convert lh.white lh.white.asc
mris_convert lh.smoothwm lh.smoothwm.asc

MapIcosahedron -overwrite -ld 141 -spec CC00110XX03_rh.spec -prefix std.141.
MapIcosahedron -overwrite -ld 141 -spec CC00110XX03_lh.spec -prefix std.141.


