# motor_archivos

Subsistema Python independiente de **SIRES** que mantiene sincronizados los catálogos oficiales de salud (SSA / GOBSI / CSG) en la base de datos PostgreSQL del proyecto.

---

## ¿Qué hace?

1. Descarga los catálogos desde los servidores oficiales.
2. Compara el SHA-256 de cada archivo con la última versión descargada — solo procesa lo que cambió.
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
```

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
```

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
```

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

## Estructura del proyecto

```
motor_archivos/
├── .env                        # Conexión a Postgres (no versionado)
├── requirements.txt
├── setup.sh
│
├── data/                       # Modelos SQLModel → tablas Postgres
│   ├── config.py               # Carga variables de entorno via pydantic-settings
│   ├── constants.py            # URLs de los catálogos oficiales
│   ├── db.py                   # Engine SQLAlchemy + iniciar_bd() (temporal, solo dev)
│   ├── clinico.py              # Diagnostico, Procedimiento, Loinc
│   ├── demografia.py           # LenguaIndigena, Religion, Formacion, Nacionalidad
│   ├── geografia.py            # EntidadFederativa, Municipio, Localidad, CodigoPostal
│   └── insumos.py              # Medicamento
│
├── helpers/
│   ├── extractor.py            # Descarga de archivos (SSL whitelist) + extracción de ZIPs
│   ├── hasher.py               # SHA-256 para comparación de versiones
│   ├── parser.py               # Detección de modelo por regex + lectura de archivos
│   ├── sanitizer.py            # Normalización de DataFrames + transformers por catálogo
│   ├── scanner.py              # Utilidades de escaneo de directorios
│   └── logger.py               # Logger coloreado en consola + archivo logs/ejecucion.log
│
├── scripts/
│   ├── cargar_catalogos.py     # Punto de entrada — orquesta todo el proceso
│   ├── sincronizador.py        # Descarga + comparación de hashes
│   └── pipeline.py             # ETL por archivo → bulk upsert en PostgreSQL
│
├── descargas/                  # Archivos descargados (no versionados)
│   ├── *_origen.{xlsx|xls|xlsm|zip}
│   ├── temporales/             # Archivos temporales para comparación de hashes
│   └── *_extraido/             # Contenido extraído de ZIPs
│
└── logs/
    └── ejecucion.log
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
| `cif` | CIF-IA | XLSX | ⏳ Sin modelo |
| `clues` | Establecimientos de salud CLUES | XLSX | ⏳ Sin modelo |
| `loinc` | LOINC (Regenstrief) | CSV | ⏳ Descarga manual² |

> ¹ `csg.gob.mx` tiene certificado SSL inválido — la descarga se hace con `verify=False` (whitelist explícita en `extractor.py`).
>
> ² LOINC requiere registro en loinc.org. La descarga automática está deshabilitada (`_OMITIR_DESCARGA` en `sincronizador.py`).

---

## Flujo de datos

```
URLs oficiales SSA / GOBSI / CSG
        │
        ▼
sincronizador.py
  ├── Descarga → descargas/temporales/*
  ├── SHA-256 nuevo vs SHA-256 guardado
  │     ├── Sin cambios → descarta temporal, omite catálogo
  │     └── Cambio detectado → reemplaza archivo final
  │           └── (si .zip) → extrae contenido
  └── Devuelve lista de archivos modificados
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
| `Loinc` | `loinc` | `loinc_num` | Carga manual |

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
| `Municipio` | `cat_municipios` | `cvegeo` | Clave geoestadística INE |
| `Localidad` | `cat_localidades` | `cvegeo` | Clave geoestadística INE |
| `CodigoPostal` | `codigos_postales` | `(c_estado, c_mnpio, id_asenta_cpcons)` | PK compuesta; 15 campos del catálogo de Correos |

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

**Parche de `font family` en archivos XLSX del gobierno**
Algunos archivos XLSX oficiales usan valores de familia de fuente (`<family val="34"/>`) que openpyxl rechaza aunque Excel los acepta. `parser.py` detecta el error y aplica un parche en memoria al ZIP (clampea los valores a 14 en `xl/sharedStrings.xml` y `xl/styles.xml`) sin modificar el archivo original en disco.

---

## Pendientes

| Tarea | Prioridad | Detalle |
|---|---|---|
| Eliminar `iniciar_bd()` | Alta | NestJS gestiona el esquema en producción; esta función es solo para desarrollo local |
| Modelo `CLUES` | Alta | 68 columnas — analizar `clues_origen.xlsx` y diseñar el modelo con NestJS |
| Modelo `CIF` | Media | Header en fila 3: columnas `Código` / `Descripción` |
| Validación post-descarga | Media | Verificar magic bytes (`PK\x03\x04`) para detectar respuestas HTML de error disfrazadas de XLSX |
| Transformer LOINC | Baja | Agregar `transformar_loinc()` en `sanitizer.py` cuando se integre la carga del CSV |
| Migración a Alembic | Baja | Cuando NestJS tome el esquema completo |
