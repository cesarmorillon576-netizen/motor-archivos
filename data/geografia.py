from sqlmodel import SQLModel, Field  

class EntidadFederativa(SQLModel, table=True):
    __tablename__ = "cat_entidades_federativas"
    
    catalog_key: str = Field(primary_key=True)
    entidad_federativa: str
    abreviatura: str

class Municipio(SQLModel, table = True):
    __tablename__ = "cat_municipios"
    catalog_key: str = Field(primary_key=True)
    municipio: str
    abreviatura: str
    efe_key: str = Field(foreign_key="cat_entidades_federativas.catalog_key")

class Localidad(SQLModel, table = True):
    __tablename__ = "cat_localidades"
    catalog_key: str = Field(primary_key=True)
    localidad: str
    municipio_key: str = Field(foreign_key="cat_municipios.catalog_key")

class CodigoPostal(SQLModel, table = True):
    __tablename__ = "codigos_postales"

    catalog_key: str = Field(primary_key=True)
    codigo_postal: str

# TODO: Solucionar tabla
# class CLUES(SQLModel, table = True):
#    __tablename__ = "clues"

    
    