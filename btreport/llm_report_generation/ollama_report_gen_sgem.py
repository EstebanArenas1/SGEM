"""
Generación de reportes radiológicos en español para el pipeline SGEM.
Adapta BTReport al contexto clínico del Hospital Pablo Tobón Uribe.

Extiende ollama_report_gen.py con:
- Prompt en español
- Variables de cisternas basales (módulo SGEM)
- Variables de MLS por septum pellucidum (módulo SGEM)
- Ejemplos clínicos en español
"""

import json
import ollama
from sanitext.text_sanitization import sanitize_text

# ---------------------------------------------------------------------------
# Ejemplos de reportes reales en español (anonimizados)
# Sirven como few-shot examples para el LLM
# ---------------------------------------------------------------------------
EJEMPLOS_HALLAZGOS = """
1.
HALLAZGOS:
EFECTO DE MASA Y VENTRÍCULOS: Se evidencia desplazamiento de la línea media de 
aproximadamente 8 mm hacia la izquierda a nivel del septum pellucidum. Las cisternas 
basales se encuentran comprimidas, compatible con efecto de masa significativo. 
Efacement del asta frontal del ventrículo lateral derecho. No se identifica herniación 
transtentorial.
LESIÓN Y REALCE: En el lóbulo frontal derecho se identifica lesión con realce en anillo 
que mide 3.4 x 3.2 x 3.5 cm. Se observa área de hipointensidad central compatible con 
necrosis. Extensa zona de edema vasogénico perilesional.

2.
HALLAZGOS:
EFECTO DE MASA Y VENTRÍCULOS: La lesión descrita ejerce efecto de masa significativo 
sobre el atrio del ventrículo lateral derecho. Desplazamiento de línea media de 
aproximadamente 11 mm de derecha a izquierda medido a nivel del septum pellucidum. 
Las cisternas basales están parcialmente comprimidas.
LESIÓN Y REALCE: Lesión en lóbulo parieto-occipital derecho que mide 5.4 x 4.1 x 3.5 cm, 
con realce periférico nodular en sus márgenes posteromediales. Área de señal FLAIR 
perilesional que cruza el esplenio del cuerpo calloso y contacta el ventrículo lateral 
izquierdo.

3.
HALLAZGOS:
EFECTO DE MASA Y VENTRÍCULOS: Efacement de los astas anteriores de los ventrículos 
laterales. Desplazamiento de línea media de aproximadamente 5 mm hacia la derecha 
a nivel del septum pellucidum. Las cisternas basales se encuentran preservadas.
LESIÓN Y REALCE: Lesión de gran tamaño con epicentro en el lóbulo frontal paramediano 
izquierdo anterior que cruza el cuerpo calloso. La lesión invade el aspecto anterior 
de los ventrículos laterales. Área necrótica central que mide hasta 2.5 cm.
"""

# ---------------------------------------------------------------------------
# Plantilla del prompt en español con variables SGEM
# ---------------------------------------------------------------------------
PLANTILLA_REPORTE_ES = """
Eres un radiólogo generando un reporte clínico de RM cerebral en español.

A continuación se presentan ejemplos de secciones de HALLAZGOS tomados de reportes 
reales de tumores cerebrales del Hospital Pablo Tobón Uribe:

EJEMPLOS DE HALLAZGOS:
{ejemplos_hallazgos}

---

Ahora genera una sección de HALLAZGOS similar, usando ÚNICAMENTE los metadatos 
proporcionados a continuación.

INSTRUCCIONES IMPORTANTES:
- Escribe SOLO en español clínico formal, como lo haría un radiólogo colombiano.
- NO inventes información que no esté directamente respaldada por los metadatos.
- Mantén las subsecciones: EFECTO DE MASA Y VENTRÍCULOS, y LESIÓN Y REALCE.
- Selecciona los 7-10 hallazgos más relevantes clínicamente.
- Prioriza hallazgos anormales o clínicamente significativos.
- Las secuencias disponibles son: T1n, T2, T2-FLAIR y T1-Gd. No menciones difusión.
- Comenta siempre el desplazamiento de línea media usando el valor de mls_septum_mm
  y mls_direccion. Menciona explícitamente que fue medido a nivel del septum pellucidum.
- Comenta el estado de las cisternas basales usando cisterns_status y compression_ratio.
- Comenta el efacement ventricular si está presente, indicando lado y cuerno afectado.
- Indica las dimensiones de la lesión en 3D en centímetros.
- NO menciones estructuras ni hallazgos que no estén respaldados por los metadatos.

METADATOS (paciente {subject_id}):
{metadata_json}

---

Escribe ahora la sección de HALLAZGOS en español clínico formal.
"""

# ---------------------------------------------------------------------------
# Plantilla con imagen (multimodal)
# ---------------------------------------------------------------------------
PLANTILLA_REPORTE_ES_IMAGEN = """
Eres un radiólogo generando un reporte clínico de RM cerebral en español.

A continuación se presentan ejemplos de secciones de HALLAZGOS tomados de reportes 
reales de tumores cerebrales del Hospital Pablo Tobón Uribe:

EJEMPLOS DE HALLAZGOS:
{ejemplos_hallazgos}

---

Genera una sección de HALLAZGOS usando los metadatos proporcionados y la imagen T1c adjunta.

INSTRUCCIONES:
- Escribe SOLO en español clínico formal.
- NO inventes información no respaldada por metadatos o imagen.
- Mantén las subsecciones: EFECTO DE MASA Y VENTRÍCULOS, y LESIÓN Y REALCE.
- Comenta el MLS usando mls_septum_mm y mls_direccion (medido en septum pellucidum).
- Comenta cisternas basales usando cisterns_status y compression_ratio.
- Las secuencias disponibles son T1n, T2, T2-FLAIR y T1-Gd únicamente.

METADATOS (paciente {subject_id}):
{metadata_json}

---

Escribe ahora la sección de HALLAZGOS en español clínico formal.
"""


def generar_reporte_es(subject_id, metadata, image_path=None, model="llama3:8b"):
    """
    Genera el reporte radiológico en español usando el LLM.

    Parameters
    ----------
    subject_id : str
        Identificador del paciente.
    metadata : dict
        Features extraídas por BTReport + módulos SGEM.
        Debe incluir: cisterns_status, compression_ratio,
                      mls_septum_mm, mls_direccion, mls_categoria.
    image_path : str, optional
        Ruta a imagen T1c para modo multimodal.
    model : str
        Modelo Ollama a usar. Por defecto llama3:8b (compatible con T4 Colab).

    Returns
    -------
    str — texto del reporte en español
    """
    if image_path is None:
        prompt = PLANTILLA_REPORTE_ES.format(
            ejemplos_hallazgos=EJEMPLOS_HALLAZGOS,
            subject_id=subject_id,
            metadata_json=json.dumps(metadata, indent=2, ensure_ascii=False),
        )
    else:
        prompt = PLANTILLA_REPORTE_ES_IMAGEN.format(
            ejemplos_hallazgos=EJEMPLOS_HALLAZGOS,
            subject_id=subject_id,
            metadata_json=json.dumps(metadata, indent=2, ensure_ascii=False),
        )

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    reporte = response["message"]["content"]
    reporte = reporte.replace("\u2011", "-")

    try:
        return sanitize_text(reporte)
    except Exception:
        return reporte