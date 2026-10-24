# ALKIMIA POS 2.0

Punto de venta de escritorio construido con Python, customtkinter y Supabase (PostgreSQL).

## Requisitos

- Python 3.10 o superior
- Cuenta y proyecto de Supabase

## Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuración

1. Copiar `.env.example` a `.env` y completar:

```
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-anon-key
APP_TITLE=ALKIMIA POS
```

2. En el panel de Supabase, abrir **SQL Editor**, pegar el contenido de
   `supabase/schema.sql` y ejecutarlo. Crea las tablas, políticas y la función
   `register_sale`.

3. Ejecutar también `supabase/updates.sql` para habilitar la tabla de versiones
   que usa la autoactualización.

4. Verificar la conexión:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_test.py
```

## Ejecución

```powershell
.\.venv\Scripts\python.exe main.py
```

## Uso

- **Caja**: escribir código de barras, código interno o nombre y presionar ENTER.
- **F3**: editar la cantidad del producto seleccionado.
- **F5**: buscar producto por coincidencia.
- **F7** (o clic en el botón): alterna entre `MODO: Normal` y `MODO: Mesa`.
  En `MODO: Mesa` el botón se pone verde y se usa el precio mayoreo.
- **F9**: cobrar el ticket.
- **F10**: abrir el corte de caja.
- **Supr**: quitar la fila seleccionada del ticket.
- **Doble clic en una fila del ticket**: editar la cantidad.
- **Inventario**: agregar, editar, eliminar y buscar productos.
- **Corte de caja**: resumen de las ventas del día (se guarda en Supabase).
- **Historial de cortes**: exportar a CSV o PDF.
- **Configuración**: nombre del negocio, usuario, moneda, pie de ticket y
  búsqueda manual de actualizaciones.

## Datos del usuario

- `%LOCALAPPDATA%\ALKIMIA\auth.json`: usuario y contraseña local (hash PBKDF2).
- `%LOCALAPPDATA%\ALKIMIA\.env` (opcional): permite sobreescribir la configuración
  de Supabase sin recompilar.
- `%LOCALAPPDATA%\ALKIMIA\logs\alkimia.log`: log de errores (rotativo, 512 KB × 4).
- Las actualizaciones y desinstalaciones no borran estos archivos.

## Compilar el instalador

1. Instalar las dependencias de desarrollo:

```powershell
pip install -r requirements-dev.txt
```

2. Instalar [Inno Setup 6](https://jrsoftware.org/isdl.php).

3. Ejecutar:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build.ps1
```

El script genera:

- `dist\ALKIMIA\ALKIMIA.exe` — aplicación.
- `dist\installer\ALKIMIA-Setup-X.Y.Z.exe` — instalador por usuario, sin admin.
- `dist\installer\release.json` — versión, tamaño y SHA-256 del instalador.

## Publicar una actualización

1. Subir `APP_VERSION` en `app/version.py`.
2. Compilar el instalador con `scripts\build.ps1`.
3. Subir el instalador a un bucket público `releases` de Supabase Storage o a
   GitHub Releases y copiar la URL directa del archivo.
4. Insertar la versión en la tabla `app_releases`:

```sql
insert into public.app_releases
    (version, download_url, sha256, notes, mandatory, min_supported_version)
values
    ('2.0.1',
     'https://TU-PROYECTO.supabase.co/storage/v1/object/public/releases/ALKIMIA-Setup-2.0.1.exe',
     'SHA256_QUE_IMPRIME_EL_BUILD',
     'Correcciones y mejoras.',
     false,
     null);
```

La app consulta la tabla al iniciar (solo en el ejecutable compilado). Si hay
una versión nueva, ofrece descargarla, verifica el SHA-256, ejecuta el
instalador en silencio y vuelve a abrir la aplicación. Si `mandatory` es `true`
o la versión instalada es menor a `min_supported_version`, la actualización se
marca como obligatoria.

En desarrollo se puede probar con **Configuración > Buscar actualizaciones**.

## Estructura

```
main.py                     Punto de entrada
app/auth.py                 Credenciales locales
app/config.py               Variables de entorno y versión
app/paths.py                Rutas de desarrollo, PyInstaller y AppData
app/log.py                  Logging a archivo en AppData
app/version.py              Versión actual (APP_VERSION)
app/db/                     Conexión y repositorios de Supabase
app/services/updates.py     Consulta, descarga y ejecución de actualizaciones
app/ui/                     Ventana principal, vistas y diálogos
alkimia.spec                Configuración de PyInstaller
installer/alkimia.iss       Instalador de Inno Setup
scripts/build.ps1           Compilación de ejecutable e instalador
supabase/schema.sql         Esquema de base de datos
supabase/updates.sql        Tabla de versiones publicadas
scripts/smoke_test.py       Verificación de conexión y tablas
```

## Notas

- La aplicación requiere conexión a internet para consultar y guardar datos.
- El archivo `.env` no se sube al repositorio.
- El login es local; antes de distribuir a terceros asegurarse de tener RLS
  activado en Supabase y nunca incluir la `service_role` key en el cliente.
- Firmar digitalmente el instalador es opcional, pero evita advertencias de
  SmartScreen en Windows.
