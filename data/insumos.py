from typing import Optional
from sqlmodel import SQLModel, Field

class Medicamento(SQLModel, table=True):
    __tablename__ = "cat_medicamentos"
    clave: str = Field(primary_key=True)
    grupo: Optional[str] = Field(default=None)
    insumo: Optional[str] = Field(default=None)
    descripcion: Optional[str] = Field(default=None)
    indicaciones: Optional[str] = Field(default=None)

