#set data path
data_path=/mnt/e/vlad_test/

#add sub info
sub=sub-CC00058XX09
ses=ses-11300

sub=sub-CC00060XX03
ses=ses-12501

#create sub path
sub_path=${data_path}/${sub}/${ses}/

#fsaverage
fsaverage_path=/usr/local/freesurfer/7.4.1/subjects/fsaverage

# cd to anat folder
cd $sub_path

#make surf directory
mkdir ${sub_path}/surf

#Convert curv files
#vlad version which converts curvs and sulc to surface 
#using wb_command
wb_command -gifti-convert ASCII anat/${sub}_${ses}_hemi-left_curv.shape.gii surf/lh.curv
wb_command -gifti-convert ASCII anat/${sub}_${ses}_hemi-right_curv.shape.gii surf/rh.curv

wb_command -gifti-convert ASCII anat/${sub}_${ses}_hemi-left_sulc.shape.gii surf/lh.sulc
wb_command -gifti-convert ASCII anat/${sub}_${ses}_hemi-right_sulc.shape.gii surf/rh.sulc


#mike version which converts curv and sulcus to text first
#and then converts those from txt to sruface
wb_command -gifti-convert ASCII anat/${sub}_${ses}_hemi-left_curv.shape.gii surf/lh_curv.txt
wb_command -gifti-convert ASCII anat/${sub}_${ses}_hemi-right_curv.shape.gii surf/rh_curv.txt

wb_command -gifti-convert ASCII anat/${sub}_${ses}_hemi-left_sulc.shape.gii surf/lh_sulc.txt
wb_command -gifti-convert ASCII anat/${sub}_${ses}_hemi-right_sulc.shape.gii surf/rh_sulc.txt


# Convert gifti files
mris_convert anat/${sub}_${ses}_hemi-left_pial.surf.gii surf/lh.pial
mris_convert anat/${sub}_${ses}_hemi-left_wm.surf.gii surf/lh.white

mris_convert anat/${sub}_${ses}_hemi-right_pial.surf.gii surf/rh.pial
mris_convert anat/${sub}_${ses}_hemi-right_wm.surf.gii surf/rh.white



# # Write curv and sulc files In Matlab:
#VA: What does this do?
# clear all
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
mris_smooth -n 5 -nw -seed 1234 surf/rh.white surf/rh.smoothwm
mris_inflate -n 2 surf/rh.smoothwm surf/rh.inflated
mris_curvature -w surf/rh.white
mris_curvature -thresh .999 -n -a 5 -w -distances 10 10surf/ rh.inflated
mris_sphere surf/rh.inflated surf/rh.sphere


mris_smooth -n 5 -nw -seed 1234 surf/lh.white surf/lh.smoothwm
mris_inflate -n 2 surf/lh.smoothwm surf/lh.inflated
mris_curvature -w surf/lh.white
mris_curvature -thresh .999 -n -a 5 -w -distances 10 10 surf/lh.inflated
mris_sphere surf/lh.inflated surf/lh.sphere

#Register to fsaverage
mris_register surf/lh.sphere ${FREESURFER_HOME}/average/lh.average.curvature.filled.buckner40.tif surf/lh.sphere.reg
mris_register surf/rh.sphere ${FREESURFER_HOME}/average/rh.average.curvature.filled.buckner40.tif surf/rh.sphere.reg

#convert back to gifti
mris_convert surf/lh.sphere.reg surf/lh.sphere.reg.gii
mris_convert surf/rh.sphere.reg surf/rh.sphere.reg.gii

#convert anat to mgz
mri_convert anat/${sub}_${ses}_desc-restore_T2w.nii.gz surf/orig.mgz

#make orig directory in surf
#needed even if empty
mkdir surf/orig

# run this
@SUMA_Make_Spec_FS -NIFTI -sid ${sub}




@SUMA_AlignToExperiment -exp_anat anat/${sub}_${ses}_desc-restore_T2w.nii.gz -surf_anat SUMA/${sub}_SurfVol+orig -align_centers

# # Convert to asc for AFNI
# # Try this first. It might fail. In which case you run the remaining code
@SUMA_Make_Spec_FS -sid sub-CC00058XX09

#there's also a @SUMA_Make_Spec_SF (SF INSTEAD OF FS)

mris_convert surf/lh.inflated SUMA/lh.inflated.asc
mris_convert surf/lh.sphere SUMA/lh.sphere.asc
mris_convert surf/lh.sphere.reg SUMA/lh.sphere.reg.asc
mris_convert surf/lh.pial SUMA/lh.pial.asc
mris_convert surf/lh.white SUMA/lh.white.asc
mris_convert surf/lh.smoothwm SUMA/lh.smoothwm.asc

mris_convert surf/rh.inflated SUMA/rh.inflated.asc
mris_convert surf/rh.sphere SUMA/rh.sphere.asc
mris_convert surf/rh.sphere.reg SUMA/rh.sphere.reg.asc
mris_convert surf/rh.pial SUMA/rh.pial.asc
mris_convert surf/rh.white SUMA/rh.white.asc
mris_convert surf/rh.smoothwm SUMA/rh.smoothwm.asc



# MapIcosahedron -overwrite -ld 141 -spec CC00110XX03_rh.spec -prefix std.141.
# MapIcosahedron -overwrite -ld 141 -spec CC00110XX03_lh.spec -prefix std.141.

# # DRAW ROIS
#VA NOTE: WE are no longer doing these steps
# 1 calc
# 2 colat
# 3 parietal
# 4 lateral
# 5 frontal

# Convert .niml.rois to .label
# need allnode label from fs. make with freeview and remove the header!
# add header followed by node count on second line

#!ascii label  , from subject  vox2ras=TkReg

# # Register to fsaverage sphere
# mris_register -1 -dist 10 -spring 1 -L labels/rh_calc_fs.label ../../../fsaverage/rh.DKTatlas40.gcs pericalcarine -L labels/rh_colat_fs.label ../../../fsaverage/rh.destrieux.simple.2009-07-29.gcs S_oc-temp_med_and_Lingual  -L labels/rh_pariet_fs.label ../../../fsaverage/rh.destrieux.simple.2009-07-29.gcs S_oc_sup_and_transversal -L labels/rh_lat_fs.label ../../../fsaverage/rh.destrieux.simple.2009-07-29.gcs S_oc_middle_and_Lunatus -L labels/rh_front_fs.label ../../../fsaverage/rh.destrieux.simple.2009-07-29.gcs S_precentral-sup-part -inflated -curv rh.sphere ../../../fsaverage/rh.sphere rh.sphere.reg

# mris_register -1 -dist 10 -spring 1 -L labels/lh_calc_fs.label ../../../fsaverage/lh.DKTatlas40.gcs pericalcarine -L labels/lh_colat_fs.label ../../../fsaverage/lh.destrieux.simple.2009-07-29.gcs S_oc-temp_med_and_Lingual  -L labels/lh_pariet_fs.label ../../../fsaverage/lh.destrieux.simple.2009-07-29.gcs S_oc_sup_and_transversal -L labels/lh_lat_fs.label ../../../fsaverage/lh.destrieux.simple.2009-07-29.gcs S_oc_middle_and_Lunatus -L labels/lh_front_fs.label ../../../fsaverage/lh.destrieux.simple.2009-07-29.gcs S_precentral-sup-part -inflated -curv lh.sphere ../../../fsaverage/lh.sphere lh.sphere.reg







