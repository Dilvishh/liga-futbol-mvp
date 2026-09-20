from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Equipo(Base):
    __tablename__ = "equipos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    escudo_url = Column(String, nullable=True)  # Link al logo/escudo

    # Relación: Un equipo tiene muchos jugadores
    jugadores = relationship("Jugador", back_populates="equipo")

class Jugador(Base):
    __tablename__ = "jugadores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    numero = Column(Integer, nullable=True)
    posicion = Column(String, nullable=True)  # Ej: "Delantero", "Arquero"
    
    # Conexión con la tabla equipos
    equipo_id = Column(Integer, ForeignKey("equipos.id"))
    equipo = relationship("Equipo", back_populates="jugadores")

class Partido(Base):
    __tablename__ = "partidos"

    id = Column(Integer, primary_key=True, index=True)
    
    # Equipos participantes
    local_id = Column(Integer, ForeignKey("equipos.id"))
    visita_id = Column(Integer, ForeignKey("equipos.id"))
    
    # Marcador y estado
    goles_local = Column(Integer, default=0)
    goles_visita = Column(Integer, default=0)
    minuto_actual = Column(Integer, default=0)
    estado = Column(String, default="PROGRAMADO")  # PROGRAMADO, EN_VIVO, FINALIZADO

    # Relaciones para poder acceder a los nombres fácilmente (partido.local.nombre)
    local = relationship("Equipo", foreign_keys=[local_id])
    visita = relationship("Equipo", foreign_keys=[visita_id])
    incidencias = relationship("Incidencia", back_populates="partido")

class Incidencia(Base):
    __tablename__ = "incidencias"

    id = Column(Integer, primary_key=True, index=True)
    partido_id = Column(Integer, ForeignKey("partidos.id"))
    tipo = Column(String, nullable=False)  # "GOL", "AMARILLA", "ROJA", "CAMBIO", "MVP"
    minuto = Column(Integer, nullable=False)
    detalle = Column(String, nullable=True) # Ej: "Gol de Alejo Pérez (asistencia de Requira)"

    partido = relationship("Partido", back_populates="incidencias")