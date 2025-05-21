import os
import sys
import pandas as pd
import re

# Habilita importar utils desde ejecución fuera de carpeta
sys.path.append(os.path.dirname(os.path.abspath(__file__)).replace("\\utils", ""))

from utils.db_utils import get_connection

# Ruta del archivo Excel limpio
archivo = "export/archivo_limpio.xlsx"

# Columnas requeridas por la tabla
columnas_esperadas = {
    "fecha_inicio", "nombre_cliente", "correo", "telefono", "auto",
    "observacion", "fecha_ultimo_contacto", "visita_programada",
    "estado", "whatsapp_link", "link_auto"
}

# Leer archivo
df = pd.read_excel(archivo)

# Quitar columnas tipo "Unnamed"
df = df.loc[:, ~df.columns.str.contains("^unnamed", case=False)]

# Validar columnas
columnas_archivo = set(df.columns.str.strip().str.lower())
faltantes = columnas_esperadas - columnas_archivo

if faltantes:
    print("❌ ERROR: El archivo no contiene estas columnas requeridas:")
    for col in faltantes:
        print(f" - {col}")
    print("⚠️ Corrige el archivo antes de importar.")
    sys.exit(1)

# Función para limpiar y validar teléfono
def limpiar_telefono(x):
    if pd.isnull(x):
        return ""
    try:
        numero = str(int(float(x))).strip()
        if re.fullmatch(r"9\d{8}", numero):
            return numero
        else:
            return ""
    except:
        return ""

# Limpiar teléfonos
total_original = len(df)
df["telefono"] = df["telefono"].apply(limpiar_telefono)
df = df[df["telefono"].astype(bool)]

# Ordenar por fecha y limitar a 500 más recientes
df["fecha_inicio"] = pd.to_datetime(df["fecha_inicio"], errors="coerce")
df = df.sort_values(by="fecha_inicio", ascending=False).head(500)

# Insertar en la base de datos
with get_connection() as con:
    df.to_sql("cotizaciones", con, if_exists="append", index=False)

print(f"✅ Se insertaron {len(df)} fila(s) válidas en la base de datos.")
descartadas = total_original - len(df)
if descartadas > 0:
    print(f"⚠️ {descartadas} fila(s) fueron descartadas por teléfono inválido o fuera del top 500.")
