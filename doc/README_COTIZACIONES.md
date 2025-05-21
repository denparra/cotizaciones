📘 SISTEMA DE COTIZACIONES – HOJA DE VIDA DEL PROYECTO
Este sistema permite registrar y gestionar cotizaciones de clientes interesados en vehículos, funcionando como una agenda personal para seguimiento comercial.
El sistema es local, basado en SQLite y con interfaz hecha en Streamlit.

🧩 MÓDULOS DEL SISTEMA
1. 🗂️ Base de Datos (SQLite)
Tablas utilizadas:

cotizaciones
Campos:

id (INTEGER, PK, AUTOINCREMENT)

fecha_inicio (TEXT)

nombre_cliente (TEXT)

correo (TEXT)

telefono (TEXT, NOT NULL)

auto (TEXT)

link_auto (TEXT) ← Nuevo campo para almacenar el link del auto cotizado

observacion (TEXT)

fecha_ultimo_contacto (TEXT)

visita_programada (TEXT)

estado (TEXT)

whatsapp_link (TEXT)

mensajes_whatsapp
Campos:

id (INTEGER, PK, AUTOINCREMENT)

nombre (TEXT NOT NULL)

mensaje (TEXT NOT NULL)

descripcion (TEXT)

🔒 Validación: sólo telefono es obligatorio en cotizaciones.

2. 🧾 Ingreso de Cotizaciones
Formulario para ingresar cada cotización manualmente.

Validación del campo telefono.

Se incluye el campo adicional: link_auto (para el enlace del auto).

Generación automática del link WhatsApp:
https://wa.me/56NUMERO

Limpieza automática del formulario tras guardar.

Prevención de duplicados por doble clic (usando st.rerun()).

3. 📋 Visualización y Filtros
Tabla de registros con filtros por:

Nombre cliente

Teléfono

Auto

Visualización en modo tabla con paginación y columnas extendidas.

Se muestran enlaces clicables en las columnas whatsapp_link y link_auto.

Columna dinámica para envío de mensajes personalizados en WhatsApp, utilizando plantillas con placeholders:

{{NOMBRE}}, {{AUTO}}, {{LINK_AUTO}}.

4. 🛠️ Edición y Eliminación
Búsqueda de cotizaciones por nombre o teléfono.

Formulario editable para cada registro, incluyendo el campo link_auto.

Actualización de la base de datos y recarga automática tras guardar.

Botón de eliminación con confirmación visual.

Eliminación física del registro desde SQLite.

5. 📤 Exportación
Exportación de registros filtrados a Excel (.xlsx).

Generación y descarga automática del archivo exportado.

A futuro: Exportación a PDF.

6. 🔔 Recordatorios y Seguimiento
Filtros automáticos para:

Visitas programadas para hoy.

Visitas programadas para la semana.

Clientes sin contacto en más de 7 días.

7. 💬 Botón WhatsApp
Si el número está registrado, se muestra un botón directo a WhatsApp Web.

Compatible con WhatsApp Desktop si la sesión está iniciada en el navegador.

El mensaje enviado se genera reemplazando los placeholders en la plantilla seleccionada.

8. 📨 Gestión de Mensajes WhatsApp
Sección desde el menú lateral para:

Ver todos los mensajes disponibles.

Editar nombre, descripción y texto de cada mensaje.

Eliminar mensajes.

Agregar nuevos mensajes mediante formulario.

Los mensajes sirven como plantillas para personalizar el contenido enviado vía WhatsApp.

9. 📋 Actualizaciones Recientes y Mejoras en la Interfaz
Botón "Copiar mensaje" en el Sidebar:
Ahora se utiliza un componente HTML embebido en el sidebar con la API moderna de Clipboard (navigator.clipboard.writeText) para copiar el mensaje generado.
Se ha aumentado la altura del componente y se han ajustado estilos para asegurar que el botón no pierda foco ni se superponga.

Modularización del Código:
Se ha refactorizado la lógica de generación y envío de mensajes para separar funciones y mejorar la legibilidad. Esto facilita futuras ampliaciones y el mantenimiento del código.

Ajustes en la Visualización:
Se han añadido controles para la paginación y filtros automáticos, permitiendo al usuario visualizar un subconjunto de registros de forma clara y ordenada.

⚙️ Tecnologías Usadas
Python 3.8+

Streamlit

SQLite3

Pandas

XlsxWriter

Tabulate (para soporte de .to_markdown())