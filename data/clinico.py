from sqlmodel import SQLModel, Field

class Procedimiento(SQLModel, table=True):
    __tablename__ = "procedimientos"
    
    catalog_key: str = Field(primary_key=True)
    pro_nombre: str
    capitulo: str
    pro_seccion: str
    procategoria: str
    sex_type: str
    pro_subcateg: str
    pro_edad_ia: str
    pro_edad_fa: str
    procedimiento_type: str

class LOINC(SQLModel, table=True):
    __tablename__ = "loinc"
    
    loinc_num: str = Field(primary_key=True)
    component: str
    scale_typ: str
    method_typ: str
    Class: str
    class_type: str
    long_common_name: str
    short_name: str
    external_copyright_notice: str
    status: str
    version_first_released: str
    version_last_released: str

class Diagnostico(SQLModel, table=True):
    __tablename__ = "diagnostico"
    
    catalog_key: str = Field(primary_key=True)
    nombre: str
    nivel: str
    clave_capitulo: str
    capitulo: str
    restriccion_sexo: str
    edad_minima: str
    edad_maxima: str
    