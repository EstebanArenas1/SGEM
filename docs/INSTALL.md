
# Installation (~1.5 hours)
* ## Download Apptainer/Singularity images (1 hour)
  BTReport requires SynthSeg, SynthMorph, and Ollama. For convenience we have packaged the .sif images used in this Zenodo [artifact](https://zenodo.org/records/17982349). To download all of these on an HPC system, use the following command:
  ```bash
  for f in ollama.sif synthseg.sif synthmorph_4.sif; do
    wget -c https://zenodo.org/records/17982349/files/$f
  done
  ```
  > *Note: Containers are ~11 GB in total size.*

* ## Start Ollama server and download LLMs (25 minutes)

    
  ### 1. Set environment variables. 
  
  OLLAMA_MODELS should be located in a filesystem with large storage capacity, as models are 100s of GB large.
  ```bash
  export OLLAMA_SIF=/path/to/ollama.sif
  export OLLAMA_MODELS=/path/to/ollama_models
  ```
  
  ### 2. Start the Ollama server.
  On a GPU allocation, start the server in the background (e.g., using tmux), then detach.
  ```bash
  tmux new -t ollama
  python3 -m btreport.ollama_server start-ollama --gpus 0
  ```
  ### 3. Detach from tmux, and return to your original terminal
  ```bash
  Ctrl-b d
  ```
  
  ### 4. In your original terminal, download the LLMs used for generation and evaluation.
     Here we download [gpt-oss:120b](https://ollama.com/library/gpt-oss:120b) (10 minute download), [llama3:70b](https://ollama.com/library/llama3:70b) (6 minute download), and [deepseek-r1:70b](https://ollama.com/library/deepseek-r1:70b) (6 minute download).
  
  ```bash
  python3 -m btreport.ollama_server pull-llm gpt-oss:120b
  python3 -m btreport.ollama_server pull-llm llama3:70b
  python3 -m btreport.ollama_server pull-llm deepseek-r1:70b
  ```



* ## Create conda environment (5 minutes)
  A suitable [conda](https://conda.io/) environment named `BTReport` can be created
  and activated with:
     ```bash
     conda env create -f environment.yml
     conda activate BTReport
     ```
  