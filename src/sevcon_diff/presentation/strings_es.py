"""All user-visible GUI texts (Spanish). Kept in one module to ease future i18n."""

APP_TITLE = "Sevcon DCF Diff — Comparador de configuraciones Gen4"
HEADER_TITLE = "Sevcon DCF Diff"
HEADER_SUBTITLE = "Gen4 Size 6 · Control de motor y límites"

FILE_A_TITLE = "Base (A)"
FILE_B_TITLE = "Nuevo (B)"
FILE_NONE = "Ningún archivo seleccionado"
BROWSE = "Examinar…"
SWAP = "⇄"
COMPARE = "Comparar"
COMPARING = "Comparando…"
DCF_FILETYPES = (("Ficheros DCF", "*.dcf"), ("Todos los ficheros", "*.*"))
OPEN_DCF = "Seleccionar fichero DCF"

HEADLINE_EMPTY = "Sin comparación"
HEADLINE = "{count} cambios"
HEADLINE_ONE = "1 cambio"
HEADLINE_NONE = "Sin cambios"
HEADLINE_SCOPE_FOCUS = "en control de motor y límites"
HEADLINE_SCOPE_ALL = "en todas las áreas"
FIRMWARE_WARNING = "⚠ Firmware distinto: {a} → {b}"
FIRMWARE_OK = "Firmware {rev}"

GROUP_ALL = "Todas las áreas"
SEARCH_PLACEHOLDER = "Buscar parámetro…"
OTHER_AREAS = "Otras áreas ({count})"

COL_NAME = "Parámetro"
COL_A = "Antes (A)"
COL_TREND = ""
COL_B = "Después (B)"
COL_UNITS = "Unidad"
MISSING_VALUE = "—"
KIND_ADDED = "nuevo"
KIND_REMOVED = "eliminado"
OUT_OF_LIMITS = "⚠"
TREND_UP = "▲"
TREND_DOWN = "▼"
TREND_CHANGED = "→"
ROWS_EMPTY = "No hay cambios que mostrar."
HINT_EMPTY = "Selecciona un parámetro para ver su objeto y la descripción de Sevcon."
HINT_OUT_OF_LIMITS = "⚠ Fuera de límites [{low}, {high}]"

EXPORT_HTML = "Exportar HTML"
EXPORT_PDF = "Exportar PDF"
EXPORT_TITLE = "Guardar informe"
EXPORT_DONE = "Informe guardado en {path}"
EXPORT_FAILED = "No se pudo exportar el informe: {error}"
EXPORT_NOTHING = "Primero compara dos ficheros."
HTML_FILETYPES = (("Informe HTML", "*.html"),)
PDF_FILETYPES = (("Informe PDF", "*.pdf"),)

APPEARANCE_MODES = {"Sistema": "system", "Oscuro": "dark", "Claro": "light"}

STATUS_READY = "Selecciona los dos ficheros y pulsa Comparar."
STATUS_NEED_FILES = "Faltan ficheros: selecciona A y B."
STATUS_DONE = "Comparación terminada."
ERROR_TITLE = "Error"
ERROR_COMPARE = "No se pudo comparar: {error}"
