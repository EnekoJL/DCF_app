"""All user-visible GUI texts (Spanish). Kept in one module to ease future i18n."""

APP_TITLE = "Sevcon DCF Diff — Comparador de configuraciones Gen4"

FILE_A_TITLE = "Archivo base (A)"
FILE_B_TITLE = "Archivo nuevo (B)"
FILE_NONE = "Ningún archivo seleccionado"
BROWSE = "Examinar…"
SWAP = "⇄"
COMPARE = "Comparar"
COMPARING = "Comparando…"
DCF_FILETYPES = (("Ficheros DCF", "*.dcf"), ("Todos los ficheros", "*.*"))
OPEN_DCF = "Seleccionar fichero DCF"

CARD_RELEVANT = "Cambios relevantes"
CARD_MOTOR = "★ Control de motor"
CARD_NOISE = "Monitorización (ocultos)"
CARD_CHECKSUM = "Checksum A / B"
CHECKSUM_EQUAL = "igual"
CHECKSUM_DIFFERS = "difiere"
FIRMWARE_WARNING = "⚠ Distinto: {a} → {b}"
FIRMWARE_OK = "{rev} (igual en A y B)"
CARD_FIRMWARE = "Revisión de firmware"

GROUPS_TITLE = "Grupos"
GROUP_ALL = "Todos"
GROUP_MOTOR = "★ Control de motor"
SEARCH_PLACEHOLDER = "Buscar objeto, nombre o descripción…"
SHOW_NOISE = "Mostrar monitorización"
MOTOR_ONLY = "Solo control de motor"

COL_KEY = "Objeto"
COL_NAME = "Parámetro"
COL_GROUP = "Grupo"
COL_A = "Valor A"
COL_B = "Valor B"
COL_DELTA = "Δ"
COL_UNITS = "Unidad"
MISSING_VALUE = "(no existe)"
KIND_ADDED = "AÑADIDO"
KIND_REMOVED = "ELIMINADO"
ROWS_SHOWN = "{shown} de {total} cambios"

DETAIL_TITLE = "Detalle"
DETAIL_EMPTY = "Selecciona un cambio para ver el detalle."
DETAIL_DESCRIPTION = "Descripción Sevcon"
DETAIL_NO_DESCRIPTION = "(sin descripción en el DCF)"
DETAIL_GROUP = "Grupo"
DETAIL_KIND = "Tipo de cambio"
DETAIL_VALUE_A = "Valor A"
DETAIL_VALUE_B = "Valor B"
DETAIL_RAW_A = "Raw A"
DETAIL_RAW_B = "Raw B"
DETAIL_DELTA = "Δ"
DETAIL_DATA_TYPE = "Tipo de dato"
DETAIL_ACCESS = "Acceso"
DETAIL_ACCESS_LEVEL = "Nivel de acceso"
DETAIL_LIMITS = "Límites [mín, máx]"
DETAIL_DEFAULT = "Valor por defecto"
DETAIL_CATEGORY = "Categoría"
DETAIL_PREOP = "Solo en pre-operacional"
DETAIL_NOISE = "Monitorización"
DETAIL_BITS = "Campos de bits que cambian"
YES = "Sí"
NO = "No"
WARN_OUT_OF_LIMITS = "⚠ Valor {which} fuera de límites [{low}, {high}]"
WARN_NOISE = "Parámetro de monitorización: {reason}"
ACCESS_LEVELS = {
    1: "1 · Usuario",
    2: "2 · Service",
    3: "3 · Dealer",
    4: "4 · OEM Engineering",
    5: "5 · Sevcon",
}
KIND_LABELS = {"modified": "Modificado", "added": "Añadido", "removed": "Eliminado"}

EXPORT_HTML = "Exportar HTML"
EXPORT_PDF = "Exportar PDF"
EXPORT_TITLE = "Guardar informe"
EXPORT_DONE = "Informe guardado en {path}"
EXPORT_FAILED = "No se pudo exportar el informe: {error}"
EXPORT_NOTHING = "Primero compara dos ficheros."
HTML_FILETYPES = (("Informe HTML", "*.html"),)
PDF_FILETYPES = (("Informe PDF", "*.pdf"),)
IMPACT = "Analizar impacto (próximamente)"

APPEARANCE = "Tema"
APPEARANCE_MODES = {"Sistema": "system", "Oscuro": "dark", "Claro": "light"}

STATUS_READY = "Selecciona los dos ficheros y pulsa Comparar."
STATUS_NEED_FILES = "Faltan ficheros: selecciona A y B."
STATUS_DONE = "Comparación terminada: {relevant} cambios relevantes, {noise} de monitorización."
ERROR_TITLE = "Error"
ERROR_COMPARE = "No se pudo comparar: {error}"
