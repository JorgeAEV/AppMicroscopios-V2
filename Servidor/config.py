import os

# --------------------------------------------------------------------
# Configuración del directorio base para guardar imágenes y experimentos
# --------------------------------------------------------------------
# Por defecto usa /home/pi/experimentos, pero se puede cambiar con:
#   export BASE_FOLDER_PATH="/otra/ruta"
# Esto permite que funcione en cualquier Raspberry Pi y cualquier usuario.
# --------------------------------------------------------------------

BASE_FOLDER_PATH = os.environ.get(
    "BASE_FOLDER_PATH",
    os.path.expanduser("~/experimentos")  # ~/ se expande al home del usuario actual
)

# Asegurarnos de que la ruta sea absoluta
BASE_FOLDER_PATH = os.path.abspath(BASE_FOLDER_PATH)

# --------------------------------------------------------------------
# Crear automáticamente el directorio base si no existe
# --------------------------------------------------------------------
try:
    os.makedirs(BASE_FOLDER_PATH, exist_ok=True)
except PermissionError:
    raise SystemExit(
        f"ERROR: No se tiene permiso para crear o acceder a {BASE_FOLDER_PATH}. "
        f"Ejecute el servidor con permisos adecuados o cambie BASE_FOLDER_PATH."
    )
except Exception as e:
    raise SystemExit(f"ERROR: No se pudo preparar el directorio base: {e}")
