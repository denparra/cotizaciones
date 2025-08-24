import pandas as pd
import re

def preparar_excel(ruta_entrada, ruta_salida=None):
    # Carga el Excel respetando encabezados
    df = pd.read_excel(ruta_entrada)

    # Normaliza nombres de columnas
    df.columns = [col.strip().lower().replace("\n", " ") for col in df.columns]

    # Renombra columnas al formato esperado por la BD
    df = df.rename(columns={
        "fecha inicio": "fecha_inicio",
        "nombre cliente": "nombre_cliente",
        "correo": "correo",
        "contacto cliente": "telefono",
        "auto": "auto",
        "observacion": "observacion"
    })

    # Limpia teléfonos (deja solo números)
    df["telefono"] = df["telefono"].astype(str).apply(lambda x: re.sub(r"\D", "", x))

    # Completa columnas faltantes con valores por defecto
    hoy = pd.Timestamp.today().date().isoformat()
    df["fecha_ultimo_contacto"] = hoy
    df["visita_programada"] = hoy
    df["estado"] = "Pendiente"
    df["whatsapp_link"] = df["telefono"].apply(lambda t: f"https://wa.me/56{t}" if t else "")
    df["link_auto"] = ""
    df["link_chileautos"] = ""

    # Guarda si se indicó ruta de salida
    if ruta_salida:
        df.to_excel(ruta_salida, index=False)

    return df
