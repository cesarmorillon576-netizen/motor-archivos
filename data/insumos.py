from typing import Optional
from sqlmodel import SQLModel, Field

class Medicamento(SQLModel, table=True):
    __tablename__ = "cat_medicamentos"
    id: int = Field(primary_key=True)
    grupo: str
    clave: str
    insumo: str
    descripcion: str
    indicaciones: str

