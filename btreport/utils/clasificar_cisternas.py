"""
Módulo de clasificación de cisternas basales para el pipeline SGEM.
Extiende BTReport con evaluación automática del estado de las cisternas.

Autor: TFM - Hospital Pablo Tobón Uribe
"""

import logging
import nibabel as nib
import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Etiquetas del atlas Cistern_Segmentations.nii.gz
# Mapeo inferido de visualización anatómica — validar con radióloga HPTU
# ---------------------------------------------------------------------------
CISTERNAS_BASALES = [2, 3, 4, 5, 7]      # inferiores: interpeduncular, prepontina, ambiens, cuadrigeminal
CISTERNAS_SYLVIANAS = [13]                # laterales bilaterales
CISTERNAS_OTRAS = [1, 6, 8, 9, 10, 11, 12]

# Para clasificación binaria usamos las basales (más sensibles al efecto de masa)
LABELS_CLASIFICACION = CISTERNAS_BASALES

# Umbrales de compresión — a calibrar con la radióloga
UMBRAL_COMPRIMIDAS = 0.5        # >50% solapamiento → comprimidas
UMBRAL_PARCIAL = 0.2            # 20-50% → parcialmente comprimidas


def clasificar_cisternas(cisterna_registrada_path, tumor_mask_path):
    """
    Clasifica las cisternas basales como preservadas, parcialmente
    comprimidas o comprimidas según el solapamiento con tumor/edema.

    Parameters
    ----------
    cisterna_registrada_path : str
        Ruta al atlas de cisternas ya registrado al espacio del paciente.
        Este archivo lo genera register_cistern.py de BTReport.
    tumor_mask_path : str
        Ruta a la máscara de segmentación BraTS del paciente
        (etiquetas: 1=NCR, 2=ED, 4=ET).

    Returns
    -------
    dict con:
        - cisterns_status       : str  ("preservadas" | "parcialmente comprimidas" | "comprimidas")
        - compression_ratio     : float (0.0 - 1.0)
        - cistern_overlap_voxels: int
        - cistern_total_voxels  : int
        - detalle_por_region    : dict con compression_ratio por cada label
    """
    logger.info("Iniciando clasificación de cisternas basales...")

    # Cargar imágenes
    cisterna_nii = nib.load(cisterna_registrada_path)
    tumor_nii = nib.load(tumor_mask_path)

    cisterna = cisterna_nii.get_fdata().astype(int)
    tumor = tumor_nii.get_fdata().astype(int)

    # Verificar que las dimensiones coincidan
    if cisterna.shape != tumor.shape:
        raise ValueError(
            f"Dimensiones no coinciden: cisternas {cisterna.shape} vs tumor {tumor.shape}. "
            f"Verifica que el atlas esté registrado al espacio del paciente."
        )

    # Máscara binaria del tumor completo (NCR + edema + realce)
    tumor_binario = tumor > 0

    # --- Clasificación global (cisternas basales críticas) ---
    mascara_basales = np.isin(cisterna, LABELS_CLASIFICACION)
    volumen_total = int(np.sum(mascara_basales))
    overlap_total = int(np.sum(mascara_basales & tumor_binario))

    if volumen_total == 0:
        logger.warning("No se encontraron cisternas basales en la imagen registrada.")
        compression_ratio = 0.0
    else:
        compression_ratio = overlap_total / volumen_total

    # Clasificación binaria
    if compression_ratio >= UMBRAL_COMPRIMIDAS:
        estado = "comprimidas"
    elif compression_ratio >= UMBRAL_PARCIAL:
        estado = "parcialmente comprimidas"
    else:
        estado = "preservadas"

    # --- Detalle por región individual ---
    detalle = {}
    for label in LABELS_CLASIFICACION:
        mascara_label = cisterna == label
        vol = int(np.sum(mascara_label))
        overlap = int(np.sum(mascara_label & tumor_binario))
        detalle[f"label_{label}"] = {
            "volumen_voxels": vol,
            "overlap_voxels": overlap,
            "compression_ratio": round(overlap / vol, 3) if vol > 0 else 0.0
        }

    resultado = {
        "cisterns_status": estado,
        "compression_ratio": round(float(compression_ratio), 3),
        "cistern_overlap_voxels": overlap_total,
        "cistern_total_voxels": volumen_total,
        "detalle_por_region": detalle
    }

    logger.info(f"Cisternas basales: {estado} (CR={compression_ratio:.3f})")
    return resultado


def texto_reporte(resultado):
    """
    Genera el texto clínico en español para incluir en el reporte final.
    Reemplaza el texto hardcodeado de BTReport.

    Parameters
    ----------
    resultado : dict
        Output de clasificar_cisternas()

    Returns
    -------
    str con el texto listo para el reporte
    """
    estado = resultado["cisterns_status"]
    cr = resultado["compression_ratio"]

    if estado == "comprimidas":
        return (
            f"Las cisternas basales se encuentran comprimidas, "
            f"con un índice de compresión de {cr:.2f}, "
            f"lo que sugiere efecto de masa significativo sobre la fosa posterior."
        )
    elif estado == "parcialmente comprimidas":
        return (
            f"Las cisternas basales presentan compresión parcial "
            f"(índice de compresión: {cr:.2f}), "
            f"compatible con efecto de masa moderado."
        )
    else:
        return (
            f"Las cisternas basales se encuentran preservadas "
            f"(índice de compresión: {cr:.2f}), "
            f"sin evidencia de efecto de masa significativo sobre estructuras de la fosa posterior."
        )