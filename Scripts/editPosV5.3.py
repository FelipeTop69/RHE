import os
import sys
import tkinter as tk
from tkinter import filedialog

import fitz  # PyMuPDF

# 1. Interfaz de selección
root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)

print("⏳ Abriendo explorador... Por favor, selecciona la factura '03 Producto.pdf':")
pdf_filename = filedialog.askopenfilename(
    title="Selecciona la factura original (3 Productos)",
    filetypes=[("Archivos PDF", "*.pdf")]
)

if not pdf_filename:
    print("❌ Operación cancelada.")
    sys.exit()

# 2. Procesamiento
doc = fitz.open(pdf_filename)
page = doc[0]

reemplazos = {
    "CAJP-112417": "@@CONSECUTIVO@@",
    "2026-07-23": "@@FECHA@@",
    "19:19:08": "@@HORA_GEN@@",
    "19:20:11": "@@HORA_EXP@@",
    "BELTRAN GONZALEZ ESMERALDA": ["@@CLIENTE_NOMBRE@@", "COMPAÑIA OPITA DE FRIO S.A.S"],
    "5,090,879 - 1": "@@CLIENTE_NIT@@",
    "BTO ESCARCHA GRUESO": "@@PROD1_DESC@@",
    "BTO HIELO TUBULAR": "@@PROD2_DESC@@",
    "BTO ESCAR FINO": "@@PROD3_DESC@@",
    "2,00": ["@@PROD1_CANT@@", "@@PROD2_CANT@@"],
    "1,00": "@@PROD3_CANT@@",
    "18.000,00": ["@@PROD1_VALOR@@", "@@PROD2_VALOR@@"],
    "9.000,00": "@@PROD3_VALOR@@",
    "45.000,00": "@@VALOR_TOTAL@@"
}

print("\n🚀 Escaneando plantilla de 3 productos y corrigiendo duplicados...\n")

operaciones = []
diccionario_texto = page.get_text("dict")

for texto_original, tag_nuevo in reemplazos.items():
    instancias = page.search_for(texto_original)

    for indice, inst in enumerate(instancias):
        if isinstance(tag_nuevo, list):
            if indice < len(tag_nuevo):
                tag_actual = tag_nuevo[indice]
            else:
                continue
        else:
            tag_actual = tag_nuevo

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
                "texto": tag_actual,
                "fuente": fuente_final,
                "tamaño": tamaño,
                "origen": (origen_x, origen_y)
            })

for op in operaciones: page.add_redact_annot(op["rect"])
page.apply_redactions(images=0, graphics=0)

for op in operaciones:
    color_texto = (1, 0, 0) if op["texto"].startswith("@@") else (0, 0, 0)
    page.insert_text(
        op["origen"],
        op["texto"],
        fontname=op["fuente"],
        fontsize=op["tamaño"],
        color=color_texto
    )

# 3. Guardado local
nombre_plantilla = "Plantilla_Base_3P.pdf"
ruta_guardado = os.path.join(os.path.dirname(pdf_filename), nombre_plantilla)

doc.save(ruta_guardado)
doc.close()

print(f"✅ ¡Plantilla de 3 productos creada! Guardada en: {ruta_guardado}")