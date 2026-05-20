from .db import engine, iniciar_bd, obtener_sesion

# Modelos Demograficos
from .demografia import LenguaIndigena, Religion, Formacion, Nacionalidad 

# Modelos Geograficos
from .geografia import EntidadFederativa, Municipio, Localidad, CodigoPostal

# Modelos de insumos
from .insumos import Medicamento

# Modelos clinicos
from .clinico import Procedimiento, LOINC, Diagnostico