import os
import argparse
import subprocess
from pathlib import Path


# ENV='OLLAMA_HOST=http://127.0.0.1:50505'

def check_env_variables():
    if "OLLAMA_SIF" not in os.environ:
        raise RuntimeError("Set OLLAMA_SIF. Syntax: export OLLAMA_SIF=/path/to/ollama.sif")
    if "OLLAMA_MODELS" not in os.environ:
        raise RuntimeError("Set OLLAMA_MODELS. Syntax: export OLLAMA_MODELS=/path/to/ollama_models ")
    if "OLLAMA_HOST" not in os.environ:
        raise RuntimeError("Set OLLAMA_HOST. Syntax: export OLLAMA_HOST=http://127.0.0.1:50505")

def start_ollama(gpus="0"):
    check_env_variables()
    sif = os.environ["OLLAMA_SIF"]
    models = os.environ["OLLAMA_MODELS"]

    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = gpus
    env["APPTAINERENV_OLLAMA_MODELS"] = models

    subprocess.run(
        [
            "apptainer", "exec", "--nv",
            "--env", f"OLLAMA_HOST={os.environ['OLLAMA_HOST']}",
            # "--env", ENV,
            # "-B", f"{Path(models).parent}:{Path(models).parent}",
            "-B", f"{Path(models)}:{Path(models)}",
            sif,
            "ollama", "serve",
        ],
        check=True, env=env,)


def check_ollama_server():
    "Check if Ollama server is running."
    try:
        # _, host = ENV.split("=", 1)
        host=os.environ["OLLAMA_HOST"]
        subprocess.run(
            ["curl", "--noproxy", "*", "-sf", f"{host}/api/tags"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        print(f'Ollama server found at {host}')
    except Exception:
        raise RuntimeError(f"Ollama server at {host} not reachable")


def pull_llm(model):
    check_env_variables()
    check_ollama_server()
    sif = os.environ["OLLAMA_SIF"]
    models = os.environ["OLLAMA_MODELS"]
    env = os.environ.copy()
    env["APPTAINERENV_OLLAMA_MODELS"] = models

    subprocess.run([
        "apptainer", "exec",
        "--env", f"OLLAMA_HOST={os.environ['OLLAMA_HOST']}",
        # "--env", ENV,
        # "-B", f"{Path(models).parent}:{Path(models).parent}",
        "-B", f"{Path(models)}:{Path(models)}",
        sif, "ollama", "pull", model
    ], check=True, env=env)



def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    p_start = sub.add_parser("start-ollama")
    p_start.add_argument("--gpus", default="0")

    p_pull = sub.add_parser("pull-llm")
    p_pull.add_argument("model")

    args = p.parse_args()

    if args.cmd == "start-ollama":
        start_ollama(args.gpus)
    elif args.cmd == "pull-llm":
        pull_llm(args.model)

    else:
        raise ValueError('Command not valid. Choose one of: ["start-ollama", "pull-llm"]')


if __name__ == '__main__':
    main()