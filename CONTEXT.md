# CONTEXT — motor_archivos

## Rol dentro de SIRES

`motor_archivos` es un **subsistema Python independiente** del proyecto SIRES. Su única responsabilidad es:

1. Descargar los catálogos oficiales de salud (SSA / GOBSI) desde sus URLs públicas.
2. Leer y normalizar los archivos descargados (`.xlsx`, `.xls`, `.xlsm`, `.csv`, `.zip`).
3. Sincronizar los registros en los **modelos únicos** de la base de datos PostgreSQL que el backend NestJS ya tiene creada (o creará).

El backend de SIRES está hecho en **NestJS** y es el responsable del ciclo de vida de la base de datos (migraciones, creación de tablas, relaciones, etc.). Este subsistema **no gestiona el esquema**, solo escribe datos. La función `iniciar_bd()` en `db.py` existe únicamente como ayuda temporal para pruebas locales y debe eliminarse cuando se integre con el backend real.

---

## Estructura del proyecto

```
motor_archivos/
├── .env                        # Variables de conexión a Postgres (no versionado)
├── .gitignore
├── requirements.txt
├── setup.sh                    # Instala python3-pip + libpq-dev + pip install -r requirements.txt
│
├── data/                       # Modelos SQLModel (mapeo a tablas Postgres)
│   ├── __init__.py             # Exporta todos los modelos + enums + engine + get_session + URLs
│   ├── config.py               # Carga .env con pydantic-settings → objeto Settings
│   ├── constants.py            # URLS_CATALOGOS: dict clave→URL oficial por catálogo
│   ├── db.py                   # Engine SQLAlchemy, get_session, iniciar_bd (temporal)
│   ├── demografia.py           # Modelos: LenguaIndigena, Religion, Formacion, Nacionalidad
│   ├── geografia.py            # Modelos: EntidadFederativa, Municipio, Localidad, CodigoPostal
│   ├── insumos.py              # Modelo: Medicamento
│   └── clinico.py              # Modelos: Diagnostico, Procedimiento, Loinc + enums
│
├── helpers/                    # Utilidades de procesamiento
│   ├── __init__.py             # Re-exporta: log, descargar_archivo, extraer_zip,
│   │                           #   escanear_directorio, buscar_archivo_arbol,
│   │                           #   normalizar_dataframe, obtener_modelo, procesar_archivo
│   ├── logger.py               # Logger con colores ANSI en consola + archivo logs/ejecucion.log
│   ├── extractor.py            # descargar_archivo() con whitelist SSL, extraer_zip()
│   ├── scanner.py              # escanear_directorio() → dict, buscar_archivo_arbol()
│   ├── sanitizer.py            # normalizar_dataframe() genérico + transformers por catálogo
│   └── parser.py               # obtener_modelo() con regex, procesar_archivo() con dtype=str
│
├── scripts/
│   └── cargar_catalogos.py     # Orquestador principal: descarga → parse → transform → upsert
│
├── descargas/                  # Archivos descargados (no versionados, en .gitignore)
│   ├── *_origen.xlsx / .xls    # Archivos tal como se bajan de la fuente oficial
│   ├── *_origen.zip            # ZIPs (diagnósticos, nacionalidades)
│   └── *_extraido/             # Carpetas de extracción de ZIPs
│
└── logs/
    └── ejecucion.log           # Log histórico de ejecuciones (no versionado)
```

---

## Catálogos oficiales (`data/constants.py`)

Fuente: GOBSI / SSA / CSG México. Todos son archivos Excel o ZIP.

| Clave                | Descripción                                    | Formato  | Estado en ETL  |
|----------------------|------------------------------------------------|----------|----------------|
| `diagnosticos`       | Catálogo CIE-10 (DGIS)                         | ZIP→XLSX | ✅ Funcional   |
| `procedimiento`      | Catálogo CIE-9-MC (DGIS)                       | XLSX     | ✅ Funcional   |
| `entidad_federativa` | Entidades federativas                          | XLSX     | ✅ Funcional   |
| `municipio`          | Municipios del territorio nacional             | XLSX     | ✅ Funcional   |
| `localidades`        | Localidades del territorio nacional            | XLSX     | ✅ Funcional   |
| `lenguas_indigenas`  | Lenguas indígenas nacionales                   | XLSX     | ✅ Funcional   |
| `formacion_academica`| Formación académica del personal de salud      | XLSX     | ✅ Funcional   |
| `nacionalidades`     | Nacionalidades / catálogo de países            | ZIP→XLSX | ✅ Funcional   |
| `medicamentos`       | Compendio nacional de insumos (CSG)            | XLSM     | ⚠ SSL relajado |
| `religion`           | Catálogo de religiones (SSA)                   | XLSX     | ❌ Archivo corrupto en origen |
| `codigo_postal`      | Códigos postales (Correos de México vía SSA)   | XLS      | ⚠ Modelo pendiente |
| `cif`                | CIF-IA (Clasificación Internacional Funcionamiento) | XLSX | ⚠ Modelo pendiente |
| `clues`              | Establecimientos de salud (CLUES)              | XLSX     | ⚠ Modelo pendiente (68 cols) |
| ~~`procedimientos`~~ | _(eliminado — era duplicado de `procedimiento`)_ | —      | —              |

> **LOINC** se omite de la descarga automática porque requiere registro manual en loinc.org.

---

## Modelos de datos (`data/`)

### Demografía (`demografia.py`)

| Modelo          | Tabla               | PK             | Campos relevantes                                         |
|-----------------|---------------------|----------------|-----------------------------------------------------------|
| `LenguaIndigena`| `lenguas_indigenas` | `clave_familia`| familia (opcional), clave_grupo, grupo, clave_lengua, lengua_indigena |
| `Religion`      | `religiones`        | `clave_credo`  | credo, clave_grupo, grupo, denominacion, religion         |
| `Formacion`     | `formaciones`       | `catalog_key`  | formacion_academica (opcional), agrupacion, grado         |
| `Nacionalidad`  | `nacionalidades`    | `codigo_pais`  | pais, clave_nacionalidad                                  |

### Geografía (`geografia.py`)

| Modelo              | Tabla                       | PK           | FK / Notas                                        |
|---------------------|-----------------------------|--------------|---------------------------------------------------|
| `EntidadFederativa` | `cat_entidades_federativas` | `catalog_key`| abreviatura NOT NULL (presente en el Excel)       |
| `Municipio`         | `cat_municipios`            | `catalog_key`| efe_key FK → entidades; abreviatura Optional (no está en el Excel fuente) |
| `Localidad`         | `cat_localidades`           | `catalog_key`| municipio_key FK → municipios (alias de MUN_KEY)  |
| `CodigoPostal`      | `codigos_postales`          | `catalog_key`| Modelo pendiente — archivo origen corrupto        |

### Insumos (`insumos.py`)

| Modelo       | Tabla             | PK   | Campos                                |
|--------------|-------------------|------|---------------------------------------|
| `Medicamento`| `cat_medicamentos`| `id` | grupo, clave, insumo, descripcion, indicaciones |

> TODO: cambiar PK de `id` autoincrement a `clave: str` cuando se coordine con NestJS.

### Clínico (`clinico.py`) — refactorizado en Sprint 1

Enums exportados: `RestriccionSexo`, `UnidadEdad`, `LoincScale`, `LoincStatus`.

| Modelo        | Tabla          | PK           | Notas clave                                                     |
|---------------|----------------|--------------|------------------------------------------------------------------|
| `Diagnostico` | `diagnostico`  | `catalog_key`| Enums CHECK constraint; edades como Int64 nullable; banderas Apéndice A NOM-024 |
| `Procedimiento`| `procedimiento`| `catalog_key`| subcategoria Optional (1010 nulls reales); SEX_TYPE numérico 0/1/2 |
| `Loinc`       | `loinc`        | `loinc_num`  | Descarga manual; loinc_class reemplaza `Class`                  |

**Campos de Diagnostico:**
`catalog_key, nombre, clave_capitulo, capitulo, vigente, valido_consulta_externa, valido_afeccion_principal, valido_causa_basica_defuncion, restriccion_sexo, edad_min_valor, edad_min_unidad, edad_max_valor, edad_max_unidad`

**Campos de Procedimiento:**
`catalog_key, nombre, capitulo, seccion, categoria, subcategoria, grupo_lc, tipo_procedimiento, es_principal, restriccion_sexo, edad_min_valor, edad_min_unidad, edad_max_valor, edad_max_unidad`

---

## Helpers (`helpers/`)

### `logger.py`
Logger singleton `log` con colores ANSI en consola (INFO=verde, WARNING=amarillo, ERROR=rojo) y archivo `logs/ejecucion.log`. Formato: `[YYYY-MM-DD HH:MM:SS] [LEVEL] [archivo:linea]: mensaje`.

### `extractor.py`
- `descargar_archivo(url, destino)` → `bool`: descarga por chunks de 8 KB. Deshabilita verificación SSL solo para dominios en `_DOMINIOS_SSL_RELAJADO` (actualmente: `csg.gob.mx`).
- `extraer_zip(ruta_zip, destino)` → `bool`: extrae el ZIP en la carpeta destino.

### `scanner.py`
- `escanear_directorio(ruta)` → `dict{excel, csv, zip, desconocido}`: clasifica archivos recursivamente.
- `buscar_archivo_arbol(ruta, palabra_clave)` → `str | None`: búsqueda case-insensitive por substring.

### `parser.py`
- `obtener_modelo(ruta)` → clase SQLModel: detecta el modelo con regex sobre el nombre del archivo (lista ordenada de tuplas, el primer match gana).
- `procesar_archivo(ruta)` → `pd.DataFrame`: lee `.xlsx`/`.xlsm` (openpyxl), `.xls` (xlrd), `.csv` (utf-8 con fallback ISO-8859-1). Lee todo como `dtype=str` para evitar inferencias erróneas. Elimina filas completamente vacías.

**Mapeo regex → modelo** (en orden de prioridad):
```
diagnostico          → Diagnostico
procedimiento        → Procedimiento
loinc                → Loinc
lengua               → LenguaIndigena
religion             → Religion
formacion            → Formacion
nacionalidad         → Nacionalidad
entidad              → EntidadFederativa
municipio            → Municipio
localidad            → Localidad
codigo[_ ]?postal|^cp_ → CodigoPostal
medicamento          → Medicamento
```

### `sanitizer.py`

**`normalizar_dataframe(df)`** — limpieza genérica para todos los catálogos:
1. Normaliza nombres de columnas: NFKD sin tildes, lowercase, `[\s\.\-]+` → `_`.
2. Alias `mun_key` → `municipio_key`.
3. Normaliza columnas llave (strip, quita `.0` de floats, NULL para valores vacíos).
4. Reemplaza NaN/None → `None` compatible con Postgres.

**Transformaciones específicas por catálogo** (despachadas por `transformar_para_modelo`):

| Transformer               | Tabla         | Qué hace                                           |
|---------------------------|---------------|----------------------------------------------------|
| `transformar_diagnostico` | `diagnostico` | LSEX→enum, LINF/LSUP→edad partida Int64, flags SI/NO→bool |
| `transformar_procedimiento`| `procedimiento`| SEX_TYPE 0/1/2→enum, pro_edad_ia+pro_cve_edia numérico→edad partida, renames |

**Parsers atómicos disponibles:**
- `parse_si_no(raw)` → bool
- `parse_sexo_diagnostico(raw)` → str (maneja texto `HOMBRE`/`MUJER`/`NO`)
- `parse_sexo_procedimiento(raw)` → str (maneja numérico `0`/`1`/`2`)
- `parse_edad_concatenada(raw)` → `(int|None, str|None)` — para CIE-10 (`028D`)
- `parse_edad_separada(valor, unidad)` → `(int|None, str|None)` — para CIE-9-MC (numérico con `_CVE_UNIDAD_EDAD`: 1=A, 2=M, 3=D, 4=H)

---

## Script principal (`scripts/cargar_catalogos.py`)

### `orquestador(carpeta="descargas")`
1. `iniciar_bd()` ⚠ **TEMPORAL**
2. `descargar_catalogos()` — detecta extensión real desde URL (antes del `?`), descarga, extrae ZIPs.
3. `escanear_directorio()` — obtiene lista de archivos excel+csv.
4. Ordena por FK: entidades → municipios → localidades → resto.
5. Por cada archivo: `cargar_archivo()`.

### `cargar_archivo(ruta, batch_size=5000)`
Pipeline por archivo:
```
procesar_archivo() → normalizar_dataframe() → transformar_para_modelo()
→ df.where(pd.notna(df), None)   ← re-aplica NaN→None después del transformer
→ Session(engine, autoflush=False)
→ batches de 5000: {k: v for k, v in fila.to_dict().items() if pd.notna(v)}
→ session.merge(Modelo(**datos)) × N
→ session.commit() por batch
```

Mejoras clave vs versión anterior:
- `autoflush=False`: evita flush prematuro que causaba errores de FK.
- Commit por batch de 5000: las 296k localidades pasan de 19 min a ~2-3 min.
- `pd.notna(v)` en el filtro: maneja correctamente NaN numérico (no solo `None`).
- Extensión real extraída del URL: `codigo_postal` → `.xls`, `medicamentos` → `.xlsm`.

---

## Configuración y entorno

### `.env` (no versionado)
```
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nest_project        # Base de datos del backend NestJS
```

### Ejecutar
```bash
cd motor_archivos
python scripts/cargar_catalogos.py
```

### `requirements.txt`
```
pandas==2.1.4
openpyxl==3.1.2
xlrd==2.0.1
requests==2.31.0
sqlmodel==0.0.38
psycopg2-binary==2.9.12
pydantic-settings==2.2.1
```

---

## TODOs / Pendientes (post Sprint 1)

| Elemento | Prioridad | Nota |
|---|---|---|
| `iniciar_bd()` | **ELIMINAR** | NestJS gestiona el esquema en producción |
| `CLUES` modelo | Alta | 68 columnas — requiere análisis de `clues_origen.xlsx` |
| `CIF` modelo | Media | Header en fila 3: columnas `Código`/`Descripción` |
| `Religion` archivo corrupto | Media | El servidor devuelve HTML; agregar validación de Content-Type/magic bytes en extractor |
| `CodigoPostal` modelo | Media | Archivo actual `_origen.xlsx` incompleto/corrupto; nuevo download como `.xls` se hará en próxima ejecución |
| `Medicamento.clave` como PK | Baja | Cambiar de `id` int autoincrement a `clave: str`; coordinar con NestJS |
| LOINC transformer | Baja | Agregar `transformar_loinc` en sanitizer cuando se cargue el CSV |
| Validación post-descarga | Media | Verificar magic bytes antes de guardar para detectar HTML de error |
| Migración a Alembic | Baja | `iniciar_bd()` seguirá usándose hasta que NestJS tome el control del esquema |

---

## Decisiones clave de diseño

### Por qué `pd.notna(v)` en lugar de `v is not None`
Pandas convierte listas con `None` a columnas `float64` donde `None` → `NaN`. Al hacer `fila.to_dict()`, los valores NaN aparecen como `float('nan')` (que `is not None`). El filtro `pd.notna` atrapa correctamente ambos casos.

### Por qué `pd.Int64Dtype()` para columnas de edad
Los transformers crean columnas de edad como listas Python con `None` y `int`. Pandas infiere `float64` para estas mezclas. Usar `pd.array(..., dtype=pd.Int64Dtype())` preserva los enteros y permite `None` sin conversión a `NaN`, manteniendo el tipo correcto hasta llegar a Pydantic/SQLAlchemy.

### Por qué `SEX_TYPE` de procedimientos usa parser distinto
El catálogo CIE-10 (diagnósticos) codifica el sexo como texto (`NO`/`HOMBRE`/`MUJER`), mientras el catálogo CIE-9-MC (procedimientos) usa código numérico DGIS (`0`=AMBOS, `1`=HOMBRE, `2`=MUJER). Usar el mismo parser produciría que todos los procedimientos queden como AMBOS.

### Por qué `PRO_CVE_EDIA` necesita mapeo numérico
Las unidades de edad en procedimientos son código numérico DGIS (`1`=A años, `2`=M meses, `3`=D días, `4`=H horas), no la letra directamente. El mapeo `_CVE_UNIDAD_EDAD` convierte estos antes de almacenarlos como `UnidadEdad` enum.

---

## Flujo de datos completo

```
URLs oficiales SSA/GOBSI/CSG
        │
        ▼
descargar_archivo() ──→ descargas/*_origen.{xlsx|xls|xlsm|zip}
        │
        ▼ (si .zip)
extraer_zip() ──────→ descargas/*_extraido/*.xlsx
        │
        ▼
escanear_directorio("descargas") → [excel + csv files]
        │
        ▼ [sort: entidades → municipios → localidades → resto]
        │
        ▼  (por cada archivo)
procesar_archivo(dtype=str) ──→ pd.DataFrame crudo
        │
        ▼
normalizar_dataframe() ──→ columnas limpias, llaves normalizadas, NaN→None
        │
        ▼
transformar_para_modelo() ──→ columnas exactas del modelo (enums, Int64, bools)
        │
        ▼
df.where(pd.notna(df), None) ──→ NaN residuales → None
        │
        ▼  (batches de 5000, autoflush=False)
{k: v for k, v in fila.to_dict().items() if pd.notna(v)}
        │
        ▼
session.merge(Modelo(**datos))  ← upsert por PK
session.commit() por batch
        │
        ▼
PostgreSQL (DB de NestJS: nest_project)
```
