import yaml
import glob
import os
import re
import numpy as np
from collections import defaultdict
from typing import Dict, Any

# ============================================================
# Utility helpers (same semantics as your evaluator)
# ============================================================

def is_not_mentioned(val) -> bool:
    if val is None:
        return True
    if isinstance(val, str) and val.strip().lower() in {
        "not mentioned", "not reported", "unknown", "n/a"
    }:
        return True
    return False


def normalize_tokens(text: str):
    return re.findall(r"[a-z]+", (text or "").lower())


def word_ngrams(tokens, n):
    return {
        tuple(tokens[i:i+n])
        for i in range(len(tokens) - n + 1)
    }


def ngram_partial_match(a: str, b: str, n: int = 1, min_overlap: int = 1):
    if not a or not b:
        return False
    ta = normalize_tokens(a)
    tb = normalize_tokens(b)
    if len(ta) < n or len(tb) < n:
        return False
    return "Partial" if len(word_ngrams(ta, n) & word_ngrams(tb, n)) >= min_overlap else False


VENTRICLE_KEYWORDS = ["ventricle", "ventricular", "horn", "ependymal"]


def contains_any(text, keywords):
    text = (text or "").lower()
    return any(k in text for k in keywords)


def values_match(cls, attr, val_a, val_b, text_a, text_b):
    if is_not_mentioned(val_a) or is_not_mentioned(val_b):
        return "N/A"

    if val_a == val_b:
        return True

    if cls == "tumor_location" and attr == "location":
        return ngram_partial_match(text_a, text_b, n=1)

    return False


def compute_difference(cls, attr, val_a, val_b):
    if cls == "midline_shift" and attr == "shift":
        try:
            return float(val_a["value"]) - float(val_b["value"])
        except Exception:
            return None

    if cls == "number_of_lesions" and attr == "count":
        try:
            return float(val_a) - float(val_b)
        except Exception:
            return None

    return None


# ============================================================
# Adapter: BTReport metadata → LangExtract-style extractions
# ============================================================

def metadata_to_extractions(obj: Dict[str, Any]) -> Dict[str, Any]:
    text = obj.get("Text Report", "")
    extractions = []

    if "max_shift_mm" in obj:
        extractions.append({
            "extraction_class": "midline_shift",
            "attributes": {
                "shift": {"value": obj["max_shift_mm"], "unit": "mm"}
            },
            "extraction_text": text
        })

    if "Number of lesions" in obj:
        extractions.append({
            "extraction_class": "number_of_lesions",
            "attributes": {
                "count": obj["Number of lesions"]
            },
            "extraction_text": text
        })

    if "Tumor Location" in obj:
        extractions.append({
            "extraction_class": "tumor_location",
            "attributes": {
                "location": obj["Tumor Location"]
            },
            "extraction_text": text
        })

    if "Side of Tumor Epicenter" in obj:
        extractions.append({
            "extraction_class": "side_of_tumor_epicenter",
            "attributes": {
                "side": obj["Side of Tumor Epicenter"]
            },
            "extraction_text": text
        })

    if "Cortical involvement" in obj:
        extractions.append({
            "extraction_class": "cortical_involvement",
            "attributes": {
                "involvement": obj["Cortical involvement"]
            },
            "extraction_text": text
        })

    if "Ependymal (ventricular) Invasion" in obj:
        extractions.append({
            "extraction_class": "ventricular_invasion",
            "attributes": {
                "invasion": obj["Ependymal (ventricular) Invasion"]
            },
            "extraction_text": text
        })

    if "Enlarged Ventricles" in obj:
        extractions.append({
            "extraction_class": "ventricle_enlargement",
            "attributes": {
                "enlargement": obj["Enlarged Ventricles"]
            },
            "extraction_text": text
        })

    return {"extractions": extractions}


# ============================================================
# Core comparison
# ============================================================

def compare_extractions(a: dict, b: dict):

    def index_by_class(extractions):
        by = defaultdict(list)
        for ex in extractions or []:
            by[ex["extraction_class"]].append(ex)
        return by

    a_by = index_by_class(a.get("extractions", []))
    b_by = index_by_class(b.get("extractions", []))

    classes = {
        "midline_shift",
        "number_of_lesions",
        "tumor_location",
        "side_of_tumor_epicenter",
        "cortical_involvement",
        "ventricular_invasion",
        "ventricle_enlargement",
    }

    out = {}

    for cls in classes:
        out[cls] = {}

        ex_a = a_by.get(cls, [None])[0]
        ex_b = b_by.get(cls, [None])[0]

        attrs_a = (ex_a or {}).get("attributes", {})
        attrs_b = (ex_b or {}).get("attributes", {})
        text_a = (ex_a or {}).get("extraction_text", "")
        text_b = (ex_b or {}).get("extraction_text", "")

        for attr in set(attrs_a) | set(attrs_b):
            val_a = attrs_a.get(attr)
            val_b = attrs_b.get(attr)

            entry = {
                "a": val_a,
                "b": val_b,
                "match": values_match(cls, attr, val_a, val_b, text_a, text_b),
            }

            diff = compute_difference(cls, attr, val_a, val_b)
            if diff is not None:
                entry["difference"] = diff

            out[cls][attr] = entry

    return out


# ============================================================
# Main: run over all subjects
# ============================================================

CLINICAL_GLOB = (
    "/pscratch/sd/j/jehr/MSFT/BTReport/btreport/evaluation/"
    "intermediate_feature_validation/"
    "btreport_gptoss120b/llama3:70b_v1/clinical-report/"
    "extraction_results*.yaml"
)

AGG_METADATA = (
    "/pscratch/sd/j/jehr/MSFT/BTReport/btreport/evaluation/intermediate_feature_validation/aggregated_patient_metadata.yaml"
)

OUT_YAML = (
    "/pscratch/sd/j/jehr/MSFT/BTReport/btreport/evaluation/"
    "intermediate_feature_validation/"
    "extraction_type_analysis.yaml"
)

clinicals = sorted(glob.glob(CLINICAL_GLOB))
print(f"Found {len(clinicals)} clinical extraction files")

with open(AGG_METADATA, "r") as f:
    metadata = yaml.safe_load(f)

joint = {
    "subjects": {},
    "summary": defaultdict(lambda: defaultdict(lambda: {
        "count": 0,
        "match": {"true": 0, "partial": 0, "false": 0, "na": 0},
        "numeric": {"n": 0, "sum_diff": 0.0, "sum_abs_diff": 0.0},
    }))
}

for clin_path in clinicals:
    fname = os.path.basename(clin_path)
    subject_id = fname.replace("extraction_results_", "").replace(".yaml", "")

    if subject_id not in metadata:
        print(f"[WARN] Missing metadata for {subject_id}")
        continue

    with open(clin_path, "r") as f:
        clinical = yaml.safe_load(f)

    predicted = metadata_to_extractions(metadata[subject_id])

    comp = compare_extractions(clinical, predicted)
    joint["subjects"][subject_id] = comp

    for cls, attrs in comp.items():
        for attr, e in attrs.items():
            s = joint["summary"][cls][attr]
            s["count"] += 1

            m = e["match"]
            if m is True:
                s["match"]["true"] += 1
            elif m == "Partial":
                s["match"]["partial"] += 1
            elif m in ("N/A", None):
                s["match"]["na"] += 1
            else:
                s["match"]["false"] += 1

            if "difference" in e and isinstance(e["difference"], (int, float)):
                d = float(e["difference"])
                s["numeric"]["n"] += 1
                s["numeric"]["sum_diff"] += d
                s["numeric"]["sum_abs_diff"] += abs(d)

# ============================================================
# Finalize metrics
# ============================================================

for cls, attrs in joint["summary"].items():
    for attr, s in attrs.items():
        valid = s["match"]["true"] + s["match"]["partial"] + s["match"]["false"]

        if valid > 0:
            s["metrics"] = {
                "accuracy_strict": s["match"]["true"] / valid,
                "accuracy_soft": (s["match"]["true"] + s["match"]["partial"]) / valid,
                "omission_rate": s["match"]["na"] / s["count"],
            }
        else:
            s["metrics"] = None

        if s["numeric"]["n"] > 0:
            s["numeric"]["mean_diff"] = s["numeric"]["sum_diff"] / s["numeric"]["n"]
            s["numeric"]["mean_abs_diff"] = s["numeric"]["sum_abs_diff"] / s["numeric"]["n"]
            del s["numeric"]["sum_diff"]
            del s["numeric"]["sum_abs_diff"]
        else:
            del s["numeric"]

joint["summary"] = {
    cls: dict(attrs) for cls, attrs in joint["summary"].items()
}

with open(OUT_YAML, "w") as f:
    yaml.safe_dump(joint, f, sort_keys=False)

print(f"Saved extraction-type analysis to {OUT_YAML}")
