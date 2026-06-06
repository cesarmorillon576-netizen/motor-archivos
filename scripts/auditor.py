import argparse
import re
from datetime import date
from pathlib import Path

LOG = Path("logs/ejecucion.log")

LINEA = re.compile(
    r"\[(?P<ts>[\d\- :]+)\] "
       r"\[(?P<nivel>\w+)\] "
       r"\[(?P<origen>[^\]]+)\]: "
       r"(?P<msg>.*)"
)

CATFASE = re.compile(r"\[(?P<catalogo>[^:\]]+):(?P<fase>[^\]]+)\]")

def parse_linea(linea: str) -> dict | None:
    m = LINEA.match(linea)
    if not m:
        return None
        
    d = m.groupdict()
    cf = CATFASE.search(d["msg"])
    d["catalogo"] = cf.group("catalogo") if cf else None
    d["fase"] = cf.group("fase") if cf else None
    return d

def cargar() -> list[dict]:
    if not LOG.exists():
        print(f"No existe {LOG}")
        return []
    filas = []
    for linea in LOG.read_text(encoding = "utf-8").splitlines():
        d = parse_linea(linea)
        if d:
           filas.append(d)
    return filas
   
   
def main():
    p = argparse.ArgumentParser(description="Audita logs/ejecucion.log")
    p.add_argument("--nivel", help="Filtrar por nivel: ERROR, WARNING, INFO")
    p.add_argument("--catalogo", help="Filtrar por catálogo, ej: loinc")
    p.add_argument("--hoy", action="store_true", help="Solo registros de hoy")
    p.add_argument("--resumen", action="store_true", help="Resumen de catálogos con error")
    args = p.parse_args()

    filas = cargar()

    if args.nivel:
        filas = [f for f in filas if f["nivel"] == args.nivel.upper()]
    if args.catalogo:
        filas = [f for f in filas if f["catalogo"] == args.catalogo]
    if args.hoy:
        filas = [f for f in filas if date.fromisoformat(f["ts"].split()[0]) == date.today()]

    if args.resumen:
        fallidos = {f["catalogo"] for f in filas
        if f["nivel"] == "ERROR" and f["catalogo"]}

        print(f"Catálogos fallidos: {fallidos or 'ninguno'}")
        return

    for f in filas:
        cat = f["catalogo"] or "-"
        print(f"{f['ts']} [{f['nivel']}] ({cat}/{f['fase'] or '-'}) {f['msg']}")


if __name__ == "__main__":
    main()