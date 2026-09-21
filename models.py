from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Torneo(Base):
    __tablename__ = "torneos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)  # Ej: Copa Clausura 2026
    temporada = Column(String, default="2026")
    activo = Column(Boolean, default=True)

    categorias = relationship("Categoria", back_populates="torneo")


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)  # Ej: Primera División, Grupo A, Senior +30
    torneo_id = Column(Integer, ForeignKey("torneos.id"))

    torneo = relationship("Torneo", back_populates="categorias")
    equipos = relationship("Equipo", back_populates="categoria")
    partidos = relationship("Partido", back_populates="categoria")


class Equipo(Base):
    __tablename__ = "equipos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    escudo_url = Column(String, default="https://cdn-icons-png.flaticon.com/512/1165/1165187.png")
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=True)

    categoria = relationship("Categoria", back_populates="equipos")
    jugadores = relationship("Jugador", back_populates="equipo")


class Jugador(Base):
    __tablename__ = "jugadores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    numero = Column(Integer, nullable=True)
    posicion = Column(String, default="Delantero") # Arquero, Defensa, Volante, Delantero
    foto_url = Column(String, default="https://cdn-icons-png.flaticon.com/512/847/847969.png")
    equipo_id = Column(Integer, ForeignKey("equipos.id"))

    equipo = relationship("Equipo", back_populates="jugadores")
    incidencias = relationship("Incidencia", back_populates="jugador")


class Partido(Base):
    __tablename__ = "partidos"

    id = Column(Integer, primary_key=True, index=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    jornada = Column(String, default="Fecha 1")  # Ej: Fecha 1, Semifinal
    cancha = Column(String, default="Cancha 1")
    fecha_hora = Column(String, default="Sábado 16:00")
    
    local_id = Column(Integer, ForeignKey("equipos.id"))
    visita_id = Column(Integer, ForeignKey("equipos.id"))
    
    goles_local = Column(Integer, default=0)
    goles_visita = Column(Integer, default=0)
    estado = Column(String, default="PROGRAMADO")  # PROGRAMADO, EN_VIVO, FINALIZADO
    minuto_actual = Column(Integer, default=0)

    categoria = relationship("Categoria", back_populates="partidos")
    local = relationship("Equipo", foreign_keys=[local_id])
    visita = relationship("Equipo", foreign_keys=[visita_id])
    incidencias = relationship("Incidencia", back_populates="partido", cascade="all, delete-orphan")


class Incidencia(Base):
    __tablename__ = "incidencias"

    id = Column(Integer, primary_key=True, index=True)
    partido_id = Column(Integer, ForeignKey("partidos.id"))
    tipo = Column(String)  # GOL, AMARILLA, ROJA, MVP
    minuto = Column(Integer, default=0)
    detalle = Column(String, nullable=True)
    jugador_id = Column(Integer, ForeignKey("jugadores.id"), nullable=True)

    partido = relationship("Partido", back_populates="incidencias")
    jugador = relationship("Jugador", back_populates="incidencias")
