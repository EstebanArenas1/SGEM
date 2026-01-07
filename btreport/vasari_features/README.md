# VASARI Features

To standardize neuroimaging-derived feature extraction and improve repeatability, tools such as
VASARI (Visually AcceSAble Rembrandt Images) were developed to quantitatively characterize
anatomical relationships between glioblastoma (GBM) and clinically relevant brain structures.
These relationships are well established in the literature, routinely described in neuroradiology
reports, and actively used by neurosurgeons to assess surgical candidacy.

In this repo, we use a modified variant of [VASARI-auto](#VASARI-auto),
an automated VASARI labeling pipeline that has been validated as "non-inferior to expert
radiologist annotations" while substantially reducing inter-rater variability. Our implementation
integrates subject-space anatomical and midline segmentations derived earlier in the BTReport
pipeline, enabling more accurate and anatomically faithful feature estimation. Additionally, we make additional modifications to better fit the needs of this project, outlined in the next section.

## Modifications to [VASARI-auto](#VASARI-auto) for BTReport

This codebase is derived from the original [VASARI-auto](#VASARI-auto) implementation and has been extended
to better support large-scale, automated feature extraction from BraTS-style datasets.
Key modifications include:

- Refactoring the original pipeline into an `ExtractVASARI` class for cleaner integration
- Improved midline-crossing logic by computing directly in subject space, using the patient's deformed midline, extracted using the methods described in BTReport.
- Robust multifocal vs. multicentric lesion identification using connected-component analysis,
  retaining secondary lesions only when their maximal diameter exceeds 1 cm
- Use of images in their original acquisition space rather than MNI152-registered volumes to
  improve estimation of quantities such as necrotic proportion, etc.
- Inclusion of eloquent cortical regions derived from Brodmann Area Maps
- Addition of lesion size measurements along anterior–posterior, transverse, and cranio–caudal axes
- Restriction to features derivable from BraTS-compatible segmentation masks
  (e.g., removal of non-computable CET proportions)
- Conversion of proportion-based features to continuous floating-point values
.

## VASARI-auto

This implementation is based on VASARI-auto by James Ruffle
(UCL Queen Square Institute of Neurology) and is distributed under the Apache 2.0 License. If you use this code, please cite the original work.

 >[VASARI-auto: Equitable, efficient, and economical featurisation of glioma MRI](https://pmc.ncbi.nlm.nih.gov/articles/PMC11415871/)  
  James K. Ruffle, Samia Mohinta, Kelly Pegoretti Baruteau, Rebekah Rajiah, Faith Lee,  
  Sebastian Brandner, Parashkev Nachev, and Harpreet Hyare  
  NeuroImage: Clinical, 44, 103668

  [Full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC11415871/) ·
  [GitHub repository](https://github.com/jamesruffle/vasari-auto)


