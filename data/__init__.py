from .db import engine, iniciar_bd, get_session
from .constants import URLS_CATALOGOS

# Modelos y enums clínicos
from .clinico import (
    Diagnostico,
    Procedimiento,
    Loinc,
    RestriccionSexo,
    UnidadEdad,
    LoincScale,
    LoincStatus,
)

# Modelos demográficos
from .demografia import LenguaIndigena, Religion, Formacion, Nacionalidad

# Modelos geográficos
from .geografia import EntidadFederativa, Municipio, Localidad, CodigoPostal

# Modelos de insumos
from .insumos import Medicamento
