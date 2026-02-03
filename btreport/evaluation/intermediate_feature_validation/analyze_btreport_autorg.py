import langextract as lx
import textwrap
import os, json
import re
import csv
from tqdm import tqdm
import traceback
from datetime import datetime

def load_by_acc(csv_path):
    data = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            acc = row["Acc"]
            data[acc] = {
                "MRN": row["MRN"],
                "Report": row["Report"],
            }
    return data


TOP_LEVEL = [
    "CLINICAL INDICATION",
    "TECHNIQUE",
    "CONTRAST",
    "COMPARISON",
    "FINDINGS",
    "HEAD MRA",
    "IMPRESSION"
]

SUBFINDINGS = [
    "MASS EFFECT & VENTRICLES",
    "BRAIN",
    "ENHANCEMENT",
    "VASCULAR",
    "EXTRA-AXIAL",
    "EXTRA-CRANIAL"
]

def parse_radiology_report(text):
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)

    header_regex = r"(?im)^(" + "|".join(TOP_LEVEL) + r")\s*:?\s*$"
    matches = list(re.finditer(header_regex, text))

    sections = {}
    for i,m in enumerate(matches):
        key = m.group(1).strip().upper()
        start = m.end()
        end   = matches[i+1].start() if i+1 < len(matches) else len(text)
        sections[key] = text[start:end].strip()

    if "FINDINGS" not in sections:
        found = re.search(r"(?is)FINDINGS\s*:\s*(.+?)(IMPRESSION|CONCLUSION|$)", text)
        if found:
            sections["FINDINGS"] = found.group(1).strip()
        else:
            sections["FINDINGS"] = ""  # gracefully return empty

    block = sections.get("FINDINGS", "")
    if block:
        sub_regex = r"(?im)^(" + "|".join(SUBFINDINGS) + r")\s*:?\s*"
        sub = list(re.finditer(sub_regex, block))

        for i,m in enumerate(sub):
            key = m.group(1).strip().upper()
            start = m.end()
            end   = sub[i+1].start() if i+1 < len(sub) else len(block)
            sections[key] = block[start:end].strip()

        sections["FINDINGS"] = ""  # remove summary container

    return sections



acc_dict = load_by_acc(r"/pscratch/sd/j/jehr/MSFT/BTReport_evaluation/glioma_JP (2).csv")

for sub in acc_dict.keys():
    tmp = parse_radiology_report(acc_dict[sub]["Report"])
    include_keys=['BRAIN', 'MASS EFFECT & VENTRICLES',]
    text = ["\n\n".join(f"{k}:\n{tmp[k]}" for k in include_keys if k in tmp)][0]
    acc_dict[sub]["Filtered Report"] = text


REAL_REPORT_1= acc_dict["40547140"]["Filtered Report"] 
REAL_REPORT_2= acc_dict["39346227"]["Filtered Report"] 
REAL_REPORT_3= acc_dict["43908543"]["Filtered Report"] 

# INPUT_REPORT = acc_dict[subjects[79]]["Filtered Report"]
# INPUT_REPORT = acc_dict["40781581"]["Filtered Report"]



def main(input_report, id=None, save_dir=None, model_id='gpt-oss:120b'):
    os.makedirs(save_dir, exist_ok=True)
    identifier = f'_{id}' if id is not None else ''
    save_dir = f'{save_dir}/' if save_dir is not None else ''
    prompt = textwrap.dedent("""
        Extract tumor features, lesion characteristics, and brain anatomy in order of appearance.
        Use exact text for extractions. Do not paraphrase or overlap entities.
        Provide meaningful attributes for each entity to add context, such as measurements, locations, and descriptions.""")

    examples = [
        lx.data.ExampleData(
            text=REAL_REPORT_1,
            extractions=[
                lx.data.Extraction(
                    extraction_class="tumor_dimensions",
                    extraction_text="2.0 x 1.6 cm in axial dimension (801/93) and 2.7 cm in craniocaudal dimension (702/193)",
                    attributes={"axial": "2.0 x 1.6 cm", "craniocaudal": "2.7 cm", "current": "yes"}
                ),
                lx.data.Extraction(
                    extraction_class="number_of_lesions",
                    extraction_text="a mass",
                    attributes={"count": "1"}
                ),
                lx.data.Extraction(
                    extraction_class="cortical_involvement",
                    extraction_text="cortically based",
                    attributes={"involvement": "yes"}
                ),
                lx.data.Extraction(
                    extraction_class="tumor_location",
                    extraction_text="posterior medial left parietal occipital lobe",
                    attributes={"location": "posterior medial left parietal occipital lobe"}
                ),
                # lx.data.Extraction(
                #     extraction_class="ventricular_invasion",
                #     extraction_text="mass effect on the left lateral ventricle occipital horn",
                #     attributes={"invasion": "yes", "ventricle": "left lateral ventricle occipital horn"}
                # ),
                lx.data.Extraction(
                    extraction_class="side_of_tumor_epicenter",
                    extraction_text="left parietal occipital lobe",
                    attributes={"side": "left"}
                ),
                lx.data.Extraction(
                    extraction_class="enhancement_characteristics",
                    extraction_text="thick irregular peripheral enhancement and central necrosis",
                    attributes={"characteristics": "thick irregular peripheral enhancement and central necrosis"}
                ),
                lx.data.Extraction(
                    extraction_class="multifocality",
                    extraction_text="no additional sites of abnormal enhancement",
                    attributes={"multifocal": "no"}
                ),
                lx.data.Extraction(
                    extraction_class="deep_white_matter_invasion",
                    extraction_text="adjacent left temporoparietal white matter",
                    attributes={"invasion": "yes", "region": "left temporoparietal white matter"}
                ),
                lx.data.Extraction(
                    extraction_class="midline_shift",
                    extraction_text="no midline shift mentioned",
                    attributes={"shift": {"value": "no", "unit": None}}
                ),
                lx.data.Extraction(
                    extraction_class="midline_shift",
                    extraction_text="not mentioned",
                    attributes={"shift": {"value": "not reported", "unit": None}}
                ),
                lx.data.Extraction(
                    extraction_class="midline_shift",
                    extraction_text="5 mm midline shift",
                    attributes={"shift": {"value": "5", "unit": "mm"}}
                ),
                lx.data.Extraction(
                    extraction_class="ventricle_symmetry",
                    extraction_text="symmetric ventricles",
                    attributes={"symmetry": "yes"}
                ),
                lx.data.Extraction(
                    extraction_class="ventricle_enlargement",
                    extraction_text="enlarged ventricles",
                    attributes={"enlargement": "yes"}
                ),
            ]
        ),
    lx.data.ExampleData(
        text=REAL_REPORT_2,         
        extractions=[
            lx.data.Extraction(
                extraction_class="tumor_dimensions",
                extraction_text=(
                    "Approximately 7.8 x 4.9 x 3.8 cm (AP x TV x CC) "
                    "heterogeneously rim-enhancing mass"
                ),
                attributes={
                    "axial": "7.8 x 4.9 cm",          # AP × TV (largest transverse plane)
                    "craniocaudal": "3.8 cm",        # CC (depth)
                    "current": "yes"
                }
            ),
            lx.data.Extraction(
                extraction_class="number_of_lesions",
                extraction_text="single large mass",
                attributes={"count": "1"}
            ),

            lx.data.Extraction(
                extraction_class="cortical_involvement",
                extraction_text="epicenter in the right temporal lobe",
                attributes={"involvement": "yes"}
            ),

            lx.data.Extraction(
                extraction_class="tumor_location",
                extraction_text="right temporal lobe",
                attributes={"location": "right temporal lobe"}
            ),

            lx.data.Extraction(
                extraction_class="ventricular_effacement",
                extraction_text="right lateral ventricle is effaced",
                attributes={
                    "effacement": "yes",
                    "ventricle": "right lateral ventricle"
                }
            ),
            lx.data.Extraction(
                extraction_class="side_of_tumor_epicenter",
                extraction_text="right temporal lobe",
                attributes={"side": "right"}
            ),
            lx.data.Extraction(
                extraction_class="enhancement_characteristics",
                extraction_text="heterogeneously rim-enhancing mass with scattered internal susceptibility artifact",
                attributes={
                    "characteristics": (
                        "heterogeneous rim enhancement, internal susceptibility artifact"
                    )
                }
            ),
            lx.data.Extraction(
                extraction_class="multifocality",
                extraction_text="no additional sites of abnormal enhancement",
                attributes={"multifocal": "no"}
            ),
            lx.data.Extraction(
                extraction_class="deep_white_matter_invasion",
                extraction_text="no tumor-related deep white-matter invasion described",
                attributes={"invasion": "no"}
            ),
            lx.data.Extraction(
                extraction_class="midline_shift",
                extraction_text="Approximately 1.0 cm leftward midline shift",
                attributes={"shift": {"value": "10", "unit": "mm"}}   
            ),
            lx.data.Extraction(
                extraction_class="ventricle_symmetry",
                extraction_text="mild asymmetric enlargement of the left lateral ventricle",
                attributes={"symmetry": "no"}
            ),
            lx.data.Extraction(
                extraction_class="ventricle_enlargement",
                extraction_text="mild asymmetric enlargement of the left lateral ventricle",
                attributes={"enlargement": "yes"}
            ),
            lx.data.Extraction(
                extraction_class="multiple_satellite_lesions",
                extraction_text="no satellite lesions mentioned",
                attributes={"satellite": "no"}
            ),
            lx.data.Extraction(
                extraction_class="multifocality",
                extraction_text="no additional sites of abnormal enhancement",
                attributes={"multifocal": "no"}
            ),
        ]
    ),


    lx.data.ExampleData(
        text=REAL_REPORT_3,
        extractions=[
            lx.data.Extraction(
                extraction_class="tumor_dimensions",
                extraction_text=(
                    "Increasing size of a rim-enhancing lesion centered in the right cerebral peduncle "
                    "which measures 2.1 x 2.1 x 1.6 cm"
                ),
                attributes={
                    "axial": "2.1 x 2.1 cm",          # AP × TV (largest transverse plane)
                    "craniocaudal": "1.6 cm",        # CC (depth)
                    "current": "yes"
                }
            ),
            lx.data.Extraction(
                extraction_class="number_of_lesions",
                extraction_text="single rim-enhancing lesion",
                attributes={"count": "1"}
            ),
            lx.data.Extraction(
                extraction_class="side_of_tumor_epicenter",
                extraction_text="centered in the right cerebral peduncle",
                attributes={"side": "right"}
            ),
            lx.data.Extraction(
                extraction_class="midline_shift",
                extraction_text="No shift.",
                attributes={"shift": {"value": "0", "unit": "mm"}}
            ),
            lx.data.Extraction(
                extraction_class="multiple_satellite_lesions",
                extraction_text="No new enhancing lesions are identified.",
                attributes={"satellite": "no"}
            ),
            lx.data.Extraction(
                extraction_class="ventricle_symmetry",
                extraction_text="The lateral ventricles are symmetric.",
                attributes={"symmetry": "yes"}
            ),
            lx.data.Extraction(
                extraction_class="ventricle_enlargement",
                extraction_text="The ventricles, sulci and cisterns are normal.",
                attributes={"enlargement": "no"}
            ),
            lx.data.Extraction(
                extraction_class="multifocality",
                extraction_text="No new enhancing lesions are identified.",
                attributes={"multifocal": "no"}
            ),
            lx.data.Extraction(
                extraction_class="cortical_involvement",
                extraction_text="Lesion centered in the right cerebral peduncle with no cortical involvement.",
                attributes={"involvement": "no"}
            ),
            lx.data.Extraction(
                extraction_class="deep_white_matter_invasion",
                extraction_text="Mild surrounding white-matter edema within the midbrain/pons but no deep white-matter invasion described.",
                attributes={"invasion": "no"}
            ),
            lx.data.Extraction(
                extraction_class="tumor_location",
                extraction_text="right cerebral peduncle",
                attributes={"location": "right cerebral peduncle"}
            ),
            lx.data.Extraction(
                extraction_class="ventricular_invasion",
                extraction_text="No ventricular invasion noted.",
                attributes={"invasion": "no"}
            ),
            lx.data.Extraction(
                extraction_class="ventricular_effacement",
                extraction_text="No shift and ventricles are normal.",
                attributes={
                    "effacement": "no",
                    "ventricle": "none"
                }
            )
        ]
    ),

    ]

    try:
        result = lx.extract(
            text_or_documents=input_report,
            prompt_description=prompt,
            examples=examples,
            model_id=model_id,  # Automatically selects Ollama provider
            model_url="http://localhost:11434",
            fence_output=False,
            use_schema_constraints=True
        )

        # Save the results to a JSONL file
        lx.io.save_annotated_documents([result], output_name=f"{save_dir}extraction_results{identifier}.jsonl", output_dir=".")

        # Generate the visualization from the file
        html_content = lx.visualize(f"{save_dir}extraction_results{identifier}.jsonl")
        with open(f"{save_dir}visualization{identifier}.html", "w") as f:
            if hasattr(html_content, 'data'):
                f.write(html_content.data)  # For Jupyter/Colab
            else:
                f.write(html_content)
    except Exception as e:
        LOG_FILE=f"{save_dir}error_log.txt"
        

        with open(LOG_FILE, "a") as f:
            f.write(f"[{datetime.now().isoformat()}]\n")
            f.write(f'\n\n{id} unsuccessful:\n')
            f.write(f'\nInput Report:\n{input_report}\n')
            f.write(f"{str(e)}\n")
            f.write(traceback.format_exc())
            f.write("\n" + "-"*80 + "\n")

# json_path='/pscratch/sd/j/jehr/MSFT/BTReportClinicalEvalData/merged_reports_btreport_gptoss_120b.json'
json_path='/pscratch/sd/j/jehr/MSFT/BTReport/merged_reports_btreport_V3.json'
with open(json_path, 'r') as file:
    # Deserialize the JSON data from the file into a Python object
    report_dict = json.load(file)

for sub in sorted(report_dict.keys()):
    tmp_clinical = parse_radiology_report(report_dict[sub]["Clinical Report"])
    # tmp_predicted = parse_radiology_report(report_dict[sub]["Predicted Report (AutoRG-Brain)"]) ##

    include_keys=['BRAIN', 'MASS EFFECT & VENTRICLES',]
    text_clinical = ["\n\n".join(f"{k}:\n{tmp_clinical[k]}" for k in include_keys if k in tmp_clinical)][0]
    # text_predicted = ["\n\n".join(f"{k}:\n{tmp_predicted[k]}" for k in include_keys if k in tmp_predicted)][0]
    text_predicted=report_dict[sub]["Predicted Report (AutoRG-Brain)"]

    report_dict[sub]["Filtered Clinical Report"] = text_clinical
    report_dict[sub]["Filtered Predicted Report"] = text_predicted


if __name__ == '__main__':
    keys=['Predicted Report']#,'Clinical Report']
    for key in keys:
        model_id='llama3:70b'
        save_dir=f"/pscratch/sd/j/jehr/MSFT/BTReport/btreport/evaluation/intermediate_feature_validation/autorg_brain/{model_id}/{'-'.join(key.lower().split(' '))}" ##
        subjects = sorted(list(report_dict.keys()))
        for id in tqdm(subjects, total=len(subjects), colour='green'):
            if os.path.exists(f"{save_dir}/extraction_results_{id}.jsonl"):
                continue
            INPUT_REPORT = report_dict[id][f"Filtered {key}"]
            print(f"Processing {id}")
            main(input_report=INPUT_REPORT, id=id, save_dir=save_dir, model_id=model_id)