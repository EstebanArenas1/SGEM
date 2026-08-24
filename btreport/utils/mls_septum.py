"""
Módulo de medición de desplazamiento de línea media (MLS)
por detección directa del septum pellucidum.

Contribución original SGEM — TFM Hospital Pablo Tobón Uribe.
Complementa el método de registro de BTReport (SynthMorph).
"""

import logging
import nibabel as nib
import numpy as np

logger = logging.getLogger(__name__)

# Etiquetas del septum pellucidum en SynthSeg (confirmadas en midline_shift3d.py)
SP_LABELS = [10, 49]

# Umbrales clínicos estándar (mm)
UMBRAL_SIGNIFICATIVO = 5.0   # >5mm → MLS significativo
UMBRAL_CRITICO = 10.0        # >10mm → MLS crítico


def medir_mls_septum(anat_seg_path):
    """
    Mide el desplazamiento de línea media directamente desde
    la posición del septum pellucidum en la segmentación anatómica.

    Parameters
    ----------
    anat_seg_path : str
        Ruta a la segmentación anatómica de SynthSeg en espacio del paciente.
        Archivo generado por BTReport durante el preprocesamiento.

    Returns
    -------
    dict con:
        - mls_septum_mm     : float — desplazamiento en milímetros
        - mls_direccion     : str   — "izquierda→derecha" o "derecha→izquierda"
        - mls_significativo : bool  — True si >5mm
        - mls_critico       : bool  — True si >10mm
        - mls_categoria     : str   — "ausente" | "leve" | "moderado" | "severo"
        - septum_centroid_x : float — posición x del centroide del septum (voxels)
        - brain_center_x    : float — centro geométrico del cerebro (voxels)
        - voxel_size_mm     : float — tamaño del voxel en mm
    """
    logger.info("Midiendo MLS por septum pellucidum...")

    seg_nii = nib.load(anat_seg_path)
    seg = seg_nii.get_fdata().astype(int)
    voxel_size = float(seg_nii.header.get_zooms()[0])  # mm por voxel en eje X

    # --- Detectar septum pellucidum ---
    sp_mask = np.isin(seg, SP_LABELS)
    if np.sum(sp_mask) == 0:
        raise ValueError(
            "No se detectó septum pellucidum (etiquetas 10, 49) en la segmentación. "
            "Verifica que SynthSeg procesó correctamente la imagen."
        )

    sp_voxels = np.argwhere(sp_mask)
    septum_centroid_x = float(np.mean(sp_voxels[:, 0]))

    # --- Centro geométrico del cerebro ---
    brain_mask = seg > 0
    brain_voxels = np.argwhere(brain_mask)
    x_min = float(brain_voxels[:, 0].min())
    x_max = float(brain_voxels[:, 0].max())
    brain_center_x = (x_min + x_max) / 2.0

    # --- Calcular MLS ---
    desplazamiento_voxels = septum_centroid_x - brain_center_x
    mls_mm = abs(desplazamiento_voxels) * voxel_size

    # Dirección anatómica
    # En coordenadas RAS: X positivo = derecha
    if desplazamiento_voxels > 0:
        direccion = "izquierda→derecha"
    else:
        direccion = "derecha→izquierda"

    # Categoría clínica
    if mls_mm < 3.0:
        categoria = "ausente"
    elif mls_mm < 5.0:
        categoria = "leve"
    elif mls_mm < 10.0:
        categoria = "moderado"
    else:
        categoria = "severo"

    resultado = {
        "mls_septum_mm": round(mls_mm, 2),
        "mls_direccion": direccion,
        "mls_significativo": mls_mm >= UMBRAL_SIGNIFICATIVO,
        "mls_critico": mls_mm >= UMBRAL_CRITICO,
        "mls_categoria": categoria,
        "septum_centroid_x": round(septum_centroid_x, 2),
        "brain_center_x": round(brain_center_x, 2),
        "voxel_size_mm": voxel_size
    }

    logger.info(f"MLS septum: {mls_mm:.2f} mm {direccion} — {categoria}")
    return resultado


def texto_reporte(resultado):
    """
    Genera el texto clínico en español para el reporte final.

    Parameters
    ----------
    resultado : dict
        Output de medir_mls_septum()

    Returns
    -------
    str con el texto listo para insertar en el reporte
    """
    mls = resultado["mls_septum_mm"]
    direccion = resultado["mls_direccion"]
    categoria = resultado["mls_categoria"]

    if categoria == "ausente":
        return (
            f"No se evidencia desplazamiento significativo de la línea media. "
            f"El septum pellucidum se encuentra centrado "
            f"(desplazamiento medido: {mls:.1f} mm)."
        )
    elif categoria == "leve":
        return (
            f"Desplazamiento leve de la línea media de aproximadamente {mls:.1f} mm "
            f"en dirección {direccion}, medido a nivel del septum pellucidum."
        )
    elif categoria == "moderado":
        return (
            f"Desplazamiento moderado de la línea media de aproximadamente {mls:.1f} mm "
            f"en dirección {direccion}, medido a nivel del septum pellucidum. "
            f"Hallazgo compatible con efecto de masa significativo."
        )
    else:
        return (
            f"Desplazamiento severo de la línea media de aproximadamente {mls:.1f} mm "
            f"en dirección {direccion}, medido a nivel del septum pellucidum. "
            f"Hallazgo sugestivo de efecto de masa crítico — requiere evaluación urgente."
        )