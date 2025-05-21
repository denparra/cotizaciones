###FUNCIONAL CON TODO###


import streamlit as st
import streamlit.components.v1 as components  # Para inyectar HTML/JS
from utils.db_utils import (
    create_tables,
    agregar_columna_link_auto,
    crear_tabla_mensajes,
    obtener_mensajes_whatsapp,
    insertar_cotizacion,
    obtener_cotizaciones,
    actualizar_cotizacion,
    eliminar_cotizacion,
)
import pandas as pd
import datetime
import urllib.parse

# Inicializa la base de datos y crea las tablas/columnas necesarias
create_tables()
agregar_columna_link_auto()
crear_tabla_mensajes()

# Configuración inicial de la app
st.set_page_config(page_title="Sistema de Cotizaciones", layout="centered")
st.title("📋 Sistema de Cotizaciones")
st.markdown("Bienvenido. Usa el menú lateral para navegar entre las funciones.")

# Menú lateral
st.sidebar.title("Navegación")
opcion = st.sidebar.radio("Ir a:", ["Inicio", "Nueva Cotización", "Ver Cotizaciones", "Exportar", "Gestión de Mensajes"])

if opcion == "Inicio":
    st.info("Selecciona una opción en el menú lateral para comenzar.")

elif opcion == "Nueva Cotización":
    st.header("📝 Ingresar Nueva Cotización")
    if st.session_state.get("limpiar_formulario"):
        for key in ["nombre", "correo", "telefono", "auto", "observacion"]:
            st.session_state[key] = ""
        st.session_state.limpiar_formulario = False

    with st.form("form_nueva"):
        hoy = datetime.date.today()
        fecha_inicio = st.date_input("Fecha inicio", value=hoy)
        nombre = st.text_input("Nombre cliente", key="nombre")
        correo = st.text_input("Correo electrónico", key="correo")
        telefono = st.text_input("Teléfono (obligatorio)", key="telefono")
        auto = st.text_input("Auto", key="auto")
        link_auto = st.text_input("Link del auto", key="link_auto")
        observacion = st.text_area("Observación", key="observacion")
        fecha_ultimo = st.date_input("Fecha último contacto", value=hoy)
        visita = st.date_input("Visita programada", value=hoy)
        estado = st.selectbox("Estado", ["Pendiente", "Visitado", "Cerrado", "Otro"])
        boton = st.form_submit_button("Guardar")

        if boton:
            if not telefono.strip():
                st.warning("⚠️ El campo teléfono es obligatorio.")
            else:
                whatsapp = f"https://wa.me/56{telefono.strip()}"
                data = (
                    fecha_inicio.isoformat(), nombre.strip(), correo.strip(), telefono.strip(),
                    auto.strip(), observacion.strip(), fecha_ultimo.isoformat(),
                    visita.isoformat(), estado, whatsapp,
                    link_auto.strip()  # nuevo campo agregado
                )
                insertar_cotizacion(data)
                st.success("✅ Cotización guardada correctamente.")
                st.session_state.limpiar_formulario = True
                st.rerun()

elif opcion == "Ver Cotizaciones":
    st.header("📑 Cotizaciones Registradas")
    # --- Filtros manuales ---
    with st.expander("🔍 Filtros"):
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro_nombre = st.text_input("Filtrar por nombre")
        with col2:
            filtro_telefono = st.text_input("Filtrar por teléfono")
        with col3:
            filtro_auto = st.text_input("Filtrar por auto")
    filtros = {
        "nombre": filtro_nombre.strip(),
        "telefono": filtro_telefono.strip(),
        "auto": filtro_auto.strip()
    }
    st.sidebar.markdown("---")
    limite = st.sidebar.slider("🔢 Máximo de registros", 50, 1000, 200, step=50)
    df = obtener_cotizaciones(filtros, limite)

    # --- Mensajes predeterminados para WhatsApp ---
    st.markdown("### 📨 Mensaje predeterminado para WhatsApp")
    col_msg, _ = st.columns([2, 3])
    mensajes_raw = obtener_mensajes_whatsapp()
    if mensajes_raw:
        opciones = {f"{m[1]}": (m[2], m[3]) for m in mensajes_raw}  # {nombre: (mensaje, descripción)}
        mensaje_nombre = col_msg.selectbox("Selecciona un mensaje:", list(opciones.keys()))
        mensaje_plantilla, mensaje_desc = opciones[mensaje_nombre]
        if mensaje_desc:
            st.caption(f"💬 {mensaje_desc}")
    else:
        mensaje_plantilla = ""
        st.info("No hay mensajes cargados.")

    # --- Filtros automáticos tipo recordatorio ---
    st.markdown("### 🔔 Recordatorios rápidos")
    opciones_recordatorio = [
        "— Ver todas",
        "Visitas para hoy",
        "Visitas esta semana",
        "Sin contacto en 7 días"
    ]
    opcion_recordatorio = st.selectbox("¿Qué deseas ver?", opciones_recordatorio)
    hoy = datetime.date.today()
    if opcion_recordatorio == "Visitas para hoy":
        df = df[df["visita_programada"] == hoy.isoformat()]
    elif opcion_recordatorio == "Visitas esta semana":
        fin_semana = hoy + datetime.timedelta(days=6 - hoy.weekday())
        df = df[
            (pd.to_datetime(df["visita_programada"]).dt.date >= hoy) &
            (pd.to_datetime(df["visita_programada"]).dt.date <= fin_semana)
        ]
    elif opcion_recordatorio == "Sin contacto en 7 días":
        hace_7 = hoy - datetime.timedelta(days=7)
        df = df[pd.to_datetime(df["fecha_ultimo_contacto"]).dt.date <= hace_7]
    if df.empty:
        st.warning("No se encontraron cotizaciones.")
        st.stop()

    st.success(f"{len(df)} cotización(es) encontradas.")

    # --- Paginación ---
    page_size = 20
    total_pages = (len(df) - 1) // page_size + 1
    page = st.number_input("📄 Página", min_value=1, max_value=total_pages, value=1, step=1)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    df_paginated = df.iloc[start_idx:end_idx].reset_index(drop=True)

    # --- Función para generar el mensaje ---
    def generar_mensaje(row, plantilla):
        return plantilla.replace("{{NOMBRE}}", row.get("nombre_cliente") or "") \
                        .replace("{{AUTO}}", row.get("auto") or "") \
                        .replace("{{LINK_AUTO}}", row.get("link_auto") or "")

    # --- Mostrar tabla interactiva con columnas extendidas ---
    st.markdown("### Lista de Cotizaciones")
    # Se definen los pesos relativos para las columnas: [Fecha, Última vez, Visita, Nombre, Teléfono, Auto, WhatsApp, Link Auto, Copiar, ID]
    col1, col2, col3, col4, col5, col6, col7, col8, col9, col10 = st.columns([3, 1.5, 1.5, 2, 3, 3, 2, 2, 3, 1])
    col1.markdown("**Fecha**")
    col2.markdown("**Última vez**")
    col3.markdown("**Visita**")
    col4.markdown("**Nombre**")
    col5.markdown("**Teléfono**")
    col6.markdown("**Auto**")
    col7.markdown("**WhatsApp**")
    col8.markdown("**Link Auto**")
    col9.markdown("**Copiar**")
    col10.markdown("**ID**")

    for index, row in df_paginated.iterrows():
        r_col1, r_col2, r_col3, r_col4, r_col5, r_col6, r_col7, r_col8, r_col9, r_col10 = st.columns([3,1.5,1.5,2,3,3,2,2,3,1])
        r_col1.write(row["fecha_inicio"])
        r_col2.write(row["fecha_ultimo_contacto"])
        r_col3.write(row["visita_programada"])
        r_col4.write(row["nombre_cliente"])
        r_col5.write(row["telefono"])
        r_col6.write(row["auto"])

        # Botón de WhatsApp: genera el enlace con el mensaje personalizado
        mensaje_personalizado = generar_mensaje(row, mensaje_plantilla)
        whatsapp_url = f"https://wa.me/56{row['telefono']}?text={urllib.parse.quote(mensaje_personalizado)}"
        r_col7.markdown(f"[Enviar]({whatsapp_url})")

        # Enlace para ver el link del auto (si existe)
        if row["link_auto"] and row["link_auto"].strip():
            r_col8.markdown(f"[Ver Auto]({row['link_auto']})")
        else:
            r_col8.write("—")

        # Botón "Copiar": carga el mensaje en el área de texto
        if r_col9.button("Copiar", key=f"copia_{row['id']}"):
            st.session_state['mensaje_generado'] = mensaje_personalizado
            st.success(f"Mensaje de {row['nombre_cliente']} cargado para copiar.")
        r_col10.write(row["id"])

    # --- Área de texto para mostrar el mensaje generado ---
    st.markdown("---")
    st.subheader("📝 Mensaje Generado:")
    mensaje = st.session_state.get('mensaje_generado', '')
    st.text_area("Mensaje", mensaje, height=180)

    # --- Botón con diseño mejorado para copiar el mensaje ---
    copy_button_html = f"""
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          .copy-button {{
            padding: 10px 20px;
            font-size: 16px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s ease;
          }}
          .copy-button:hover {{
            background-color: #45a049;
          }}
          .copy-button:active {{
            background-color: #3e8e41;
          }}
        </style>
      </head>
      <body>
        <button class="copy-button" id="copyBtn" onclick="copyText()">Enviar y Copiar</button>
        <script>
          function copyText() {{
              var text = `{mensaje}`;
              navigator.clipboard.writeText(text).then(function() {{
                  var btn = document.getElementById('copyBtn');
                  btn.innerText = 'Copiado!';
                  setTimeout(function() {{
                    btn.innerText = 'Enviar y Copiar';
                  }}, 2000);
              }}, function(err) {{
                  console.error('Error al copiar: ', err);
              }});
          }}
        </script>
      </body>
    </html>
    """
    components.html(copy_button_html, height=120)

    # --- Edición de cotización por búsqueda ---
    st.subheader("✏️ Buscar para Editar")
    busqueda = st.text_input("Buscar por teléfono o nombre")
    if busqueda:
        df_result = df[
            df["telefono"].str.contains(busqueda, case=False, na=False) |
            df["nombre_cliente"].str.contains(busqueda, case=False, na=False)
        ]
        if df_result.empty:
            st.warning("No se encontraron coincidencias.")
        else:
            seleccion = st.selectbox(
                "Selecciona para editar:",
                df_result["id"].astype(str) + " - " + df_result["telefono"].fillna("")
            )
            selected_id = int(seleccion.split(" - ")[0])
            fila = df[df["id"] == selected_id].iloc[0]
            with st.form("form_editar"):
                fecha_inicio = st.date_input("Fecha inicio", value=pd.to_datetime(fila["fecha_inicio"]).date())
                nombre = st.text_input("Nombre cliente", value=fila["nombre_cliente"] or "")
                correo = st.text_input("Correo", value=fila["correo"] or "")
                telefono = st.text_input("Teléfono", value=fila["telefono"] or "")
                auto = st.text_input("Auto", value=fila["auto"] or "")
                link_auto = st.text_input("Link del auto", value=fila["link_auto"] or "")
                observacion = st.text_area("Observación", value=fila["observacion"] or "")
                fecha_ultimo = st.date_input("Fecha último contacto", value=pd.to_datetime(fila["fecha_ultimo_contacto"]).date())
                visita = st.date_input("Visita programada", value=pd.to_datetime(fila["visita_programada"]).date())
                estado = st.selectbox(
                    "Estado",
                    ["Pendiente", "Visitado", "Cerrado", "Otro"],
                    index=["Pendiente", "Visitado", "Cerrado", "Otro"].index(fila["estado"] or "Pendiente")
                )
                boton_actualizar = st.form_submit_button("Guardar cambios")
            if boton_actualizar:
                whatsapp = f"https://wa.me/56{telefono.strip()}"
                data = (
                    fecha_inicio.isoformat(), nombre.strip(), correo.strip(), telefono.strip(),
                    auto.strip(), observacion.strip(), fecha_ultimo.isoformat(),
                    visita.isoformat(), estado, whatsapp,
                    link_auto.strip()
                )
                actualizar_cotizacion(selected_id, data)
                st.success("✅ Cotización actualizada.")
                st.rerun()
            st.markdown("---")
            st.warning("¿Deseas eliminar esta cotización? Esta acción no se puede deshacer.")
            if st.button("🗑️ Eliminar cotización"):
                eliminar_cotizacion(selected_id)
                st.success("✅ Cotización eliminada.")
                st.rerun()

elif opcion == "Exportar":
    st.info("Funcionalidad en desarrollo.")

elif opcion == "Gestión de Mensajes":
    from utils.db_utils import insertar_mensaje, eliminar_mensaje, actualizar_mensaje
    st.header("💬 Gestión de Mensajes de WhatsApp")
    st.subheader("📋 Mensajes existentes")
    mensajes = obtener_mensajes_whatsapp()
    if not mensajes:
        st.info("No hay mensajes guardados.")
    else:
        for mid, nombre, texto, desc in mensajes:
            with st.expander(f"✏️ {nombre}"):
                nuevo_nombre = st.text_input(f"Nombre mensaje {mid}", value=nombre, key=f"nombre_{mid}")
                nueva_desc = st.text_input(f"Descripción {mid}", value=desc or "", key=f"desc_{mid}")
                nuevo_texto = st.text_area(f"Texto {mid}", value=texto, height=200, key=f"texto_{mid}")
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button(f"💾 Guardar cambios {mid}"):
                        actualizar_mensaje(mid, nuevo_nombre, nuevo_texto, nueva_desc)
                        st.success("Mensaje actualizado.")
                        st.rerun()
                with col2:
                    if st.button(f"🗑️ Eliminar mensaje {mid}"):
                        eliminar_mensaje(mid)
                        st.warning("Mensaje eliminado.")
                        st.rerun()
    st.markdown("---")
    st.subheader("➕ Agregar nuevo mensaje")
    with st.form("nuevo_mensaje"):
        nombre_nuevo = st.text_input("Nombre")
        desc_nuevo = st.text_input("Descripción")
        texto_nuevo = st.text_area("Mensaje", height=200)
        boton_nuevo = st.form_submit_button("Agregar")
        if boton_nuevo:
            if not nombre_nuevo or not texto_nuevo:
                st.warning("Nombre y mensaje son obligatorios.")
            else:
                insertar_mensaje(nombre_nuevo, texto_nuevo, desc_nuevo)
                st.success("Mensaje agregado correctamente.")
                st.rerun()
