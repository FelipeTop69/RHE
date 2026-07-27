import os
import sys
import tkinter as tk
from tkinter import filedialog

import fitz  # PyMuPDF

# 1. Interfaz de selección
root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)

print("⏳ Abriendo explorador... Por favor, selecciona tu 'Plantilla_Base_1P.pdf':")
pdf_filename = filedialog.askopenfilename(
    title="Selecciona la Plantilla (1 Producto)",
    filetypes=[("Archivos PDF", "*.pdf")]
)

if not pdf_filename:
    print("❌ Operación cancelada. No se seleccionó ningún archivo.")
    sys.exit()

# Tu Payload (Los datos a inyectar)
nueva_factura = {
    "@@CONSECUTIVO@@": "CAJP-112500",
    "@@FECHA@@": "2026-07-26",
    "@@HORA_GEN@@": "08:15:00",
    "@@HORA_EXP@@": "08:15:10",
    "@@CLIENTE_NOMBRE@@": "TOVAR AVILES RUBEN FELIPE",
    "@@CLIENTE_NIT@@": "1.007.681.658-3",
    "@@PROD1_DESC@@": "BOTELLON DE AGUA 18.9 L",
    "@@PROD1_CANT@@": "1,00",
    "@@VALOR_TOTAL@@": "2.200,00"
}

print("\n🚀 Generando factura final con precisión de línea base...\n")

# 2. Procesamiento
doc = fitz.open(pdf_filename)
page = doc[0]

operaciones = []
diccionario_texto = page.get_text("dict")

# PASO 1: RECOLECTAR DATOS DE LOS TAGS ROJOS
for tag, nuevo_valor in nueva_factura.items():
    instancias = page.search_for(tag)

    for inst in instancias:
        span_match = None
        for bloque in diccionario_texto.get("blocks", []):
            for linea in bloque.get("lines", []):
                for span in linea.get("spans", []):
                    if tag in span.get("text", ""):  # noqa: SIM102
                        if abs(span["bbox"][1] - inst.y0) < 5:
                            span_match = span
                            break
                if span_match: break
            if span_match: break

        if span_match:
            origen_x, origen_y = span_match["origin"]
            tamaño = span_match["size"]
            fuente_original = span_match["font"].lower()

            if "bold" in fuente_original or "black" in fuente_original:
                fuente_final = "hebo"
            elif "courier" in fuente_original:
                fuente_final = "cour"
            else:
                fuente_final = "helv"

            operaciones.append({
                "rect": inst,
                "texto": nuevo_valor,
                "fuente": fuente_final,
                "tamaño": tamaño,
                "origen": (origen_x, origen_y)
            })

# PASO 2: BORRADO INTELIGENTE
for op in operaciones:
    page.add_redact_annot(op["rect"])

page.apply_redactions(images=0, graphics=0)

# PASO 3: INYECTAR TEXTO EN NEGRO
for op in operaciones:
    page.insert_text(
        op["origen"],
        op["texto"],
        fontname=op["fuente"],
        fontsize=op["tamaño"],
        color=(0, 0, 0)
    )

# 4. Guardado local
nombre_salida = f"Factura_{nueva_factura['@@CONSECUTIVO@@']}_1P.pdf"
ruta_guardado = os.path.join(os.path.dirname(pdf_filename), nombre_salida)

doc.save(ruta_guardado)
doc.close()

print(f"✅ ¡Factura generada exitosamente! Guardada en: {ruta_guardado}")