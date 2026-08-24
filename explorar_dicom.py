"""
Explorar la estructura de los datos DICOM del HPTU.
Identifica qué secuencia de RM es cada carpeta.
"""
import os
import pydicom

DICOM_ROOT = r"C:\Users\esteb\Documents\Practicas_HPTU\DICOM_SGEM"

print(f"Explorando: {DICOM_ROOT}\n")

for paciente in sorted(os.listdir(DICOM_ROOT)):
    paciente_path = os.path.join(DICOM_ROOT, paciente)
    if not os.path.isdir(paciente_path):
        continue
    
    print(f"{'='*60}")
    print(f"PACIENTE: {paciente}")
    
    # Entrar al nivel de estudio
    for estudio in sorted(os.listdir(paciente_path)):
        estudio_path = os.path.join(paciente_path, estudio)
        if not os.path.isdir(estudio_path):
            continue
        
        print(f"  ESTUDIO: {estudio}")
        
        # Entrar al nivel de series
        for serie in sorted(os.listdir(estudio_path)):
            serie_path = os.path.join(estudio_path, serie)
            if not os.path.isdir(serie_path):
                continue
            
            # Leer el primer archivo DICOM de la serie
            archivos = [f for f in os.listdir(serie_path) 
                       if not f.endswith('.txt') and not f.endswith('.xml')]
            
            if not archivos:
                continue
                
            try:
                dcm = pydicom.dcmread(
                    os.path.join(serie_path, archivos[0]), 
                    stop_before_pixels=True
                )
                
                descripcion = getattr(dcm, 'SeriesDescription', 'Sin descripción')
                modalidad = getattr(dcm, 'Modality', '?')
                n_archivos = len(archivos)
                paciente_id = getattr(dcm, 'PatientID', 'Anónimo')
                
                print(f"    Serie {serie}: [{modalidad}] {descripcion} ({n_archivos} cortes)")
                
            except Exception as e:
                print(f"    Serie {serie}: Error leyendo DICOM — {e}")

print(f"\n{'='*60}")
print("Exploración completada")