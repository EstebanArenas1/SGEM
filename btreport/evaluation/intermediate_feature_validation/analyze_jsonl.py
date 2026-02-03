# import json
# from collections import defaultdict
# from pprint import pformat
# import glob
# import json
# from pathlib import Path

# def aggregate_extraction_attribute_comparison(
#     clinical_files,
#     predicted_files,
#     output_json,
# ):
#     """
#     Aggregate attribute-level comparisons across subjects.

#     Output schema (per extraction_class):
#         total
#         exact_match
#         mismatch
#         missing_predicted
#         missing_clinical
#         examples[]
#     """

#     def load_by_class(path):
#         with open(path, "r") as f:
#             obj = json.loads(f.readline())

#         by_class = defaultdict(list)
#         for ex in obj.get("extractions", []):
#             by_class[ex["extraction_class"]].append(ex)
#         return by_class

#     summary = defaultdict(lambda: {
#         "total": 0,
#         "exact_match": 0,
#         "mismatch": 0,
#         "missing_predicted": 0,
#         "missing_clinical": 0,
#         "examples": [],
#     })

#     for clin_path, pred_path in zip(clinical_files, predicted_files):
#         subject_id = Path(clin_path).stem.replace("extraction_results_", "")

#         clinical = load_by_class(clin_path)
#         predicted = load_by_class(pred_path)

#         all_classes = set(clinical) | set(predicted)
        
#         raise ValueError(all_classes)

#         for cls in all_classes:
#             clin_list = clinical.get(cls, [])
#             pred_list = predicted.get(cls, [])
            
#             max_len = max(len(clin_list), len(pred_list))

#             for i in range(max_len):
#                 summary[cls]["total"] += 1

#                 clin = clin_list[i] if i < len(clin_list) else None
#                 pred = pred_list[i] if i < len(pred_list) else None

#                 if clin is None:
#                     summary[cls]["missing_clinical"] += 1
#                     summary[cls]["examples"].append({
#                         "subject": subject_id,
#                         "type": "missing_clinical",
#                         "predicted": pred.get("attributes") if pred else None,
#                     })
#                     continue

#                 if pred is None:
#                     summary[cls]["missing_predicted"] += 1
#                     summary[cls]["examples"].append({
#                         "subject": subject_id,
#                         "type": "missing_predicted",
#                         "clinical": clin.get("attributes"),
#                     })
#                     continue

#                 if clin.get("attributes") == pred.get("attributes"):
#                     summary[cls]["exact_match"] += 1
#                 else:
#                     summary[cls]["mismatch"] += 1
#                     summary[cls]["examples"].append({
#                         "subject": subject_id,
#                         "type": "attribute_mismatch",
#                         "clinical": clin.get("attributes"),
#                         "predicted": pred.get("attributes"),
#                     })

#     with open(output_json, "w") as f:
#         json.dump(summary, f, indent=2)


# if __name__ == '__main__':
#     clinicals = sorted(glob.glob("/pscratch/sd/j/jehr/MSFT/BTReport/btreport/evaluation/intermediate_feature_validation/btreport_gptoss120b/llama3:70b/clinical-report/extraction_results*.jsonl"))

#     predicteds = sorted(glob.glob("/pscratch/sd/j/jehr/MSFT/BTReport/btreport/evaluation/intermediate_feature_validation/btreport_gptoss120b/llama3:70b/predicted-report/extraction_results*.jsonl"))

#     aggregate_extraction_attribute_comparison(
#         clinical_files=clinicals,
#         predicted_files=predicteds,
#         output_json="aggregated_attribute_comparison.json",
#     )


import json
from collections import defaultdict
import glob
from pathlib import Path
import re


# -----------------------------
# Configuration
# -----------------------------

NUMERIC_CLASSES = {
    "midline_shift",
    "tumor_dimensions",
}


# def extract_numeric(attr):
#     """
#     Recursively extract a float from nested attribute structures.

#     Handles:
#       - float / int
#       - numeric strings
#       - nested dicts like {"shift": {"value": "0", "unit": "mm"}}
#       - dicts with keys: value, mm, cm
#     """
#     if attr is None:
#         return None

#     # direct numeric
#     if isinstance(attr, (int, float)):
#         return float(attr)

#     # numeric string
#     if isinstance(attr, str):
#         m = re.search(r"[-+]?\d*\.?\d+", attr)
#         if m:
#             return float(m.group())
#         return None

#     # dict: search common keys first, then recurse
#     if isinstance(attr, dict):
#         # preferred numeric keys
#         for k in ["value", "mm", "cm"]:
#             if k in attr:
#                 return extract_numeric(attr[k])

#         # otherwise recurse through values
#         for v in attr.values():
#             val = extract_numeric(v)
#             if val is not None:
#                 return val

#     return None
def collapse_by_class(cls, extractions):
    """
    Collapse mention-level extractions into a single subject-level value
    using class-specific clinical rules.
    """
    if not extractions:
        return None

    # -------------------------------------------------
    # MIDLINE SHIFT (numeric, take max abs in mm)
    # -------------------------------------------------
    if cls == "midline_shift":
        vals = []
        for ex in extractions:
            v = extract_numeric(ex.get("attributes"))
            if v is not None:
                vals.append(abs(v))

        if not vals:
            return None

        return {
            "attributes": {
                "shift_mm": max(vals)
            }
        }

    # -------------------------------------------------
    # TUMOR DIMENSIONS (dominant lesion)
    # -------------------------------------------------
    if cls == "tumor_dimensions":
        max_extent = None

        for ex in extractions:
            attrs = ex.get("attributes", {})
            for k in ["axial", "craniocaudal"]:
                v = extract_numeric(attrs.get(k))
                if v is not None:
                    max_extent = max(max_extent or 0.0, v)

        if max_extent is None:
            return None

        return {
            "attributes": {
                "max_dimension_mm": max_extent
            }
        }

    # -------------------------------------------------
    # TUMOR LOCATION (most specific, allow multi-lobe)
    # -------------------------------------------------
    if cls == "tumor_location":
        locations = []

        for ex in extractions:
            loc = ex.get("attributes", {}).get("location")
            if isinstance(loc, list):
                locations.extend(loc)
            elif isinstance(loc, str):
                locations.append(loc)

        if not locations:
            return None

        # choose most specific (longest)
        best = max(locations, key=lambda x: len(x))

        return {
            "attributes": {
                "location": best
            }
        }

    # -------------------------------------------------
    # SIDE OF TUMOR EPICENTER
    # -------------------------------------------------
    if cls == "side_of_tumor_epicenter":
        sides = set(
            ex.get("attributes", {}).get("side")
            for ex in extractions
            if ex.get("attributes", {}).get("side")
        )

        if "bilateral" in sides or {"left", "right"} <= sides:
            side = "bilateral"
        elif "left" in sides:
            side = "left"
        elif "right" in sides:
            side = "right"
        else:
            side = "unknown"

        return {
            "attributes": {
                "side": side
            }
        }

    # -------------------------------------------------
    # VENTRICULAR EFFACEMENT (severity dominates)
    # -------------------------------------------------
    if cls == "ventricular_effacement":
        priority = {
            "": 0,
            "unknown": 0,
            "no": 1,
            "partial": 2,
            "yes": 3,
            "mild": 2,
            "similar": 2,
            "mild herniation": 3,
        }

        best = None
        best_score = -1

        for ex in extractions:
            eff = ex.get("attributes", {}).get("effacement", "")
            score = priority.get(eff, 0)
            if score > best_score:
                best = ex
                best_score = score

        return best

    # -------------------------------------------------
    # VENTRICLE SYMMETRY
    # -------------------------------------------------
    if cls == "ventricle_symmetry":
        priority = {
            "": 0,
            "unknown": 0,
            "yes": 1,
            "no": 2,
        }

        best = None
        best_score = -1

        for ex in extractions:
            sym = ex.get("attributes", {}).get("symmetry", "")
            score = priority.get(sym, 0)
            if score > best_score:
                best = ex
                best_score = score

        return best

    # -------------------------------------------------
    # VENTRICLE ENLARGEMENT
    # -------------------------------------------------
    if cls == "ventricle_enlargement":
        priority = {
            "": 0,
            "unknown": 0,
            "no": 1,
            "yes": 2,
        }

        best = None
        best_score = -1

        for ex in extractions:
            val = ex.get("attributes", {}).get("enlargement", "")
            score = priority.get(val, 0)
            if score > best_score:
                best = ex
                best_score = score

        return best

    # -------------------------------------------------
    # VENTRICULAR INVASION
    # -------------------------------------------------
    if cls == "ventricular_invasion":
        priority = {
            "": 0,
            "unknown": 0,
            "no": 1,
            "yes": 2,
        }

        best = None
        best_score = -1

        for ex in extractions:
            val = ex.get("attributes", {}).get("invasion", "")
            score = priority.get(val, 0)
            if score > best_score:
                best = ex
                best_score = score

        return best

    # -------------------------------------------------
    # NUMBER OF LESIONS (take max)
    # -------------------------------------------------
    if cls == "number_of_lesions":
        counts = []
        for ex in extractions:
            c = ex.get("attributes", {}).get("count")
            if isinstance(c, str):
                if c.isdigit():
                    counts.append(int(c))
                elif c.startswith(">"):
                    counts.append(2)
            elif isinstance(c, int):
                counts.append(c)

        if not counts:
            return None

        return {
            "attributes": {
                "count": max(counts)
            }
        }

    # -------------------------------------------------
    # CORTICAL INVOLVEMENT
    # -------------------------------------------------
    if cls == "cortical_involvement":
        for ex in extractions:
            if ex.get("attributes", {}).get("involvement") == "yes":
                return ex
        return extractions[0]

    # -------------------------------------------------
    # LESION CHARACTERISTICS (union)
    # -------------------------------------------------
    if cls == "lesion_characteristics":
        features = set()
        for ex in extractions:
            feats = ex.get("attributes", {}).get("spectra_features", [])
            for f in feats:
                features.add(f)

        if not features:
            return None

        return {
            "attributes": {
                "spectra_features": sorted(features)
            }
        }

    # -------------------------------------------------
    # FALLBACK
    # -------------------------------------------------
    return extractions[0]


def extract_numeric(attr, *, threshold=None, zero_below=False):
    """
    Recursively extract a numeric value and normalize to millimeters (mm).

    Handles:
      - float / int
      - numeric strings
      - {"value": x, "unit": "mm" | "cm"}
      - {"mm": x} or {"cm": x}
      - arbitrarily nested dicts

    Optional:
      - threshold (float): threshold in mm
      - zero_below (bool): if True, |x| < threshold → 0
    """
    if attr is None:
        return None

    val = None
    unit = None

    # -----------------------------
    # Direct numeric
    # -----------------------------
    if isinstance(attr, (int, float)):
        val = float(attr)
        unit = "mm"

    # -----------------------------
    # Numeric string
    # -----------------------------
    elif isinstance(attr, str):
        m = re.search(r"[-+]?\d*\.?\d+", attr)
        if m:
            val = float(m.group())
            unit = "mm"

    # -----------------------------
    # Dict handling (unit-aware)
    # -----------------------------
    elif isinstance(attr, dict):

        # Case 1: explicit value + unit
        if "value" in attr:
            val = extract_numeric(attr["value"])
            unit = attr.get("unit", "mm")

        # Case 2: unit-encoded key
        elif "mm" in attr:
            val = extract_numeric(attr["mm"])
            unit = "mm"

        elif "cm" in attr:
            val = extract_numeric(attr["cm"])
            unit = "cm"

        # Case 3: recurse arbitrarily
        else:
            for v in attr.values():
                val = extract_numeric(v)
                if val is not None:
                    unit = "mm"
                    break

    if val is None:
        return None

    # -----------------------------
    # Unit normalization
    # -----------------------------
    if unit == "cm":
        val *= 10.0  # cm → mm

    # -----------------------------
    # Thresholding logic (mm)
    # -----------------------------
    if threshold is not None and zero_below:
        if abs(val) < threshold:
            return 0.0

    return val


def aggregate_extraction_attribute_comparison(
    clinical_files,
    predicted_files,
    output_json,
):
    """
    Aggregate attribute-level comparisons across subjects.

    For categorical classes:
        - exact match / mismatch

    For numeric classes:
        - mean error (bias)
        - standard deviation of error

    Additional for midline_shift:
        - mean / std error ignoring zero clinical MLS cases
    """

    def load_by_class(path):
        with open(path, "r") as f:
            obj = json.loads(f.readline())

        by_class = defaultdict(list)
        for ex in obj.get("extractions", []):
            by_class[ex["extraction_class"]].append(ex)
        return by_class

    summary = defaultdict(lambda: {
        "total": 0,
        "exact_match": 0,
        "mismatch": 0,
        "missing_predicted": 0,
        "missing_clinical": 0,

        # numeric accumulators (all cases)
        "numeric_count": 0,
        "signed_error_sum": 0.0,
        "squared_error_sum": 0.0,

        # MLS-only: non-zero clinical cases
        "numeric_count_nonzero": 0,
        "signed_error_sum_nonzero": 0.0,
        "squared_error_sum_nonzero": 0.0,

        "examples": [],
    })

    for clin_path, pred_path in zip(clinical_files, predicted_files):
        subject_id = Path(clin_path).stem.replace("extraction_results_", "")

        clinical = load_by_class(clin_path)
        predicted = load_by_class(pred_path)

        all_classes = set(clinical) | set(predicted)
    
        all_classes = {'side_of_tumor_epicenter', 'tumor_location', 'ventricle_symmetry', 'midline_shift', 'number_of_lesions', 'ventricular_effacement', 'ventricular_invasion', 'tumor_dimensions', 'ventricle_enlargement', 'cortical_involvement', }

        for cls in all_classes:

            clin_list = collapse_by_class(cls, clinical.get(cls, []))
            pred_list = collapse_by_class(cls, predicted.get(cls, []))

            # clin_list = clinical.get(cls, [])
            # pred_list = predicted.get(cls, [])

            print(clin_list)

            max_len = max(len(clin_list), len(pred_list))
            
            # if len(clin_list) > 1:
            #     print('**-**'*30)
            #     print(clin_list)
            #     continue
            # else:
            #     continue

            for i in range(max_len):
                summary[cls]["total"] += 1

                clin = clin_list[i] if i < len(clin_list) else None
                pred = pred_list[i] if i < len(pred_list) else None

                if clin is None:
                    summary[cls]["missing_clinical"] += 1
                    summary[cls]["examples"].append({
                        "subject": subject_id,
                        "type": "missing_clinical",
                        "predicted": pred.get("attributes") if pred else None,
                    })
                    continue

                if pred is None:
                    summary[cls]["missing_predicted"] += 1
                    summary[cls]["examples"].append({
                        "subject": subject_id,
                        "type": "missing_predicted",
                        "clinical": clin.get("attributes"),
                    })
                    continue

                clin_attr = clin.get("attributes")
                pred_attr = pred.get("attributes")

                # -----------------------------
                # Numeric classes
                # -----------------------------
                if cls in NUMERIC_CLASSES:
                    if cls == "midline_shift":
                        clin_val = extract_numeric(
                            clin_attr, threshold=5.0, zero_below=True
                        )
                        pred_val = extract_numeric(
                            pred_attr, threshold=5.0, zero_below=True
                        )
                    else:
                        clin_val = extract_numeric(clin_attr)
                        pred_val = extract_numeric(pred_attr)

                    if clin_val is None or pred_val is None:
                        summary[cls]["mismatch"] += 1
                        summary[cls]["examples"].append({
                            "subject": subject_id,
                            "type": "numeric_parse_failure",
                            "clinical": clin_attr,
                            "predicted": pred_attr,
                        })
                        continue

                    err = pred_val - clin_val

                    # all numeric cases
                    summary[cls]["numeric_count"] += 1
                    summary[cls]["signed_error_sum"] += err
                    summary[cls]["squared_error_sum"] += err ** 2

                    # MLS non-zero-only
                    if cls == "midline_shift" and clin_val != 0:
                        summary[cls]["numeric_count_nonzero"] += 1
                        summary[cls]["signed_error_sum_nonzero"] += err
                        summary[cls]["squared_error_sum_nonzero"] += err ** 2

                    summary[cls]["examples"].append({
                        "subject": subject_id,
                        "type": "numeric_comparison",
                        "clinical_value": clin_val,
                        "predicted_value": pred_val,
                        "error": err,
                    })

                # -----------------------------
                # Categorical classes
                # -----------------------------
                else:
                    if clin_attr == pred_attr:
                        summary[cls]["exact_match"] += 1
                    else:
                        summary[cls]["mismatch"] += 1
                        summary[cls]["examples"].append({
                            "subject": subject_id,
                            "type": "attribute_mismatch",
                            "clinical": clin_attr,
                            "predicted": pred_attr,
                        })

    # -----------------------------
    # Finalize numeric statistics
    # -----------------------------
    for cls, stats in summary.items():
        n = stats.get("numeric_count", 0)
        if n > 0:
            mean_err = stats["signed_error_sum"] / n
            var = (stats["squared_error_sum"] / n) - (mean_err ** 2)
            var = max(var, 0.0)

            stats["mean_error"] = mean_err
            stats["std_error"] = var ** 0.5

            del stats["signed_error_sum"]
            del stats["squared_error_sum"]

        # MLS non-zero-only stats
        if cls == "midline_shift":
            nz = stats.get("numeric_count_nonzero", 0)
            if nz > 0:
                mean_err_nz = stats["signed_error_sum_nonzero"] / nz
                var_nz = (stats["squared_error_sum_nonzero"] / nz) - (mean_err_nz ** 2)
                var_nz = max(var_nz, 0.0)

                stats["mean_error_nonzero"] = mean_err_nz
                stats["std_error_nonzero"] = var_nz ** 0.5

            del stats["signed_error_sum_nonzero"]
            del stats["squared_error_sum_nonzero"]

    with open(output_json, "w") as f:
        json.dump(summary, f, indent=2)

    # -----------------------------
    # Console summary
    # -----------------------------
    print("\n=== Aggregated Extraction Summary ===")

    for cls, stats in summary.items():
        if stats["total"] <= 100:
            continue

        print(f"\n[{cls}]")
        print(f"  total: {stats['total']}")
        print(f"  exact_match: {stats['exact_match']}")
        print(f"  mismatch: {stats['mismatch']}")
        print(f"  missing_predicted: {stats['missing_predicted']}")
        print(f"  missing_clinical: {stats['missing_clinical']}")

        if stats.get("numeric_count", 0) > 0:
            print(f"  numeric_count: {stats['numeric_count']}")
            print(f"  mean_error: {stats['mean_error']:.3f}")
            print(f"  std_error: {stats['std_error']:.3f}")

        if cls == "midline_shift" and stats.get("numeric_count_nonzero", 0) > 0:
            print(f"  numeric_count_nonzero: {stats['numeric_count_nonzero']}")
            print(f"  mean_error_nonzero: {stats['mean_error_nonzero']:.3f}")
            print(f"  std_error_nonzero: {stats['std_error_nonzero']:.3f}")

# def aggregate_extraction_attribute_comparison(
#     clinical_files,
#     predicted_files,
#     output_json,
# ):
#     """
#     Aggregate attribute-level comparisons across subjects.

#     For categorical classes:
#         - exact match / mismatch

#     For numeric classes:
#         - mean error (bias)
#         - standard deviation of error
#     """

#     def load_by_class(path):
#         with open(path, "r") as f:
#             obj = json.loads(f.readline())

#         by_class = defaultdict(list)
#         for ex in obj.get("extractions", []):
#             by_class[ex["extraction_class"]].append(ex)
#         return by_class

#     summary = defaultdict(lambda: {
#         "total": 0,
#         "exact_match": 0,
#         "mismatch": 0,
#         "missing_predicted": 0,
#         "missing_clinical": 0,

#         # numeric-only accumulators
#         "numeric_count": 0,
#         "signed_error_sum": 0.0,
#         "squared_error_sum": 0.0,

#         "examples": [],
#     })

#     for clin_path, pred_path in zip(clinical_files, predicted_files):
#         subject_id = Path(clin_path).stem.replace("extraction_results_", "")

#         clinical = load_by_class(clin_path)
#         predicted = load_by_class(pred_path)

#         all_classes = set(clinical) | set(predicted)

#         for cls in all_classes:
#             clin_list = clinical.get(cls, [])
#             pred_list = predicted.get(cls, [])

#             max_len = max(len(clin_list), len(pred_list))

#             for i in range(max_len):
#                 summary[cls]["total"] += 1

#                 clin = clin_list[i] if i < len(clin_list) else None
#                 pred = pred_list[i] if i < len(pred_list) else None

#                 if clin is None:
#                     summary[cls]["missing_clinical"] += 1
#                     summary[cls]["examples"].append({
#                         "subject": subject_id,
#                         "type": "missing_clinical",
#                         "predicted": pred.get("attributes") if pred else None,
#                     })
#                     continue

#                 if pred is None:
#                     summary[cls]["missing_predicted"] += 1
#                     summary[cls]["examples"].append({
#                         "subject": subject_id,
#                         "type": "missing_predicted",
#                         "clinical": clin.get("attributes"),
#                     })
#                     continue

#                 clin_attr = clin.get("attributes")
#                 pred_attr = pred.get("attributes")

#                 # -----------------------------
#                 # Numeric classes
#                 # -----------------------------
#                 if cls in NUMERIC_CLASSES:
#                     if cls == "midline_shift":
#                         clin_val = extract_numeric(clin_attr, threshold=5.0, zero_below=True)
#                         pred_val = extract_numeric(pred_attr, threshold=5.0, zero_below=True)
#                     else:
#                         clin_val = extract_numeric(clin_attr)
#                         pred_val = extract_numeric(pred_attr)
#                     # clin_val = extract_numeric(clin_attr)
#                     # pred_val = extract_numeric(pred_attr)

#                     if clin_val is None or pred_val is None:
#                         summary[cls]["mismatch"] += 1
#                         summary[cls]["examples"].append({
#                             "subject": subject_id,
#                             "type": "numeric_parse_failure",
#                             "clinical": clin_attr,
#                             "predicted": pred_attr,
#                         })
#                         continue

#                     err = pred_val - clin_val
#                     summary[cls]["numeric_count"] += 1
#                     summary[cls]["signed_error_sum"] += err
#                     summary[cls]["squared_error_sum"] += err ** 2

#                     summary[cls]["examples"].append({
#                         "subject": subject_id,
#                         "type": "numeric_comparison",
#                         "clinical_value": clin_val,
#                         "predicted_value": pred_val,
#                         "error": err,
#                     })

#                 # -----------------------------
#                 # Categorical classes
#                 # -----------------------------
#                 else:
#                     if clin_attr == pred_attr:
#                         summary[cls]["exact_match"] += 1
#                     else:
#                         summary[cls]["mismatch"] += 1
#                         summary[cls]["examples"].append({
#                             "subject": subject_id,
#                             "type": "attribute_mismatch",
#                             "clinical": clin_attr,
#                             "predicted": pred_attr,
#                         })

#     # -----------------------------
#     # Finalize numeric statistics
#     # -----------------------------
#     for cls, stats in summary.items():
#         n = stats.get("numeric_count", 0)
#         if n > 0:
#             mean_err = stats["signed_error_sum"] / n
#             variance = (stats["squared_error_sum"] / n) - (mean_err ** 2)
#             variance = max(variance, 0.0)  # numerical safety

#             stats["mean_error"] = mean_err
#             stats["std_error"] = variance ** 0.5

#             # remove raw accumulators from output
#             del stats["signed_error_sum"]
#             del stats["squared_error_sum"]

#     with open(output_json, "w") as f:
#         json.dump(summary, f, indent=2)

#     print("\n=== Aggregated Extraction Summary ===")

#     for cls, stats in summary.items():
#         if not stats['total'] > 100:
#             continue
#         print(f"\n[{cls}]")
#         print(f"  total: {stats['total']}")
#         print(f"  exact_match: {stats['exact_match']}")
#         print(f"  mismatch: {stats['mismatch']}")
#         print(f"  missing_predicted: {stats['missing_predicted']}")
#         print(f"  missing_clinical: {stats['missing_clinical']}")

#         if stats.get("numeric_count", 0) > 0:
#             print(f"  numeric_count: {stats['numeric_count']}")
#             print(f"  mean_error: {stats.get('mean_error'):.3f}")
#             print(f"  std_error: {stats.get('std_error'):.3f}")


import json
import yaml

def json_file_to_yaml(json_path: str, yaml_path: str):
    """
    Convert a JSON file to a YAML file.
    """
    with open(json_path, "r") as f:
        data = json.load(f)

    with open(yaml_path, "w") as f:
        yaml.safe_dump(
            data,
            f,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )


if __name__ == "__main__":
    clinicals = sorted(glob.glob(
        "/pscratch/sd/j/jehr/MSFT/BTReport/btreport/evaluation/intermediate_feature_validation/"
        "btreport_gptoss120b/llama3:70b/clinical-report/extraction_results*.jsonl"
    ))

    predicteds = sorted(glob.glob(
        "/pscratch/sd/j/jehr/MSFT/BTReport/btreport/evaluation/intermediate_feature_validation/"
        "btreport_gptoss120b_deepmedic/llama3:70b/predicted-report/extraction_results*.jsonl"
    ))

    # predicteds = sorted(glob.glob(
    #     "/pscratch/sd/j/jehr/MSFT/BTReport/btreport/evaluation/intermediate_feature_validation/autorg_brain/llama3:70b/predicted-report/extraction_results*.jsonl"
    # ))

    # aggregate_extraction_attribute_comparison(
    #     clinical_files=clinicals,
    #     predicted_files=predicteds,
    #     output_json="aggregated_attribute_comparison.json",
    # )

    import json
    import yaml

    for f in clinicals:

        json_file_to_yaml(json_path=f, yaml_path=f.replace('.jsonl', '.yaml'))
        # # 1. Read from the JSON file and load into a Python dictionary
        # with open(f, 'r') as json_file:
        #     python_dict = json.load(json_file)

        # # 2. Write the Python dictionary to a YAML file
        # with open(f.replace('.jsonl', '.yaml'), 'w') as yaml_file:
        #     yaml.dump(python_dict, yaml_file, default_flow_style=False)

        # print(f"Successfully converted {f} to 'yaml'.")


    for f in predicteds:

        # 1. Read from the JSON file and load into a Python dictionary
        json_file_to_yaml(json_path=f, yaml_path=f.replace('.jsonl', '.yaml'))
