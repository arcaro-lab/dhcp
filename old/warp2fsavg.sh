#set data path
data_path=/mnt/e/vlad_test/

#add sub info
sub=sub-CC00058XX09
ses=ses-11300

sub=sub-CC00071XX06
ses=ses-27000

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
mris_curvature -thresh .999 -n -a 5 -w -distances 10 10 surf/rh.inflated
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

#convert anat to afni format
3dcopy anat/${sub}_${ses}_desc-restore_T2w.nii.gz anat/${sub}_${ses}_desc-restore_T2w+orig.nii.gz

#make orig directory in surf
#needed even if empty
mkdir surf/orig

# run this without the -nifti flag
@SUMA_Make_Spec_FS -sid ${sub}

#run using original t2 not surfvol
afni -niml &
suma -spec SUMA/std.141.${sub}_both.spec -sv anat/${sub}_${ses}_desc-restore_T2w.nii.gz

suma -spec SUMA/std.141.${sub}_both.spec -sv surf/${sub}_SurfVol+orig

3dSurf2Vol \
	-spec SUMA/std.141.${sub}_lh.spec \
	-surf_A std.141.lh.white.asc \
	-surf_B std.141.lh.pial.asc \
	-sv ${sub}_${ses}_desc-restore_T2w.nii.gz \
	-grid_parent sub-CC00108XX09_ses-36800_task-rest_desc-preproc_bold_meanTP.nii.gz \
	-sdata Wang_maxprob_surf_lh_edits.1D.dset \
	-map_func mode \
	-f_steps 500 \
	-f_p1_mm -0.5 \
	-f_pn_mm 0.5 \
	-prefix Wang_maxprob_surf_lh_edits_extended_epi