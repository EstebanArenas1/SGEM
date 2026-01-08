# Midline Shift

Midline shift (MLS) is an intracranial pathology characterized by the displacement of brain tissue across the skull’s midsagittal axis. MLS arises as a result of traumatic brain injury or tumor mass effects and is an indirect indicator of elevated intracerebral pressure. Estimation of MLS is done by identifying the axial slice with the largest deviation, as indicated by midline structures such as the septum pellucidum, the third ventricle, the fourth ventricle or the falx cerebri. 

Midline shift estimation is subject to high inter-rater variability as there is not a standard procedure for axial slice level selection. Here, we propose a novel pipeline for MLS estimation based on clinical guidelines, using a deep learning atlas-based segmentation approach.

 Our approach leverages the robust registration capabilities of SynthMorph (Hoffmann et al., 2024) to register hand-annotated midline segmentations from a MNI152 atlas template onto patient T1 scans. These are compared to an “ideal” midline, which is defined by connecting the anterior and posterior points of the falx cerebri for each axial slice. 
 
 By calculating the distance between the ideal and subject midlines at each voxel, we obtain highly-accurate 3D MLS estimations in seconds, giving a more complete picture in comparison to 2D automated or manual annotation methods. Furthermore, this approach has strong zero-shot generalization and can be applied to any MRI or CT scan.

<p align="center">
<img src=../../assets/mls.png />
</p>


## Pseudocode
```text
Input:
- Subject 3D T1 scan
- Tumor segmentation mask with necrotic core (NCR), edema (ED),
  and enhancing tumor (ET) labeled according to the BraTS convention
- Manually annotated midline mask in MNI152 atlas space
  (../utils/midline_plane_regressed.nii.gz)

Steps:

1. Register the MNI152 atlas into subject space
   - Compute the MNI152-to-subject nonlinear registration using SynthMorph

2. Register the subject scan into MNI152 space
   - Compute the subject-to-MNI152 nonlinear registration

3. Warp the atlas midline mask into subject space
   - Apply the MNI152-to-subject transform to the atlas midline annotation

4. Construct the ideal midline in subject space
   For each axial slice:
   - Identify the anterior and posterior points of the falx cerebri
   - Connect these points with a straight line to define the ideal midline

5. Compare the subject midline to the ideal midline
   - Compute voxel-wise distances between the two midlines
   - Produce a dense 3D midline shift map

6. Account for tumor crossing the anatomical midline
   - Split tumor subregions (NCR, ED, ET, NCR+ET) by left/right
   - Identify the dominant tumor side
   - If NCR+ET crosses the midline:
       - Zero midline values within the tumor core
         (attribute shift to edema only)
   - Otherwise:
       - Update the subject midline to follow the tumor boundary
         opposite the dominant tumor bulk

7. Aggregate midline shift metrics
   - Per-slice signed maximum shift
   - Mean, median, maximum, and 95th percentile shift
   - Number of slices with measurable shift
   - Presence and level of clinically significant midline shift

8. Save outputs
   - 3D midline distance map (NIfTI)
   - Quantitative summary statistics (JSON)

Output:
- Dense 3D midline shift estimation in subject space
- Clinically interpretable midline shift summary metrics
