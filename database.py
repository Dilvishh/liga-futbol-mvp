from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Nombre del archivo donde se guardarán todos los datos
SQLALCHEMY_DATABASE_URL = "sqlite:///./liga.db"

# connect_args={"check_same_thread": False} es necesario para que SQLite funcione con FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Cada vez que queramos leer o guardar algo, abriremos una 'SessionLocal'
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base para crear nuestros modelos (tablas)
Base = declarative_base()

# Función auxiliar para abrir y cerrar la conexión automáticamente en cada petición
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()