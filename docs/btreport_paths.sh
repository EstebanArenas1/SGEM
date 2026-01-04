#!/usr/bin/env bash

# BTReport path configuration
# Edit these paths to match your local installation.
# Source this file once per shell/session:
#   source docs/btreport_paths.sh



# Singularity / Apptainer images
export SYNTHMORPH_SIF=/absolute/path/to/synthmorph_4.sif
export SYNTHSEG_SIF=/absolute/path/to/synthseg.sif
export OLLAMA_SIF=/absolute/path/to/ollama.sif


export OLLAMA_MODELS=/absolute/path/to/ollama_models # Ollama model storage (should be on large-capacity storage)
export SUBJECTS_DIR=/absolute/root # Relative directory from which subject files are referenced inside containers. Usually I set this to the root of my scratch space so I dont have to deal with relative paths.





## Below here should not need to be changed ##

export OLLAMA_HOST='http://127.0.0.1:11434'
unset http_proxy https_proxy all_proxy
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY


if [ ! -x "$SYNTHMORPH_SIF" ]; then
    chmod +x "$SYNTHMORPH_SIF"
fi


for var in SYNTHMORPH_SIF SYNTHSEG_SIF OLLAMA_SIF; do
    if [ ! -f "${!var}" ]; then
        echo "ERROR: $var does not exist or is not a file: ${!var}" >&2
        return 1
    fi
done

for var in SUBJECTS_DIR OLLAMA_MODELS; do
    if [ ! -d "${!var}" ]; then
        echo "ERROR: $var does not exist or is not a directory: ${!var}" >&2
        return 1
    fi
done


echo "BTReport paths validated:"
echo "  SYNTHMORPH_SIF : $SYNTHMORPH_SIF"
echo "  SYNTHSEG_SIF  : $SYNTHSEG_SIF"
echo "  OLLAMA_SIF    : $OLLAMA_SIF"
echo "  OLLAMA_MODELS : $OLLAMA_MODELS"
echo "  SUBJECTS_DIR  : $SUBJECTS_DIR"
echo "  OLLAMA_HOST   : $OLLAMA_HOST"
