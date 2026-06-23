<h1 align="center">BTReport</h1>
<p align="center">
    <a href="https://proceedings.mlr.press/v315/heras-rivera26a.html">Paper</a> |
    <!-- <a href="https://arxiv.org/abs/2602.16006">arXiv</a> | -->
    <a href="#bibtex">BibTeX</a> |
    <a href="https://huggingface.co/datasets/kurtlab/BTReport-BraTS23"> BTReport-BraTS23 Dataset</a> |
    <a href="#clinical-evaluation-platform">Clinical Evaluation Platform</a>
</p>


<!-- <p align="center">
  <a href="https://arxiv.org/abs/2602.16006">
    <img src="https://img.shields.io/badge/arXiv-2602.16006-B31B1B?style=for-the-badge&logo=arxiv&logoColor=white" alt="arXiv">
  </a>
  <a href="#bibtex">
    <img src="https://img.shields.io/badge/BibTeX-Citation-4B0082?style=for-the-badge&logo=latex&logoColor=white" alt="BibTeX">
  </a>
  <a href="https://huggingface.co/datasets/kurtlab/BTReport-BraTS23">
    <img src="https://img.shields.io/badge/Dataset-BraTS23-FDEE21?style=for-the-badge&logo=huggingface&logoColor=black" alt="Dataset">
  </a>
  <a href="#clinical-evaluation-platform">
    <img src="https://img.shields.io/badge/Platform-Clinical_Eval-34495E?style=for-the-badge" alt="Clinical Evaluation Platform">
  </a>
</p> -->

<!-- [![arXiv](https://img.shields.io/badge/arXiv-2602.16006-b31b1b.svg)](https://arxiv.org/abs/2602.16006) -->


<p align="center">
  <img src="assets/overview.gif" width="900">
</p>

### [**BTReport: A Framework for Brain Tumor Radiology Report Generation with Clinically Relevant Features**](https://arxiv.org/abs/2602.16006)<br/>
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

<details>
<summary>Results</summary>
<p align="center">
<img src="assets/table3.png" width="600">
</p>

<p align="center">
<img src="assets/table4.png" width="600">
</p>
</details>

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

## BTReport-BraTS23 Dataset
 We provide a companion dataset which augments BraTS'23 imaging with BTReport-generated reports to further research in neuro-oncology report generation.
 
 The dataset contains reports generated with gpt-oss:120b and llama3:70b, and can be found in the [`BTReport-BraTS23 HuggingFace`](https://huggingface.co/datasets/kurtlab/BTReport-BraTS23).


<!-- 
For each subject, entries in the CSV look like:


| Subject_ID | Predicted Report (llama3:70b) | Predicted Report (gpt-oss:120b) |
| :--- | :--- | :--- |
| **BraTS-GLI-00000-000** | **FINDINGS** <br/> **MASS EFFECT & VENTRICLES:** <br/> There is a minimal left-to-right midline shift of approximately 4 mm at the level of the septum pellucidum. No significant ventricular asymmetry is identified... | **FINDINGS** <br/> **MASS EFFECT & VENTRICLES:** <br/> There is a minimal left-to-right midline shift of approximately 4 mm at the level of the septum pellucidum. The left lateral ventricle is effaced in its anterior horns... |
 -->
 
### Quick start
```python
from datasets import load_dataset # after pip install datasets

# Load the dataset from HuggingFace
dataset = load_dataset("kurtlab/BTReport-BraTS23")

# Access a specific subject's reports
example = dataset['train'][0]
print(f"Subject: {example['subject_id']}")
print(f"Llama3 Report: {example['Predicted Report (llama3:70b)']}")
print(f"Llama3 Report: {example['Predicted Report (gpt-oss:120b)']}")

```
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
  tmux new -d -s ollama3 "python3 -m btreport.ollama_server start-ollama --gpus 0,1"
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

## Clinical Evaluation Platform
https://github.com/user-attachments/assets/00887ae6-b4be-43b7-9c71-7c4db8572433

We developed an evaluation platform to collect radiologist feedback for future iterations of this project. The platform consists of an interactive image viewer pane followed by a structured questionnaire.

The viewer pane supports:
- Multi-view inspection of the four BraTS MRI sequences (T1n, T1c, T2w, T2-FLAIR)
- Overlay of the three-region tumor segmentation mask
- Visualization of ideal and deformed subject midlines for midline-shift assessment
- 2D in-plane distance measurement

After becoming familiar with the patient’s imaging, radiologists are presented with four synthetically generated reports in random order. They complete a series of multiple-choice and Likert-scale questions assessing report quality, hallucinations, and completeness.

Finally, radiologists rank the reports from most useful to least useful and may optionally provide free-text comments. All responses are stored directly on a secure server.



Check out the platform at: [https://clinical-evaluation-btreport.onrender.com/](https://clinical-evaluation-btreport.onrender.com/)

> [!NOTE]  
> The clinical evaluation platform takes around 5 minutes to load all necessary components after first opening.


## BibTeX

```

@InProceedings{rivera2026btreport,
  title = 	 {BTReport: A Framework for Brain Tumor Radiology Report Generation with Clinically Relevant Features},
  author =       {Heras Rivera, Juampablo E. and Chen, Dickson T. and Ren, Tianyi and Low, Daniel K. and Ruzevick, Jacob and Ben Abacha, Asma and Santamaria-Pang, Alberto and Kurt, Mehmet},
  booktitle = 	 {Proceedings of The 9th International Conference on Medical Imaging with Deep Learning},
  pages = 	 {1445--1472},
  year = 	 {2026},
  editor = 	 {Huo, Yuankai and Gao, Mingchen and Kuo, Chang-Fu and Jin, Yueming and Deng, Ruining},
  volume = 	 {315},
  series = 	 {Proceedings of Machine Learning Research},
  month = 	 {08--10 Jul},
  publisher =    {PMLR},
  pdf = 	 {https://raw.githubusercontent.com/mlresearch/v315/main/assets/heras-rivera26a/heras-rivera26a.pdf},
  url = 	 {https://proceedings.mlr.press/v315/heras-rivera26a.html},
  abstract = 	 {Recent advances in radiology report generation (RRG) have been driven by large paired image-text datasets; however, progress in neuro-oncology RRG has been limited due to a scarcity in open paired image-report datasets. Here, we introduce BTReport, an open-source framework for brain tumor RRG that constructs natural language radiology reports using reliably extracted quantitative imaging features. Unlike existing approaches that rely on general-purpose or fine-tuned vision-language models for both image interpretation and report composition, BTReport performs deterministic feature extraction of clinically-relevant features, then uses large language models only for syntactic structuring and narrative synthesis. By separating RRG into deterministic feature extraction and report generation stages, synthetically generated reports are completely interpretable and contain reliable numerical measurements, a key component lacking in existing RRG frameworks. We validate the clinical relevance of BTReport-derived features, and demonstrate that BTReport-generated reports more closely resemble reference clinical reports when compared to existing baseline RRG methods. To further research in neuro-oncology RRG, we introduce BTReport-BraTS, a companion dataset that augments BraTS imaging with synthetic radiology reports generated with BTReport, and BTReview, a web-based platform for validating the clinical quality of synthetically generated radiology reports.}
}

