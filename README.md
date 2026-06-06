# motor_archivos

Subsistema Python independiente de **SIRES** que mantiene sincronizados los catálogos oficiales de salud (SSA / GOBSI / CSG) en la base de datos PostgreSQL del proyecto.

---

## ¿Qué hace?

1. Descarga los catálogos desde los servidores oficiales.
2. Compara el SHA-256 de cada archivo con la última versión descargada — procesa lo que cambió **o** lo que aún no está cargado en la base de datos (tabla vacía o inexistente).
3. Normaliza y transforma los datos (`.xlsx`, `.xls`, `.xlsm`, `.csv`, `.zip`).
4. Sincroniza los registros en PostgreSQL via `INSERT ... ON CONFLICT DO UPDATE` (upsert por lotes de 5 000).

El backend NestJS es dueño del esquema de la base de datos. Este subsistema **solo escribe datos**, no crea ni migra tablas en producción.

---

## Requisitos

- Python 3.12+
- PostgreSQL 14+ (puede estar en otro servidor; solo necesitas las credenciales)

| Paquete | Versión |
|---|---|
| pandas | 2.1.4 |
| openpyxl | 3.1.2 |
| xlrd | 2.0.1 |
| requests | 2.31.0 |
| sqlmodel | 0.0.38 |
| psycopg2-binary | 2.9.12 |
| pydantic-settings | 2.2.1 |

---

## Instalación y uso

### Linux (Ubuntu / Debian)

#### 1. Instalar Python 3.12

```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Verificar
python3.12 --version
```

#### 2. Clonar el repositorio

```bash
git clone <url-del-repo>
cd motor_archivos
```

#### 3. Crear entorno virtual e instalar dependencias

```bash
python3.12 -m venv .venv
source .venv/bin/activate

# El prompt cambia a (.venv) — confirma que el entorno está activo
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configurar variables de entorno

```bash
cp .env.example .env    # si existe, o créalo manualmente
nano .env               # o cualquier editor de texto
```

Contenido del `.env`:

```env
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nest_project

# Opcionales
LOG_LEVEL=INFO         # DEBUG, INFO, WARNING, ERROR, CRITICAL (por defecto INFO)
LOINC_USER=            # solo para descargar el catálogo LOINC (Basic Auth)
LOINC_PASSWORD=
```

> Tienes la plantilla completa en `.env.example`: cópiala con `cp .env.example .env` y rellena los valores.

#### 5. Ejecutar

```bash
python scripts/cargar_catalogos.py
```

Los logs aparecen en consola y en `logs/ejecucion.log`.

> Para ejecutarlo sin activar el venv cada vez: `.venv/bin/python scripts/cargar_catalogos.py`

---

### macOS

#### 1. Instalar Homebrew y Python 3.12

```bash
# Instalar Homebrew si no lo tienes
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar Python 3.12
brew install python@3.12

# Verificar
python3.12 --version
```

#### 2. Clonar el repositorio

```bash
git clone <url-del-repo>
cd motor_archivos
```

#### 3. Crear entorno virtual e instalar dependencias

```bash
python3.12 -m venv .venv
source .venv/bin/activate

# El prompt cambia a (.venv)
pip install --upgrade pip
pip install -r requirements.txt
```

> **Apple Silicon (M1/M2/M3):** si `psycopg2-binary` falla al instalar, ejecuta primero:
> ```bash
> brew install libpq
> export LDFLAGS="-L/opt/homebrew/opt/libpq/lib"
> export CPPFLAGS="-I/opt/homebrew/opt/libpq/include"
> pip install psycopg2-binary
> ```

#### 4. Configurar variables de entorno

```bash
nano .env
```

Contenido del `.env`:

```env
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nest_project

# Opcionales
LOG_LEVEL=INFO         # DEBUG, INFO, WARNING, ERROR, CRITICAL (por defecto INFO)
LOINC_USER=            # solo para descargar el catálogo LOINC (Basic Auth)
LOINC_PASSWORD=
```

> Tienes la plantilla completa en `.env.example`: cópiala con `cp .env.example .env` y rellena los valores.

#### 5. Ejecutar

```bash
python scripts/cargar_catalogos.py
```

Los logs aparecen en consola y en `logs/ejecucion.log`.

---

### Windows

#### 1. Instalar Python 3.12

1. Descarga el instalador desde **python.org/downloads** (versión 3.12.x, Windows installer 64-bit).
2. Ejecuta el instalador y **marca** la opción **"Add Python to PATH"** antes de continuar.
3. Verifica en PowerShell:

```powershell
python --version
```

#### 2. Clonar el repositorio

```powershell
git clone <url-del-repo>
cd motor_archivos
```

#### 3. Crear entorno virtual e instalar dependencias

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la ejecución del script de activación:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Luego vuelve a activar:
.venv\Scripts\Activate.ps1
```

Con el entorno activo (el prompt muestra `(.venv)`):

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

> Con `cmd` en lugar de PowerShell, la activación es `.venv\Scripts\activate.bat`.

#### 4. Configurar variables de entorno

Crea el archivo `.env` en la raíz del proyecto con cualquier editor de texto (Bloc de notas, VS Code, etc.):

```env
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nest_project

# Opcionales
LOG_LEVEL=INFO         # DEBUG, INFO, WARNING, ERROR, CRITICAL (por defecto INFO)
LOINC_USER=            # solo para descargar el catálogo LOINC (Basic Auth)
LOINC_PASSWORD=
```

> Tienes la plantilla completa en `.env.example`: cópiala con `cp .env.example .env` y rellena los valores.

#### 5. Ejecutar

```powershell
python scripts\cargar_catalogos.py
```

Los logs aparecen en consola y en `logs\ejecucion.log`.

> **Nota:** En Windows la primera ejecución puede tardar más por el antivirus al acceder a múltiples archivos `.xlsx` descargados.

---

## Ejecuciones posteriores

Desde la segunda ejecución en adelante, el script solo descarga y procesa los catálogos cuyos archivos en el servidor oficial hayan cambiado (comparación SHA-256). Si ningún catálogo cambió, termina en segundos sin tocar la base de datos.

```bash
# Linux / macOS — activar el venv si no está activo
source .venv/bin/activate
python scripts/cargar_catalogos.py

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
python scripts\cargar_catalogos.py
```

> **Nota temporal:** `iniciar_bd()` crea las tablas automáticamente si no existen. Esto es solo para desarrollo local — en producción NestJS gestiona el esquema y esta llamada debe eliminarse.

---

## Uso

```bash
python scripts/cargar_catalogos.py
```

Eso es todo. El script detecta qué catálogos cambiaron, los descarga, los procesa y los carga. Si nada cambió desde la última ejecución, termina sin hacer nada.

Los logs se escriben en consola y en `logs/ejecucion.log`.

> **Nota temporal:** `iniciar_bd()` crea las tablas automáticamente si no existen. Esto es solo para desarrollo local — en producción NestJS gestiona el esquema y esta llamada debe eliminarse.

---

## Logs y auditoría

### Configuración del log

- **Salida doble:** consola (coloreada) + archivo `logs/ejecucion.log`.
- **Nivel configurable** vía `LOG_LEVEL` en el `.env` (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). Por defecto `INFO`.
- **Rotación automática:** el archivo rota al llegar a 5 MB y conserva hasta 5 históricos (`ejecucion.log.1` … `.5`), así no crece sin límite (`RotatingFileHandler` en `helpers/logger.py`).

### Formato de las líneas

```
[2026-06-06 12:00:00] [ERROR] [extractor.py:42]: [loinc:descarga] Sincronizacion fallida
```

Cada corrida de sincronización se delimita con marcadores y un `run_id` corto, y los mensajes del flujo llevan el prefijo `[catalogo:fase]` (fases: `descarga`, `comparacion`, `materializacion`, `bd`):

```
[...] [INFO] [...]: === INICIO sincronización run=a1b2c3d4 ===
[...] [INFO] [...]: === FIN sincronización run=a1b2c3d4 ===
```

### Auditor de logs

`scripts/auditor.py` lee `logs/ejecucion.log` y permite filtrar para responder rápido *"¿qué falló y cuándo?"*:

```bash
python -m scripts.auditor --nivel ERROR          # solo errores
python -m scripts.auditor --catalogo loinc       # solo un catálogo
python -m scripts.auditor --nivel ERROR --hoy    # errores de hoy
python -m scripts.auditor --resumen              # qué catálogos fallaron
```

> Se ejecuta como módulo (`python -m scripts.auditor`, con puntos y sin `.py`) para que los imports del proyecto resuelvan bien.

---

## Estructura del proyecto

```
motor_archivos/
├── .env                        # Conexión a Postgres + LOG_LEVEL + LOINC (no versionado)
├── .env.example                # Plantilla de variables de entorno
├── requirements.txt
├── setup.sh
│
├── data/                       # Modelos SQLModel → tablas Postgres
│   ├── config.py               # Carga variables de entorno via pydantic-settings
│   ├── constants.py            # URLs de los catálogos oficiales
│   ├── db.py                   # Engine SQLAlchemy + iniciar_bd() (temporal, solo dev)
│   ├── clinico.py              # Diagnostico, Procedimiento, Loinc
│   ├── demografia.py           # LenguaIndigena, Religion, Formacion, Nacionalidad
│   ├── geografia.py            # EntidadFederativa, Municipio, Localidad, CodigoPostal, CLUES
│   └── insumos.py              # Medicamento
│
├── helpers/
│   ├── extractor.py            # Descarga de archivos (SSL whitelist) + extracción de ZIPs
│   ├── hasher.py               # SHA-256 para comparación de versiones
│   ├── parser.py               # Detección de modelo por regex + lectura de archivos
│   ├── sanitizer.py            # Normalización de DataFrames + transformers por catálogo
│   ├── scanner.py              # Utilidades de escaneo de directorios
│   └── logger.py               # Logger coloreado en consola + archivo rotado logs/ejecucion.log
│
├── scripts/
│   ├── cargar_catalogos.py     # Punto de entrada — orquesta todo el proceso
│   ├── sincronizador.py        # Descarga + comparación de hashes (marca inicio/fin de corrida)
│   ├── auditor.py              # Audita logs/ejecucion.log (filtros por nivel/catálogo/fecha)
│   └── pipeline.py             # ETL por archivo → bulk upsert en PostgreSQL
│
├── descargas/                  # Archivos descargados (no versionados)
│   ├── *_origen.{xlsx|xls|xlsm|zip}
│   ├── temporales/             # Archivos temporales para comparación de hashes
│   └── *_extraido/             # Contenido extraído de ZIPs
│
└── logs/
    ├── ejecucion.log           # log actual
    └── ejecucion.log.1 … .5    # históricos rotados (5 MB c/u, máx. 5)
```

---

## Catálogos

| Clave | Descripción | Formato | Estado |
|---|---|---|---|
| `diagnosticos` | CIE-10 DGIS | ZIP → XLSX | ✅ |
| `procedimiento` | CIE-9-MC DGIS | XLSX | ✅ |
| `entidad_federativa` | Entidades federativas | XLSX | ✅ |
| `municipio` | Municipios | XLSX | ✅ |
| `localidades` | Localidades (296 k filas) | XLSX | ✅ |
| `lenguas_indigenas` | Lenguas indígenas | XLSX | ✅ |
| `formacion_academica` | Formación académica del personal de salud | XLSX | ✅ |
| `nacionalidades` | Países / nacionalidades | ZIP → XLSX | ✅ |
| `religion` | Catálogo de religiones | XLSX | ✅ |
| `codigo_postal` | Códigos postales — Correos de México (32 hojas/estado) | XLS | ✅ |
| `medicamentos` | Compendio Nacional de Insumos (CSG) | XLSM | ✅ SSL relajado¹ |
| `clues` | Establecimientos de salud CLUES | XLSX | ✅ |
| `loinc` | LOINC (Regenstrief) | ZIP → CSV | ✅ Descarga autenticada² |
| `cif` | CIF-IA | XLSX | ⏳ Sin modelo |

> ¹ `csg.gob.mx` tiene certificado SSL inválido — la descarga se hace con `verify=False` (whitelist explícita en `extractor.py`).
>
> ² LOINC requiere registro en loinc.org. La descarga es automática vía Basic Auth en dos pasos: el endpoint devuelve metadata JSON con la URL real del ZIP, que se descarga con las credenciales `LOINC_USER` / `LOINC_PASSWORD` del `.env` (ver `_CATALOGOS_CON_AUTH` y `_RESOLVEDORES_URL` en `sincronizador.py`).

---

## Flujo de datos

```
URLs oficiales SSA / GOBSI / CSG
        │
        ▼
sincronizador.py
  ├── Descarga → descargas/temporales/*
  ├── SHA-256 nuevo vs SHA-256 guardado
  │     ├── Cambio detectado → reemplaza archivo final → (si .zip) extrae contenido
  │     └── Sin cambios → verifica la tabla en la BD
  │           ├── Con datos → omite catálogo
  │           └── Vacía / inexistente → re-procesa (modelo nuevo o tabla borrada)
  └── Devuelve lista de archivos a procesar
        │
        ▼  ordenados: entidades → municipios → localidades → resto
        │
        ▼  por cada archivo
pipeline.py  insertar_bd()
  ├── obtener_modelo()         — regex sobre nombre de archivo → clase SQLModel
  ├── procesar_archivo()       — dtype=str, keep_default_na=False; XLS multi-hoja; ZIP parcheado
  ├── normalizar_dataframe()   — columnas sin tildes/espacios, llaves normalizadas, NaN → None
  ├── transformar_para_modelo() — campos tipados según catálogo (enums, Int64, bools)
  └── INSERT … ON CONFLICT DO UPDATE
        — lotes de 5 000 filas, commit por lote
        │
        ▼
   PostgreSQL (nest_project)
```

---

## Modelos de datos

### Clínico

| Modelo | Tabla | PK | Notas |
|---|---|---|---|
| `Diagnostico` | `diagnostico` | `catalog_key` | CHECK constraints en sexo y unidades de edad; banderas NOM-024 Apéndice A |
| `Procedimiento` | `procedimiento` | `catalog_key` | `drop_duplicates` por `catalog_key`; sexo codificado numéricamente en origen |
| `Loinc` | `loinc` | `loinc_num` | Descarga autenticada en 2 pasos; columnas mapeadas vía `_ALIAS_COLUMNAS` |

### Demografía

| Modelo | Tabla | PK |
|---|---|---|
| `LenguaIndigena` | `lenguas_indigenas` | `clave_lengua` |
| `Religion` | `religiones` | `clave_religion` |
| `Formacion` | `formaciones` | `catalog_key` |
| `Nacionalidad` | `nacionalidades` | `codigo_pais` |

### Geografía

| Modelo | Tabla | PK | Notas |
|---|---|---|---|
| `EntidadFederativa` | `cat_entidades_federativas` | `catalog_key` | |
| `Municipio` | `cat_municipios` | `cvegeo` | Clave geoestadística INEGI (entidad + municipio) |
| `Localidad` | `cat_localidades` | `cvegeo` | Clave geoestadística INEGI; `cvegeo` de 9 díg reconstruido en `transformar_localidad` (el origen pierde el cero inicial en entidades 01–09) |
| `CodigoPostal` | `codigos_postales` | `(c_estado, c_mnpio, id_asenta_cpcons)` | PK compuesta; 15 campos del catálogo de Correos |
| `CLUES` | `cat_establecimientos_clues` | `clues` | `municipio_cvegeo` / `localidad_cvegeo` concatenados en `transformar_clues` para casar con las tablas geográficas |

### Insumos

| Modelo | Tabla | PK |
|---|---|---|
| `Medicamento` | `cat_medicamentos` | `clave` |

---

## Decisiones de diseño relevantes

**Por qué `INSERT ON CONFLICT DO UPDATE` y no `session.merge()`**
`merge()` hace un SELECT por fila antes de insertar — 296 k localidades tardaban ~10 minutos. El upsert masivo las carga en ~2 minutos.

**Por qué `cvegeo` como PK en Municipio y Localidad**
La clave geoestadística del INE es el identificador único oficial y el que usan otras fuentes de datos del sector salud. `catalog_key` es el código DGIS y se mantiene como campo indexado adicional.

**Por qué sexo y unidades de edad se almacenan como `str` y no como tipo ENUM de PostgreSQL**
Evita que SQLAlchemy cree tipos ENUM nativos en Postgres, que son difíciles de modificar cuando NestJS toma el control del esquema. Los enums Python (`RestriccionSexo`, `UnidadEdad`) se usan para validación interna y como fuente de los CHECK constraints.

**Por qué comparación de hashes antes de procesar**
Evita re-procesar 296 k localidades (y demás catálogos grandes) en cada ejecución. El ETL solo se activa cuando el servidor GOBSI publica una nueva versión del archivo.

**Por qué la sincronización también consulta la base de datos**
El hash por sí solo asume que "archivo en disco = datos en la BD". Eso falla al agregar un modelo nuevo cuyo archivo ya estaba descargado, o cuando una tabla se borra/trunca manualmente: el catálogo se reportaría "sin cambios" y nunca se cargaría. Por eso, en la rama "sin cambios", `sincronizar_en_disco` verifica además si la tabla destino está vacía o no existe (`_tabla_pendiente`) y la recarga si hace falta. El motor queda auto-reparable.

**Por qué se reconstruye el `cvegeo` de localidades**
La columna `CVEGEO` del archivo de localidades pierde el cero inicial en las entidades 01–09 (Excel la guarda como número), generando PKs de 8 dígitos que no casan con el resto de claves geográficas (`Municipio`, `CLUES`). `transformar_localidad` reconstruye el cvegeo canónico de 9 dígitos desde las claves componentes (entidad + municipio + localidad).

**Parche de `font family` en archivos XLSX del gobierno**
Algunos archivos XLSX oficiales usan valores de familia de fuente (`<family val="34"/>`) que openpyxl rechaza aunque Excel los acepta. `parser.py` detecta el error y aplica un parche en memoria al ZIP (clampea los valores a 14 en `xl/sharedStrings.xml` y `xl/styles.xml`) sin modificar el archivo original en disco.

---

## Pendientes

| Tarea | Prioridad | Detalle |
|---|---|---|
| Eliminar `iniciar_bd()` | Alta | NestJS gestiona el esquema en producción; esta función es solo para desarrollo local |
| Modelo `CIF` | Media | Header en fila 3: columnas `Código` / `Descripción` |
| Validación post-descarga | Media | Verificar magic bytes (`PK\x03\x04`) para detectar respuestas HTML de error disfrazadas de XLSX |
| Transformer LOINC dedicado | Baja | LOINC ya carga vía el mapa de alias de `normalizar_dataframe`; un `transformar_loinc()` formalizaría `status` / `scale_typ` como enums |
| Migración a Alembic | Baja | Cuando NestJS tome el esquema completo |
