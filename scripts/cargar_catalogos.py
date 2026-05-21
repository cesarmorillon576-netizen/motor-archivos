import os
from sqlmodel import Session
from data import engine, obtener_sesion, URLS_CATALOGOS, iniciar_bd
from helpers import (
    log, descargar_archivo, extraer_zip, escanear_directorio,
    obtener_modelo, procesar_archivo, normalizar_dataframe
)

def descargar_catalogos():
    log.info(f"Iniciando descarga dde catálogos oficiales...")

    for clave, url in URLS_CATALOGOS.items():
        if "loinc" in clave:
            log.info("Saltando descarga automática de LOINC")
            continue

        extension = ".zip" if ".zip" in url.lower() else ".xlsx"
        ruta_descarga = f"descargas/{clave}_origen{extension}"       

        exito = descargar_archivo(url, ruta_descarga )

        if exito and extension == ".zip":
            carpeta_destino = f"descargas/{clave}_extraido"
            extraer_zip(ruta_descarga, carpeta_destino)   


def orquestador(carpeta_origen: str = "descargas"):
    iniciar_bd()
    descargar_catalogos()
    log.info(f"Iniciando proceso en: {carpeta_origen}")

    arbol_archivos = escanear_directorio(carpeta_origen)
    archivos_a_procesar = arbol_archivos["excel"] + arbol_archivos["csv"]

    if not archivos_a_procesar:
        log.warning("No se encontraron archivos para procesar en disco.")
        return

    prioridad = {
        'entidad_federativa_origen.xlsx': 1,
        'municipio_origen.xlsx': 2,
        'localidades_origen.xlsx': 3
    }
    archivos_a_procesar = sorted(archivos_a_procesar, key=lambda x: prioridad.get(os.path.basename(x), 99))

    for ruta_archivo in archivos_a_procesar:
        nombre_corto = os.path.basename(ruta_archivo)
        log.info(f"Procesando: {nombre_corto}")

        ModeloSql = obtener_modelo(ruta_archivo)
        if not ModeloSql:
            log.warning(f"Saltando archivo: {nombre_corto} (no mapeado)")
            continue

        df_sucio = procesar_archivo(ruta_archivo)
        if df_sucio is None or df_sucio.empty:
            continue
        df_limpio = normalizar_dataframe(df_sucio)

        registros_exitosos = 0
        try:
            with Session(engine) as session:
                for _, fila in df_limpio.iterrows():
                    nuevo_registro = ModeloSql(**fila.to_dict())
                    session.merge(nuevo_registro)
                    registros_exitosos += 1
                session.commit()
            log.info(f"Sincronizados {registros_exitosos} filas en tabla '{ModeloSql.__tablename__}'")
        except Exception as e:
            log.error(f"Error al sincronizar tabla '{nombre_corto}': {str(e)}")   

        log.info("==================================================")
        log.info(f"Catalogos actualizados.")

if __name__ == "__main__":
     orquestador()