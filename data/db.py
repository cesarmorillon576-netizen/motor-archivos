from sqlmodel import create_engine, Session, SQLModel
from .config import settings

DB_URL = (
    f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

engine = create_engine(DB_URL, echo=False)


# TODO: Eliminar cuando NestJS gestione migraciones en producción.
def iniciar_bd():
    print("Verificando base de datos")
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
