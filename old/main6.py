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

# --- Crear un placeholder en el sidebar para el mensaje generado ---
mensaje_placeholder = st.sidebar.empty()

# Resto de la aplicación
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
    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([3, 1.5, 1.5, 2, 3, 3, 2, 2, 1])
    col1.markdown("**Fecha**")
    col2.markdown("**Última vez**")
    col3.markdown("**Visita**")
    col4.markdown("**Nombre**")
    col5.markdown("**Teléfono**")
    col6.markdown("**Auto**")
    col7.markdown("**Enviar**")
    col8.markdown("**Link Auto**")
    col9.markdown("**ID**")

    for index, row in df_paginated.iterrows():
        r_col1, r_col2, r_col3, r_col4, r_col5, r_col6, r_col7, r_col8, r_col9 = st.columns([3, 1.5, 1.5, 2, 3, 3, 2, 2, 1])
        r_col1.write(row["fecha_inicio"])
        r_col2.write(row["fecha_ultimo_contacto"])
        r_col3.write(row["visita_programada"])
        r_col4.write(row["nombre_cliente"])
        r_col5.write(row["telefono"])
        r_col6.write(row["auto"])

        # Genera el mensaje personalizado y la URL de WhatsApp
        mensaje_personalizado = generar_mensaje(row, mensaje_plantilla)
        whatsapp_url = f"https://wa.me/56{row['telefono']}?text={urllib.parse.quote(mensaje_personalizado)}"

        # Botón "Enviar": actualiza el mensaje en session_state y abre WhatsApp con el mensaje
        if r_col7.button("Enviar", key=f"enviar_{row['id']}"):
            st.session_state['mensaje_generado'] = mensaje_personalizado
            custom_html = f"""
            <html>
              <head>
                <meta charset="utf-8">
                <style>
                  .send-feedback {{
                    padding: 5px;
                    font-size: 14px;
                    color: green;
                    text-align: center;
                  }}
                </style>
              </head>
              <body>
                <script>
                  function copyToClipboard(text) {{
                    var textArea = document.createElement("textarea");
                    textArea.style.position = 'fixed';
                    textArea.style.top = 0;
                    textArea.style.left = 0;
                    textArea.style.width = '2em';
                    textArea.style.height = '2em';
                    textArea.style.padding = 0;
                    textArea.style.border = 'none';
                    textArea.style.outline = 'none';
                    textArea.style.boxShadow = 'none';
                    textArea.style.background = 'transparent';
                    textArea.value = text;
                    document.body.appendChild(textArea);
                    textArea.select();
                    try {{
                      var successful = document.execCommand('copy');
                      console.log('Texto copiado: ', successful);
                    }} catch (err) {{
                      console.error('Error al copiar: ', err);
                    }}
                    document.body.removeChild(textArea);
                  }}
                  copyToClipboard(`{mensaje_personalizado}`);
                  window.open("{whatsapp_url}", "_blank");
                </script>
                <div class="send-feedback">Mensaje copiado y WhatsApp abierto.</div>
              </body>
            </html>
            """
            with r_col7:
                components.html(custom_html, height=60)
        r_col9.write(row["id"])

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

# --- Actualizar el placeholder del sidebar con el mensaje generado ---
mensaje = st.session_state.get('mensaje_generado', 'No hay mensaje generado.')
html_mensaje = f"""
<div style="border:1px solid #ddd; padding:10px; background-color:#3a1919; font-family: monospace; margin-top:10px;">
  <h4 style="margin-bottom:5px;">Mensaje Generado</h4>
  <pre id="mensaje" style="white-space: pre-wrap; word-wrap: break-word;">{mensaje}</pre>
  <!-- Campo oculto para copia -->
  <textarea id="copyArea" style="position: absolute; left: -9999px;">{mensaje}</textarea>
  <button onclick="(function() {{
      var copyArea = document.getElementById('copyArea');
      copyArea.select();
      try {{
         var successful = document.execCommand('copy');
         alert(successful ? 'Mensaje copiado.' : 'Error al copiar.');
      }} catch(err) {{
         alert('Error al copiar: ' + err);
      }}
  }})()" style="margin-top:10px; width:100%;">Copiar mensaje</button>
</div>
"""
mensaje_placeholder.markdown(html_mensaje, unsafe_allow_html=True)
