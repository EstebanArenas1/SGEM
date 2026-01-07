# Patient Metadata

This module organizes and preprocesses patient-level information for BTReport,
including demographics, clinical outcomes (e.g., survival_days), imaging-derived
features, and quantitative midline shift metrics. It also provides plotting
utilities for generating Kaplan–Meier-style survival curves.

## Data Overview

The datasheets directory contains:
- Core clinical tables (survival_days, IDH status, demographics)
- Imaging-derived features (flattened BraTS metadata)
- Midline shift metrics
- Cohort-specific metadata (TCGA, CPTAC, UPenn, UCSF)

`merge_metadata.py` joins these sources into a unified metadata table used by
BTReport.


## Kaplan–Meier Plots

Kaplan–Meier curves visualize time-to-event outcomes (e.g., survival), with time on the x-axis and the estimated survival probability on the y-axis. Steeper declines indicate higher event rates and poorer prognosis, while flatter regions reflect more stable survival. 

When comparing multiple curves, similar or parallel shapes suggest comparable survival experiences, whereas diverging or crossing curves indicate differences between groups. Survival probabilities at specific time points can be read by tracing vertically from the time of interest to the curve and horizontally to the y-axis. For example, looking at the Age variable, we see that at 500 days from diagnosis, the probability of survival of the older age group (High) is around 50\%, while that of the younger age group (Low) is less than half at around 20%. 

In the plots below, these significant differences in the curves are reported using log-rank tests, which produce a familiar p-value. Each plot corresponds to Kaplan–Meier curves for each patient feature collected. For this study significance is thresholded at p < 0.05.

> [!TIP]
> For help understanding KM plots take a look at this tutorial[^1]. 
[^1]: https://numiqo.com/tutorial/kaplan-meier-curve



![Demographics KM](assets/all_vs_surv_KM.png)



