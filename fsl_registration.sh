#set data path
data_path=/mnt/e/vlad_test/

#add sub info
sub=sub-CC00058XX09
ses=ses-11300

#create sub path
sub_path=${data_path}/${sub}/${ses}/


# cd to anat folder
cd $sub_path

#define anat and func files
anat=anat/${sub}_${ses}_desc-restore_T2w
func=func/${sub}_${ses}_task-rest_desc-preproc_bold

#Create a 1 volume mean func image for registration
fslmaths ${func}.nii.gz -Tmean ${func}_1vol.nii.gz

#create registration matrix for func2anat
flirt -in ${func}_1vol.nii.gz -ref ${anat}.nii.gz -omat xfm/func2anat.mat -bins 256 -cost corratio -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 12

#apply registration to 1vol func data
flirt -in ${func}_1vol.nii.gz -ref ${anat}.nii.gz -out ${func}_1vol_reg.nii.gz -applyxfm -init xfm/func2anat.mat -interp trilinear

#apply registration to full func data
flirt -in ${func}.nii.gz -ref ${anat}.nii.gz -out ${func}_reg.nii.gz -applyxfm -init xfm/func2anat.mat -interp trilinear

#This works when i plot it in AFNI
#but i still need to get it to be a straightforward nifti file
3dSurf2Vol \
	-spec SUMA/std.141.${sub}_lh.spec \
	-surf_A std.141.lh.white.asc \
	-surf_B std.141.lh.pial.asc \
	-sv anat/${sub}_${ses}_desc-restore_T2w.nii.gz \
	-grid_parent ${func}_1vol_reg.nii.gz \
	-sdata Wang_maxprob_surf_lh_edits.1D.dset \
	-map_func mode \
	-f_steps 500 \
	-f_p1_mm -0.5 \
	-f_pn_mm 0.5 \
	-prefix Wang_maxprob_surf_lh_edits_extended_epi

3dSurf2Vol \
	-spec SUMA/std.141.${sub}_lh.spec \
	-surf_A std.141.lh.white.asc \
	-surf_B std.141.lh.pial.asc \
	-sv anat/${sub}_${ses}_desc-restore_T2w.nii.gz \
	-grid_parent ${func}_1vol_reg.nii.gz \
	-sdata Wang_maxprob_surf_lh_edits.1D.dset \
	-map_func mode \
	-f_steps 500 \
	-f_p1_mm -0.5 \
	-f_pn_mm 0.5 \
	-prefix Wang_maxprob_surf_lh_edits_extended_epi.nii