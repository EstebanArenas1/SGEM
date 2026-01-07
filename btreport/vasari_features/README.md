# VASARI Features

To standardize neuroimaging-derived feature extraction and improve repeatability, tools such as
VASARI (Visually AcceSAble Rembrandt Images) were developed to quantitatively characterize
anatomical relationships between glioblastoma (GBM) and clinically relevant brain structures.
These relationships are well established in the literature, routinely described in neuroradiology
reports, and actively used by neurosurgeons to assess surgical candidacy.

In this repo, we use a modified variant of VASARI-auto[^1],
an automated VASARI labeling pipeline that has been validated as "non-inferior to expert
radiologist annotations" while substantially reducing inter-rater variability. Our implementation
integrates subject-space anatomical and midline segmentations derived earlier in the BTReport
pipeline, enabling more accurate and anatomically faithful feature estimation. Additionally, we make additional modifications to better fit the needs of this project, outlined in the next section.

## Modifications to VASARI-auto[^1] for BTReport

This codebase is derived from the original VASARI-auto[^1] implementation and has been extended
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

## Attribution and Licensing

This implementation is based on VASARI-auto[^1] by James Ruffle
(UCL Queen Square Institute of Neurology) and is distributed under the Apache 2.0 License.

If you use this code, please cite the original work:

- Original repository: https://github.com/james-ruffle/vasari-auto

```
@article{ruffle2024vasari,
  title={VASARI-auto: Equitable, efficient, and economical featurisation of glioma MRI},
  author={Ruffle, James K and Mohinta, Samia and Baruteau, Kelly Pegoretti and Rajiah, Rebekah and Lee, Faith and Brandner, Sebastian and Nachev, Parashkev and Hyare, Harpreet},
  journal={NeuroImage: Clinical},
  volume={44},
  pages={103668},
  year={2024},
  publisher={Elsevier}
}
```

[^1]: https://numiqo.com/tutorial/kaplan-meier-curve
