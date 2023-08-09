#set data path
data_path=/mnt/e/vlad_test/

sub=sub-CC00060XX03
ses=ses-12501

#create sub path
sub_path=${data_path}/${sub}/${ses}/

#fsaverage
fsaverage_path=/usr/local/freesurfer/7.4.1/subjects/fsaverage

# cd to anat folder
cd $sub_path

#run using original t2 not surfvol
afni -niml &
suma -spec SUMA/std.141.${sub}_both.spec -sv anat/${sub}_${ses}_desc-restore_T2w.nii.gz

# Viewing ROIS
# 	a. Use std.141 spec file
# 	b. View -> object controller
# 	c. Load dataset
# 	d. Switch dset
# 	e. Swapepd I to 1:numeric 
# 	f. Turned off sym
# 		i. Set min I to 1 max to 25
# Change cmap to ROI_i64