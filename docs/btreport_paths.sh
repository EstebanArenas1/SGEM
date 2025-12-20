#!/usr/bin/env bash

# BTReport path configuration
# Edit these paths to match your local installation.
# Source this file once per shell/session:
#   source docs/btreport_paths.sh



# Singularity / Apptainer images
export SYNTHMORPH_SIF=/gscratch/scrubbed/juampablo/synthmorph_4.sif
export SYNTHSEG_SIF=/gscratch/scrubbed/juampablo/synthseg.sif
export OLLAMA_SIF=/gscratch/scrubbed/juampablo/ollama.sif

# Ollama model storage (should be on large-capacity storage)
export OLLAMA_MODELS=/gscratch/scrubbed/juampablo/ollama_models



for var in SYNTHMORPH_SIF SYNTHSEG_SIF OLLAMA_SIF; do
    if [ ! -f "${!var}" ]; then
        echo "ERROR: $var does not exist or is not a file: ${!var}" >&2
        return 1
    fi
done

if [ ! -d "$OLLAMA_MODELS" ]; then
    echo "ERROR: OLLAMA_MODELS does not exist or is not a directory: $OLLAMA_MODELS" >&2
    return 1
fi

echo "BTReport paths validated:"
echo "  SYNTHMORPH_SIF : $SYNTHMORPH_SIF"
echo "  SYNTHSEG_SIF  : $SYNTHSEG_SIF"
echo "  OLLAMA_SIF    : $OLLAMA_SIF"
echo "  OLLAMA_MODELS : $OLLAMA_MODELS"
