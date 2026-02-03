import yaml, glob
from collections import defaultdict
from typing import Dict, Any
from pprint import pprint
import numpy as np
import os
from collections import defaultdict

import re

def is_not_mentioned(val) -> bool:
    if val is None:
        return True
    if isinstance(val, str) and val.strip().lower() in {
        "not mentioned",
        "not reported",
        "unknown",
        "n/a",
    }:
        return True
    return False

def normalize_tokens(text: str):
    return re.findall(r"[a-z]+", text.lower())

def word_ngrams(tokens, n):
    return {
        tuple(tokens[i:i+n])
        for i in range(len(tokens) - n + 1)
    }

def ngram_partial_match(a: str, b: str, n: int = 2, min_overlap: int = 1) -> bool:
    if not a or not b:
        return False

    ta = normalize_tokens(a)
    tb = normalize_tokens(b)

    if len(ta) < n or len(tb) < n:
        return False

    if len(word_ngrams(ta, n) & word_ngrams(tb, n)) >= min_overlap:
        return "Partial"
    else:
        return False

import re

def extract_numeric_cm(x):
    """
    Extract numeric value and convert to centimeters.
    Assumptions:
      - default unit is mm if unit is missing
      - supported units: mm, cm
    """
    if x is None:
        return None

    # already numeric → assume mm
    if isinstance(x, (int, float)):
        return float(x) / 10.0

    # dict: {"value": ..., "unit": "..."}
    if isinstance(x, dict):
        val = extract_numeric_cm(x.get("value"))
        unit = (x.get("unit") or "").lower()

        if unit in ("cm", "centimeter", "centimeters"):
            return val
        if unit in ("mm", "millimeter", "millimeters", ""):
            return val

        # unknown unit → refuse silently
        return None

    # string: "4.5 cm", "30mm"
    if isinstance(x, str):
        m = re.search(r"([-+]?\d*\.?\d+)\s*(mm|cm)?", x.lower())
        if not m:
            return None

        val = float(m.group(1))
        unit = m.group(2)

        if unit == "cm":
            return val
        # default mm
        return val / 10.0

    return None

def compute_volume(attrs):
    """
    Volume proxy = axial * craniocaudal
    Units: cm² (not true volume)
    """
    if not isinstance(attrs, dict):
        return None

    axial_cm = extract_numeric_cm(attrs.get("axial"))
    if axial_cm is None:
        return None

    cc_cm = extract_numeric_cm(attrs.get("craniocaudal"))
    if cc_cm is None:
        cc_cm = 1.0  # per your rule

    return axial_cm * cc_cm




def contains_any(text, keywords):
    text = (text or "").lower()
    return any(k in text for k in keywords)
VENTRICLE_KEYWORDS = ["ventricle", "ventricular", "horn", 'ependymal']


def values_match(cls, attr, val_a, val_b, text_a, text_b):
    # missing values never match
    if is_not_mentioned(val_a) or is_not_mentioned(val_b):
        return 'N/A'   # 

    if val_a == val_b:
        return True

    if cls == "ventricular_effacement":
        if attr == "effacement":
            return val_a == val_b

        if attr == "ventricle":
            # If one side doesn't actually mention ventricles,
            if not contains_any(text_a, VENTRICLE_KEYWORDS) or not contains_any(text_b, VENTRICLE_KEYWORDS):
                return "Incorrect Parsing"
            return val_a == val_b

    if cls in {"side_of_tumor_epicenter"} and attr == "side":
        if isinstance(val_a, list)  or  isinstance(val_b, list):
            print("side_of_tumor_epicenter is a list")
            return 'N/A'
        if contains_any(val_a, 'midline') or contains_any(val_b, 'midline'):
            return 'N/A'
        else:
            return val_a == val_b

    # ---- partial match logic ----
    if cls in {"tumor_location"} and attr == "location":
        return ngram_partial_match(text_a, text_b, n=1)

    return False

import re

def compute_difference(cls, attr, val_a, val_b):
    """
    Compute signed numeric difference (a - b).

    Units:
      - midline_shift.shift: mm
      - tumor_dimensions.axial: area difference (cm^2)
      - tumor_dimensions.craniocaudal: length difference (cm)
    """

    def to_mm(value, unit):
        value = float(value)
        unit = unit.lower()
        if unit == "mm":
            return value
        if unit == "cm":
            return value * 10.0
        return None

    def to_cm(value, unit):
        value = float(value)
        unit = unit.lower()
        if unit == "cm":
            return value
        if unit == "mm":
            return value / 10.0
        return None

    # ---------------- Midline shift (mm) ----------------
    if cls == "midline_shift" and attr == "shift":
        if not isinstance(val_a, dict) or not isinstance(val_b, dict):
            return None
        try:
            a_mm = to_mm(val_a.get("value"), val_a.get("unit"))
            b_mm = to_mm(val_b.get("value"), val_b.get("unit"))
            if a_mm < 5.0:
                a_mm = 0.0
            if a_mm is None or b_mm is None:
                return None
            return a_mm - b_mm
        except Exception:
            return None

    if cls == "number_of_lesions" and isinstance(val_a, str) and isinstance(val_b, str):
        try:
            a = float(re.search(r"\d+(?:\.\d+)?", str(val_a)).group())
            b = float(re.search(r"\d+(?:\.\d+)?", str(val_b)).group())
            return float(a - b)
        except Exception:
            return None

    # ---------------- Tumor dimensions ----------------
    if cls == "tumor_dimensions" and isinstance(val_a, str) and isinstance(val_b, str):
        nums_a = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", val_a)]
        nums_b = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", val_b)]

        if not nums_a or not nums_b:
            return None

        unit_a = "cm" if "cm" in val_a.lower() else "mm"
        unit_b = "cm" if "cm" in val_b.lower() else "mm"

        try:
            # ---- axial: area difference (cm^2) ----
            if attr == "axial" and len(nums_a) >= 2 and len(nums_b) >= 2:
                a1, a2 = to_cm(nums_a[0], unit_a), to_cm(nums_a[1], unit_a)
                b1, b2 = to_cm(nums_b[0], unit_b), to_cm(nums_b[1], unit_b)
                if None in (a1, a2, b1, b2):
                    return None
                area_a = a1 * a2      # cm^2
                area_b = b1 * b2      # cm^2
                return {
                        'value': float(np.round(area_a - area_b, 3)),
                        'unit': 'cm^2'
                    }

            # ---- craniocaudal: length difference (cm) ----
            if attr == "craniocaudal":
                a_cm = to_cm(nums_a[0], unit_a)
                b_cm = to_cm(nums_b[0], unit_b)
                if a_cm is None or b_cm is None:
                    return None
                return {
                        'value': float(np.round(a_cm - b_cm, 3)),
                        'unit': 'cm'
                    }

        except Exception:
            return None

    # ---------------- Fallback ----------------
    try:
        return float(val_a) - float(val_b)
    except Exception:
        return None
    
def compare_extraction_yamls(
    yaml_a_path: str,
    yaml_b_path: str,
):
    """
    Compare two BTReport-style extraction YAMLs.

    Returns a nested dict:
        {
          extraction_class: {
            attribute_name: {
              "a": value_or_None,
              "b": value_or_None,
              "match": bool
            }
          }
        }
    """

    def load_yaml(path):
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def index_by_class(extractions):
        by_class = defaultdict(list)
        for ex in extractions or []:
            by_class[ex.get("extraction_class")].append(ex)
        return by_class

    a = load_yaml(yaml_a_path)
    b = load_yaml(yaml_b_path)

    a_by_class = index_by_class(a.get("extractions", []))
    b_by_class = index_by_class(b.get("extractions", []))
    
    all_classes = set(a_by_class) | set(b_by_class)
    all_classes = all_classes & {'side_of_tumor_epicenter', 'tumor_location', 'ventricle_symmetry', 'midline_shift', 'number_of_lesions', 'ventricular_effacement', 'ventricular_invasion', 'tumor_dimensions', 'ventricle_enlargement', 'cortical_involvement', }


    comparison = {}

    for cls in sorted(all_classes):
        comparison[cls] = {}

        # compare laast instance only 
        ex_a = a_by_class.get(cls, [None])[0]
        ex_b = b_by_class.get(cls, [None])[0]

        attrs_a = (ex_a or {}).get("attributes") or {}
        attrs_b = (ex_b or {}).get("attributes") or {}
        extr_text_a = (ex_a or {}).get("extraction_text", {})
        extr_text_b = (ex_b or {}).get("extraction_text", {})

        if cls == "tumor_dimensions":
            vol_a = compute_volume(attrs_a)
            vol_b = compute_volume(attrs_b)

            if vol_a is not None or vol_b is not None:
                attrs_a = dict(attrs_a)  # shallow copy
                attrs_b = dict(attrs_b)
                attrs_a["volume"] = vol_a
                attrs_b["volume"] = vol_b


        all_attrs = set(attrs_a) | set(attrs_b)

        for attr in sorted(all_attrs):
            val_a = attrs_a.get(attr)
            val_b = attrs_b.get(attr)

            entry = {
                "a": val_a,
                "b": val_b,
                "match": values_match(
                            cls,
                            attr,
                            val_a,
                            val_b,
                            extr_text_a,
                            extr_text_b,
                        ),
                "extraction_text_a":extr_text_a,
                "extraction_text_b":extr_text_b,

            }

            diff = compute_difference(cls, attr, val_a, val_b)
            if diff is not None:
                entry["difference"] = diff

            comparison[cls][attr] = entry

    return comparison

if __name__ == '__main__':
    clinicals = sorted(glob.glob(
        "/pscratch/sd/j/jehr/MSFT/BTReport/btreport/evaluation/intermediate_feature_validation/"
        "btreport_gptoss120b/llama3:70b/clinical-report/extraction_results*.yaml"
    ))

    predicteds = sorted(glob.glob(
        "/pscratch/sd/j/jehr/MSFT/BTReport/btreport/evaluation/intermediate_feature_validation/"
        "btreport_gptoss120b_deepmedic/llama3:70b/predicted-report/extraction_results*.yaml"
    ))

    # predicteds = sorted(glob.glob(
    #     "/pscratch/sd/j/jehr/MSFT/BTReport/btreport/evaluation/intermediate_feature_validation/autorg_brain/llama3:70b/predicted-report/extraction_results*.jsonl"
    # ))


    joint = {
        "subjects": {},
        "summary": defaultdict(lambda: defaultdict(lambda: {
            "count": 0,
            "match": {
                "true": 0,
                "partial": 0,
                "false": 0,
                "na": 0,
            },
        "numeric": {
            "n": 0,
            "sum_diff": 0.0,
            "sum_abs_diff": 0.0,
            "sum_sq_diff": 0.0,   
            "min_diff": None,
            "max_diff": None,
        }
        }))
    }

    for pred_path in predicteds:
        fname = os.path.basename(pred_path)

        yaml_a = os.path.join(
            "/pscratch/sd/j/jehr/MSFT/BTReport/btreport/evaluation/intermediate_feature_validation/"
            "btreport_gptoss120b/llama3:70b/clinical-report/",
            fname,
        )
        yaml_b = pred_path

        if not os.path.exists(yaml_a):
            print(f"Missing clinical file for {fname}")
            continue

        print(f"Comparing:\n  A: {yaml_a}\n  B: {yaml_b}")

        comparison = compare_extraction_yamls(
            yaml_a_path=yaml_a,
            yaml_b_path=yaml_b,
        )

        subject_id = fname.replace("extraction_results_", "").replace(".yaml", "")
        joint["subjects"][subject_id] = comparison

        # ---- aggregate summary ----
        for cls, attrs in comparison.items():
            for attr, entry in attrs.items():
                s = joint["summary"][cls][attr]
                s["count"] += 1

                # ---- normalize match states ----
                match = entry.get("match")
                if match in (None, "N/A", "NA"):
                    s["match"]["na"] += 1
                elif match is True:
                    s["match"]["true"] += 1
                elif match == "Partial":
                    s["match"]["partial"] += 1
                elif match is False:
                    s["match"]["false"] += 1
                else:
                    # defensive: unknown states count as NA
                    s["match"]["na"] += 1

                # ---- numeric aggregation (if present) ----
                if "difference" in entry:
                    diff = entry["difference"]

                    # allow {'value': x, 'unit': y}
                    if isinstance(diff, dict):
                        diff = diff.get("value")

                    if isinstance(diff, (int, float)):
                        diff = float(diff)
                        s["numeric"]["n"] += 1
                        s["numeric"]["sum_diff"] += diff
                        s["numeric"]["sum_abs_diff"] += abs(diff)
                        s["numeric"]["sum_sq_diff"] += diff ** 2   # NEW

                        if s["numeric"]["min_diff"] is None or diff < s["numeric"]["min_diff"]:
                            s["numeric"]["min_diff"] = diff
                        if s["numeric"]["max_diff"] is None or diff > s["numeric"]["max_diff"]:
                            s["numeric"]["max_diff"] = diff


    for cls, attrs in joint["summary"].items():
        for attr, s in attrs.items():

            m = s["match"]
            valid = m["true"] + m["partial"] + m["false"]

            if valid > 0:
                s["metrics"] = {
                    "accuracy_strict": m["true"] / valid,
                    "accuracy_soft": (m["true"] + m["partial"]) / valid,
                    "omission_rate": m["na"] / s["count"],
                }
            else:
                s["metrics"] = None

            # ---- finalize numeric stats ----
            num = s["numeric"]
            if num["n"] > 0:
                mean = num["sum_diff"] / num["n"]
                num["mean_diff"] = mean
                num["mean_abs_diff"] = num["sum_abs_diff"] / num["n"]

                # population standard deviation
                variance = (num["sum_sq_diff"] / num["n"]) - (mean ** 2)
                num["std_diff"] = variance ** 0.5 if variance > 0 else 0.0

                del num["sum_diff"]
                del num["sum_abs_diff"]
                del num["sum_sq_diff"]
            else:
                del s["numeric"]


    joint["summary"] = {
        cls: dict(attrs)
        for cls, attrs in joint["summary"].items()
    }
    
    joint = {
        "summary": joint["summary"],
        "subjects": joint["subjects"],
    }
    out_path = (
        "/pscratch/sd/j/jehr/MSFT/BTReport/btreport/evaluation/"
        "intermediate_feature_validation/joint_comparison_llama3_deepmedic.yaml"
    )

    with open(out_path, "w") as f:
        yaml.safe_dump(
            joint,
            f,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )

    print(f"Saved joint comparison to {out_path}")
