probtrackx2  -x ${maindir}/roi/week40_thalamus_2native_edits_lh.nii.gz \
    -l --onewaycondition --pd -c 0.2 -S 2000 --steplength=0.5 -P 10000 --fibthresh=0.01 --distthresh=0.0 --sampvox=0.0 \
    --avoid=${maindir}/exclusionmasks/exclusion_dwispace_allmasks_rh.nii \
    --forcedir --opd -s ${maindir}/input2bed.bedpostX/merged -m ${maindir}/input2bed.bedpostX/nodif_brain_mask \
    --dir=${curr_outdir} --waypoints=${curr_outdir}/waypoints.txt  --waycond=AND --targetmasks=${curr_outdir}/targets.txt --os2t


#vlad attempt
#f'applywarp --ref={sub_dir}/dwi/nodif_brain.nii.gz --in={waypoint_file} --warp={xfm} --out={out_file}'
#ses=ses-38800


sub=sub-CC00087AN14
ses=ses-31800

sub_dir=/mnt/DataDrive1/data_preproc/human_mri/dhcp_preprocessed/${sub}/${ses}

warp=${sub_dir}/xfm/${sub}_${ses}_from-extdhcp40wk_to-dwi_mode-image.nii.gz
target_roi=/mnt/DataDrive1/data_preproc/human_mri/dhcp_preprocessed/atlases/rois/wang/40wk/lh_V1v_40wk.nii.gz
target_roi_native=${sub_dir}/rois/wang/lh_IPS0_dwi.nii.gz
roi=/mnt/DataDrive1/data_preproc/human_mri/dhcp_preprocessed/atlases/rois/pulvinar/lh_pulvinar_40wk.nii.gz 
seed_roi=${sub_dir}/rois/pulvinar/lh_pulvinar_dwi.nii.gz

brain=${sub_dir}/dwi/nodif_brain.nii.gz

exclusionmask=${sub_dir}/rois/exclusionmasks/exclusion_allmasks_rh.nii.gz
merged=${sub_dir}/dwi_bedpostx.bedpostX/merged
nodif_brain_mask=${sub_dir}/dwi_bedpostx.bedpostX/nodif_brain_mask.nii.gz

waypoint=/mnt/DataDrive1/data_preproc/human_mri/dhcp_preprocessed/sub-CC00087AN14/ses-31800/rois/waypointmasks/V1_lh_sub-CC00087AN14_waypoint_mask_dwispace.nii.gz
waypoint_file=/mnt/DataDrive3/vlad/git_repos/dhcp/diffusion/waypoints.txt

target_file=/mnt/DataDrive3/vlad/git_repos/dhcp/diffusion/targets.txt

out_dir=${sub_dir}/derivatives/probtrackx

applywarp --ref=${brain} --in=${roi} --warp=${warp} --out=${seed_roi}


probtrackx2 -x ${seed_roi} -l --onewaycondition --pd -c 0.2 -S 2000 --steplength=0.5 -P 10000 --fibthresh=0.01 --distthresh=0.0 --sampvox=0.0 --avoid=${exclusionmask} --forcedir --opd -s ${merged} -m ${nodif_brain_mask} --dir=${out_dir} --waypoints=${waypoint_file} --waycond=AND --targetmasks=${target_file} --os2t



#rerun mike version
maindir=/mnt/DataDrive3/vlad/diffusion/individual_subjects/sub-CC00063AN06/ses-15102
curr_outdir=${maindir}/test
waypoints=${maindir}/ProbTrackX2/V1v_lh_distcorr/waypoints_vlad.txt
targets=${maindir}/ProbTrackX2/V1v_lh_distcorr/targets_vlad.txt


probtrackx2 -x ${maindir}/roi/week40_thalamus_2native_edits_lh.nii.gz -l --onewaycondition --pd -c 0.2 -S 2000 --steplength=0.5 -P 10000 --fibthresh=0.01 --distthresh=0.0 --sampvox=0.0 --avoid=${maindir}/exclusionmasks/exclusion_dwispace_allmasks_rh.nii --forcedir --opd -s ${maindir}/input2bed.bedpostX/merged -m ${maindir}/input2bed.bedpostX/nodif_brain_mask --dir=${curr_outdir} --waypoints=${waypoints} --waycond=AND --targetmasks=${targets} --os2t
