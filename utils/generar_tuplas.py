import pandas as pd
import re

df = pd.read_excel("export/archivo_limpio.xlsx")

# Limpieza básica
df = df.loc[:, ~df.columns.str.contains("^Unnamed", case=False)]
df["telefono"] = df["telefono"].astype(str).str.replace(r"\D", "", regex=True)
df = df[df["telefono"].str.match(r"^9\d{8}$")]

# Validar fechas
df["fecha_inicio"] = pd.to_datetime(df["fecha_inicio"], errors="coerce").dt.date
df["fecha_ultimo_contacto"] = pd.to_datetime(df["fecha_ultimo_contacto"], errors="coerce").dt.date
df["visita_programada"] = pd.to_datetime(df["visita_programada"], errors="coerce").dt.date

# Links
df["whatsapp_link"] = df["telefono"].apply(lambda x: f"https://wa.me/56{x}")
df["link_auto"] = df["link_auto"].fillna("").astype(str)

# Solo los primeros 500
df = df.sort_values("fecha_inicio", ascending=False).head(500)

# Mostrar como lista de tuplas
for _, row in df.iterrows():
    fila = (
        str(row["fecha_inicio"]),
        str(row["nombre_cliente"]),
        str(row["correo"]),
        str(row["telefono"]),
        str(row["auto"]),
        str(row["observacion"]),
        str(row["fecha_ultimo_contacto"]),
        str(row["visita_programada"]),
        str(row["estado"]),
        str(row["whatsapp_link"]),
        str(row["link_auto"])
    )
    print(f"{fila},")
