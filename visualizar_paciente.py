"""
Visualización rápida de las 4 secuencias de un paciente HPTU.
"""
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt

PACIENTE = "HPTU-001"
BASE = f"data/HPTU/{PACIENTE}"

secuencias = {
    "T1n (sin contraste)": f"{BASE}/{PACIENTE}-t1n.nii.gz",
    "T1c (con contraste)": f"{BASE}/{PACIENTE}-t1c.nii.gz",
    "T2":                  f"{BASE}/{PACIENTE}-t2.nii.gz",
    "FLAIR":               f"{BASE}/{PACIENTE}-flair.nii.gz",
}

fig, axes = plt.subplots(1, 4, figsize=(20, 5))
fig.suptitle(f"Paciente {PACIENTE} — 4 secuencias RM — HPTU", fontsize=14)

for ax, (nombre, ruta) in zip(axes, secuencias.items()):
    img = nib.load(ruta).get_fdata()
    corte = img[:, :, img.shape[2] // 2]
    ax.imshow(corte.T, cmap="gray", origin="lower")
    ax.set_title(nombre)
    ax.axis("off")
    print(f"{nombre}: {img.shape} — rango [{img.min():.0f}, {img.max():.0f}]")

plt.tight_layout()
plt.savefig("visualizacion_HPTU-001.png", dpi=150)
plt.show()
print("\nImagen guardada como visualizacion_HPTU-001.png")