


# BTReport 
[arXiv](./assets/MIDL_2026_BTReport__Latest_.pdf) | [BibTeX](./assets/MIDL_2026_BTReport__Latest_.pdf)

<!-- [![arXiv](https://img.shields.io/badge/arXiv-2112.1075-b31b1b.svg)](https://arxiv.org/abs/2112.1075)  -->


<p align="center">
<img src=assets/overview.gif />
</p>

### [**BTReport: A Framework for Brain Tumor Radiology Report Generation with Clinically Relevant Features**](./assets/MIDL_2026_BTReport__Latest_.pdf)<br/>
[Juampablo E. Heras Rivera](https://juampabloheras.github.io/)\*, Dickson T. Chen\*, Tianyi Ren, Daniel K. Low,  <br/>
Jacob Ruzevick, Asma Ben Abacha, Alberto Santamaria-Pang, Mehmet Kurt<br/>
\*equal contribution
<table>
<tr>
<td>

**[KurtLab, University of Washington](https://www.kurtlab.com/)** <br/>
**[Microsoft Health AI, Microsoft](https://www.microsoft.com/en-us/research/lab/microsoft-health-futures/)**

</td>
<!-- <td width="200"></td> spacer column -->
<td align="right">
  <img src="assets/affiliations.png" width="220" alt="BTReport affiliations">
</td>
</tr>
</table>

![-----------------------------------------------------](assets/purpleline.png)

## Overview
BTReport is an open-source framework for brain tumor radiology report generation using quantitative neuroimaging features.  BTReport first extracts clinically relevant features (patient metadata, VASARI features, midline shift) using a patients scan and tumor segmentation mask, then uses large language models for report formatting.

The framework consists of four components:
-  **[patient_metadata](./btreport/patient_metadata/)** — demographic and clinical information (e.g., age, sex, diagnosis, outcome).
-  **[vasari_features](./btreport/vasari_features/)** — standardized VASARI features.
-  **[midline_shift](./btreport/midline_shift/)** — quantitative estimation of 3D midline shift using a deep learning registration approach.
-  **[llm_report_generation](./btreport/llm_report_generation/)** — LLM synthesis of structured radiology reports grounded in deterministic features.

![-----------------------------------------------------](assets/purpleline.png)
## Example findings generated with BTReport
<p align="center">
<img src=assets/example_subject.png />
</p>

**MASS EFFECT & VENTRICLES:**  
There is an approximately 10 mm leftward midline shift at the level of the fourth ventricle. The right lateral ventricle, including the inferior horn, is effaced by tumor, whereas the left lateral ventricle is enlarged, producing marked ventricular asymmetry. No tonsillar herniation is seen, and the basal cisterns remain patent.

**BRAIN / ENHANCEMENT:**  
A solitary, markedly enhancing lesion centered in the right cortex involving the parietal, occipital, and temporal lobes measures 7.1 × 4.9 × 5.9 cm (AP × TV × CC). The enhancing rim is thick (>3 mm). The lesion demonstrates ependymal invasion of the right lateral ventricle and extends into deep right-sided structures, including the thalamus, caudate, putamen, pallidum, and hippocampus, with associated deep white matter infiltration. Multiple small enhancing satellite nodules are present adjacent to the main mass. Approximately 6% of the lesion is non-enhancing necrotic tissue. A large surrounding FLAIR-hyperintense region consistent with vasogenic edema comprises the majority of the lesion volume (66%) but does not cross the midline. The enhancing component remains confined to the right side.

![-----------------------------------------------------](assets/purpleline.png)


## Installation (~1.5 hours)

Installation is divided into three steps:
  1. Downloading all accompanying Singularity images
  2. Setting up Ollama and downloading the LLMs used for inference and evaluation
  3. Creating a conda environment
     
See [INSTALL.md](docs/INSTALL.md) for full installation instructions on HPC systems. 
![-----------------------------------------------------](assets/purpleline.png)

## Usage


### 1. Dataset formatting
  BTReport requires each subject's data be separated into individual folders. Each subject folder should include at least two niftii files: a T1 scan with file ending `-t1n.nii.gz` , and the corresponding tumor segmentation mask with file ending `-seg.nii.gz`. Following BraTS convention, segmentations should contain NCR, ED, and ET subregions.  Optionally, an additional metadata.json file may be provided containing the ground-truth Findings section and/or supplementary patient metadata. When included, the ground-truth Findings section should be stored under the 'Clinical Report' key.
  ```text
  data/
  ├── subject_001/
  │   ├── <subject_identifier>-t1n.nii.gz
  │   ├── <subject_identifier>-seg.nii.gz
  │   └── metadata.json  
  ├── subject_002/
  │   ├── <subject_identifier>-t1n.nii.gz
  │   └── <subject_identifier>-seg.nii.gz
  └── ...
  ```


### 2. Set environment variables and start Ollama server
* Change the paths in `docs/btreport_paths.sh`  to match those set in [INSTALL.md](docs/INSTALL.md), then run 
  ```bash
  source docs/btreport_paths.sh 
  ```
  This will set the paths as environment variables and validate that each provided path points to a file/dir. 

* On a GPU allocation, start the Ollama server in the background (e.g., within a detached [tmux](https://hamvocke.com/blog/a-quick-and-easy-guide-to-tmux/) session).
  ```bash
  tmux new -t ollama
  python3 -m btreport.ollama_server start-ollama --gpus 0,1
  Ctrl-b d
  ```


### 3. Report generation
<!-- #### For a single subject:

```bash
module load apptainer
conda activate BTReport
python3 -m btreport.generate_report \
  --subject_folder <path/to/subject/folder> \
  --llm gpt-oss:120b
``` -->
#### For all subjects in a directory:
```bash
module load apptainer
conda activate BTReport
python3 -m btreport.run_all_reports \
  --root_folder <path/to/root/folder> \
  --llm llama3:70b
```
This command will extract all of the relevant metadata, then generate reports for each subject individually. Additionally, if a ground truth report is provided for a subject, the paired ground truth and predicted reports will be saved to `root_folder/merged_reports_btreport.json` for evaluation.


### 4. Evaluation against real report
To evaluate the quality of reports, we compare generated reports to ground truth clinical reports when they are available. The following command calculates the evaluation metrics included in the BTReport manuscript, taking `root_folder/merged_reports_btreport.json` as an input.

#### For metrics without verbose explanations
```bash
python3 -m btreport.eval_json \
  --json </path/to/merged_reports_btreport.json> \
  --real_report_key "Clinical Report" \
  --synthetic_report_key "Predicted Report (gpt-oss:120b)" \
  --parse-real \
  --parse-synthetic \ 
  --devices 0,1

```

#### For full verbose metric details
```bash
python3 -m btreport.eval_json \
  --json </path/to/merged_reports_btreport.json> \
  --real_report_key "Clinical Report" \
  --synthetic_report_key "Predicted Report (llama3:70b)" \
  --devices 0,1 \
  --parse-real \
  --no-parse-synthetic \
  --do_details

```

![-----------------------------------------------------](assets/purpleline.png)

## BTReport-BraTS23 Dataset
 We provide a companion dataset which augments BraTS'23 imaging with these features to further research in neuro-oncology report generation.
 
 The dataset contains reports generated with gpt-oss:120b and llama3:70b, and can be found in `./btreport_brats23.json`.



