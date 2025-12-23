import argparse
import subprocess
import os
import json 
from .utils.log import get_logger

# logger = get_logger("btreport.run_all_reports", subject="run_all")
logger = get_logger("batchgen")

def main():
    parser = argparse.ArgumentParser(
        description="Run generate_report.py on ALL subject folders inside a directory."
    )

    parser.add_argument("--root_folder", type=str, required=True,
                        help="Path containing many subject subfolders.")

    parser.add_argument("--clear_tmp", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--ncr_label", type=int, default=1)
    parser.add_argument("--ed_label", type=int, default=2)
    parser.add_argument("--et_label", type=int, default=4)
    parser.add_argument("--llm", type=str, default="gpt-oss:120b")
    parser.add_argument("--eval", action="store_true", help='Running evaluation after generation.')

    args = parser.parse_args()

    root = os.path.realpath(args.root_folder)
    llm = args.llm

    generate_script = "btreport.generate_report"


    for entry in sorted(os.listdir(root)):
        subject_dir = os.path.join(root, entry)

        if not os.path.isdir(subject_dir):
            continue  # skip files

        logger.info(f"\n=== Processing {subject_dir} ===")

        cmd = [
            "python3",
            "-m",
            generate_script,
            "--subject_folder", subject_dir,
            "--ncr_label", str(args.ncr_label),
            "--ed_label", str(args.ed_label),
            "--et_label", str(args.et_label),
            "--llm", llm,
        ]

        if args.clear_tmp:
            cmd.append("--clear_tmp")
        if args.overwrite:
            cmd.append("--overwrite")

        subprocess.run(cmd, check=True)

        update_merged_reports(
            root_dir=root,
            subject_id=entry,
            llm=llm,
        )

    logger.info("\nFinished processing all subjects.")





def update_merged_reports(root_dir, subject_id, llm, real_report_key='Clinical Report', output_filename='merged_reports_btreport.json', subject_report_filename="patient_metadata_btreport.json"):
    merged_path = os.path.join(root_dir, output_filename)
    if os.path.exists(merged_path):
        with open(merged_path, "r") as f:
            merged = json.load(f)
    else:
        merged = {}

    subject_report_path = os.path.join(root_dir, subject_id, subject_report_filename)
    if not os.path.exists(subject_report_path):
        logger.info(f'Missing {subject_report_path}, skipping merge.')
        return

    try:
        with open(subject_report_path, "r") as f:
            subject_btreport = json.load(f)
    except Exception as e:
        logger.info(f"Failed to read {subject_report_path}: {e}")
        return

    bt_generated_key = f"BTReport Generated Report ({llm})"
    predicted_key = f"Predicted Report ({llm})"

    if real_report_key not in subject_btreport:
        logger.info(f"Merge error: '{real_report_key}' missing in {subject_report_path}")
        return

    if bt_generated_key not in subject_btreport:
        logger.info(f"Merge error: '{bt_generated_key}' missing in {subject_report_path}")
        return

    if subject_id not in merged:
        merged[subject_id] = {}

    # Store ground truth
    merged[subject_id][real_report_key] = subject_btreport[real_report_key]

    # Store prediction
    merged[subject_id][predicted_key] = subject_btreport[bt_generated_key]

    # Safe write
    tmp_path = merged_path + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(merged, f, indent=2)
    os.replace(tmp_path, merged_path)

    logger.info(f"Merged {subject_id} [{llm}]")

if __name__ == "__main__":
    main()
