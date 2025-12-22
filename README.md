


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



## Installation (~1.5 hours)
See [INSTALL.md](docs/INSTALL.md) for full installation instructions on HPC systems. 


![-----------------------------------------------------](assets/purpleline.png)

## Usage


### 1. Dataset formatting
  BTReport requires each subject's data be separated into individual folders. Each subject folder should include at least two niftii files: a T1 scan with file ending `-t1n.nii.gz` , and the corresponding tumor segmentation mask with file ending `-seg.nii.gz`. Following BraTS convention, segmentations should contain NCR, ED, and ET subregions.  Optionally an additional file with additional patient metadata can be added in a file as `metadata.json`. 
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
#### For a single subject:

```bash
module load apptainer
conda activate BTReport
python3 -m btreport.generate_report --subject_folder <path/to/subject/folder> --llm gpt-oss:120b
```
#### For multiple subjects in a directory:
```bash
module load apptainer
conda activate BTReport
python3 -m btreport.run_all_reports --root_folder <path/to/root/folder> --llm llama3:70b
```

![-----------------------------------------------------](assets/purpleline.png)

## Dataset
We provide a companion dataset which augments BraTS imaging with these features to further research in neuro-oncology report generation.



