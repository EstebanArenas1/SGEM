"""
Convierte las series DICOM relevantes del HPTU a formato NIfTI.
Organiza los archivos en la estructura que espera BTReport.
"""
import os
import subprocess

DICOM_ROOT = r"C:\Users\esteb\Documents\Practicas_HPTU\DICOM_SGEM"
OUTPUT_ROOT = r"C:\Users\esteb\Documents\Practicas_HPTU\SGEM\data\HPTU"

# Mapeo de series por paciente
# Formato: {id_paciente: {secuencia: carpeta_serie}}
PACIENTES = {
    "HPTU-001": {
        "base": "10000000/10000001",
        "t1n":  "100003B0",
        "t1c":  "1000044D",
        "t2":   "10000115",
        "flair":"100003ED",
    },
    "HPTU-002": {
        "base": "10000593/10000594",
        "t1n":  "1000082C",
        "t1c":  "10000602",
        "t2":   "1000076E",
        "flair":"10000986",
    },
    "HPTU-003": {
        "base": "100009C6/100009C7",
        "t1n":  "10000B8E",
        "t1c":  "10000B36",
        "t2":   "10000BBC",
        "flair":"10000CBE",
    },
}

os.makedirs(OUTPUT_ROOT, exist_ok=True)

for paciente_id, info in PACIENTES.items():
    print(f"\nProcesando {paciente_id}...")
    output_dir = os.path.join(OUTPUT_ROOT, paciente_id)
    os.makedirs(output_dir, exist_ok=True)

    for secuencia, serie in info.items():
        if secuencia == "base":
            continue

        input_dir = os.path.join(DICOM_ROOT, info["base"], serie)
        output_file = os.path.join(output_dir, f"{paciente_id}-{secuencia}.nii.gz")

        if os.path.exists(output_file):
            print(f"  {secuencia}: ya existe, saltando")
            continue

        print(f"  Convirtiendo {secuencia} ({serie})...")
        result = subprocess.run([
            "dcm2niix",
            "-z", "y",
            "-f", f"{paciente_id}-{secuencia}",
            "-o", output_dir,
            input_dir
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print(f"  ✅ {secuencia} convertido")
        else:
            print(f"  ❌ Error en {secuencia}: {result.stderr[:100]}")

print("\nConversión completada")
print(f"Archivos en: {OUTPUT_ROOT}")