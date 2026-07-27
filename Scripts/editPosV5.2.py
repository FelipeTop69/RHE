import os
import sys
import tkinter as tk
from tkinter import filedialog

import fitz  # PyMuPDF

# 1. Interfaz de selección
root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)

print("⏳ Abriendo explorador... Por favor, selecciona tu factura original:")
pdf_filename = filedialog.askopenfilename(
    title="Selecciona la factura original (2 Productos)",
    filetypes=[("Archivos PDF", "*.pdf")]
)

if not pdf_filename:
    print("❌ Operación cancelada.")
    sys.exit()

# 2. Procesamiento
doc = fitz.open(pdf_filename)
page = doc[0]

reemplazos = {
    "CAJP-112194": "@@CONSECUTIVO@@",
    "2026-07-22": "@@FECHA@@",
    "08:23:41": "@@HORA_GEN@@",
    "08:23:49": "@@HORA_EXP@@",
    "PEREZ PERDOMO SEBASTIAN": "@@CLIENTE_NOMBRE@@",
    "1,007,681,658 - 3": "@@CLIENTE_NIT@@",
    "B. TUB 15 KILOS": "@@PROD1_DESC@@",
    "3,00": "@@PROD1_CANT@@",
    "18.000,00": "@@PROD1_VALOR@@",
    "BOTELLON DE AGUA 18.9 L": "@@PROD2_DESC@@",
    "2,00": "@@PROD2_CANT@@",
    "13.000,00": "@@PROD2_VALOR@@",
    "31.000,00": "@@VALOR_TOTAL@@"
}

print("\n🚀 Escaneando plantilla de 2 productos...\n")

operaciones = []
diccionario_texto = page.get_text("dict")

for texto_original, tag_nuevo in reemplazos.items():
    instancias = page.search_for(texto_original)

    for indice, inst in enumerate(instancias):
        if texto_original == "3,00" and indice == 0:
            continue

        span_match = None
        for bloque in diccionario_texto.get("blocks", []):
            for linea in bloque.get("lines", []):
                for span in linea.get("spans", []):
                    if texto_original in span.get("text", ""):  # noqa: SIM102
                        if abs(span["bbox"][1] - inst.y0) < 5:
                            span_match = span
                            break
                if span_match: break
            if span_match: break

        if span_match:
            origen_x, origen_y = span_match["origin"]
            tamaño = span_match["size"]
            fuente_original = span_match["font"].lower()

            if "bold" in fuente_original or "black" in fuente_original: fuente_final = "hebo"
            elif "courier" in fuente_original: fuente_final = "cour"
            else: fuente_final = "helv"

            operaciones.append({
                "rect": inst,
                "texto": tag_nuevo,
                "fuente": fuente_final,
                "tamaño": tamaño,
                "origen": (origen_x, origen_y)
            })

for op in operaciones: page.add_redact_annot(op["rect"])
page.apply_redactions(images=0, graphics=0)

for op in operaciones:
    page.insert_text(op["origen"], op["texto"], fontname=op["fuente"], fontsize=op["tamaño"], color=(1, 0, 0))

# 3. Guardado local
nombre_plantilla = "Plantilla_Base_2P.pdf"
ruta_guardado = os.path.join(os.path.dirname(pdf_filename), nombre_plantilla)

doc.save(ruta_guardado)
doc.close()

print(f"✅ ¡Plantilla de 2 productos creada! Guardada en: {ruta_guardado}")