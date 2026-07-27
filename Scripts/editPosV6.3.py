import os
import sys
import tkinter as tk
from tkinter import filedialog

import fitz  # PyMuPDF

# 1. Interfaz de selección
root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)

print("⏳ Abriendo explorador... Por favor, selecciona tu 'Plantilla_Base_3P.pdf':")
pdf_filename = filedialog.askopenfilename(
    title="Selecciona la Plantilla (3 Productos)",
    filetypes=[("Archivos PDF", "*.pdf")]
)

if not pdf_filename:
    print("❌ Operación cancelada. No se seleccionó ningún archivo.")
    sys.exit()

# Payload extendido para tres productos
nueva_factura = {
    "@@CONSECUTIVO@@": "CAJP-113000",
    "@@FECHA@@": "2026-08-01",
    "@@HORA_GEN@@": "14:30:00",
    "@@HORA_EXP@@": "14:30:15",
    "@@CLIENTE_NOMBRE@@": "CARLOS RAMIREZ",
    "@@CLIENTE_NIT@@": "85.456.789-2",
    "@@PROD1_DESC@@": "B. TUB 15 KILOS",
    "@@PROD1_CANT@@": "4,00",
    "@@PROD1_VALOR@@": "24.000,00",
    "@@PROD2_DESC@@": "BOTELLON DE AGUA 18.9 L",
    "@@PROD2_CANT@@": "1,00",
    "@@PROD2_VALOR@@": "8.500,00",
    "@@PROD3_DESC@@": "BOLSA HIELO 5 KILOS",
    "@@PROD3_CANT@@": "3,00",
    "@@PROD3_VALOR@@": "12.000,00",
    "@@VALOR_TOTAL@@": "44.500,00"
}

print("\n🚀 Generando factura final de 3 productos...\n")

# 2. Procesamiento
doc = fitz.open(pdf_filename)
page = doc[0]
operaciones = []
diccionario_texto = page.get_text("dict")

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

            if "bold" in fuente_original or "black" in fuente_original: fuente_final = "hebo"
            elif "courier" in fuente_original: fuente_final = "cour"
            else: fuente_final = "helv"

            operaciones.append({
                "rect": inst,
                "texto": nuevo_valor,
                "fuente": fuente_final,
                "tamaño": tamaño,
                "origen": (origen_x, origen_y)
            })

for op in operaciones: page.add_redact_annot(op["rect"])
page.apply_redactions(images=0, graphics=0)

for op in operaciones:
    page.insert_text(op["origen"], op["texto"], fontname=op["fuente"], fontsize=op["tamaño"], color=(0, 0, 0))

# 3. Guardado local
nombre_salida = f"Factura_{nueva_factura['@@CONSECUTIVO@@']}_3P.pdf"
ruta_guardado = os.path.join(os.path.dirname(pdf_filename), nombre_salida)

doc.save(ruta_guardado)
doc.close()

print(f"✅ ¡Factura generada exitosamente! Guardada en: {ruta_guardado}")