from sqlmodel import SQLModel, Field

class LenguaIndigena(SQLModel, table = True):
    __tablename__ = "lenguas_indigenas"
    
    clave_familia: str = Field(primary_key=True)
    clave_grupo: str
    grupo: str
    clave_lengua: str
    lengua_indigena: str

class Religion(SQLModel, table = True):
    __tablename__ = "religiones"
    
    clave_credo: str = Field(primary_key=True)
    credo: str
    clave_grupo: str
    grupo: str
    clave_denominacion: str
    denominacion: str
    clave_religion: str
    religion: str

class Formacion(SQLModel, table = True):
    __tablename__ = "formaciones"
    
    catalog_key: str = Field(primary_key=True)
    agrupacion: str
    grado: str

class Nacionalidad(SQLModel, table = True):
    __tablename__ = "nacionalidades"
    
    codigo_pais: str = Field(primary_key=True)
    pais: str
    clave_nacionalidad: str

    