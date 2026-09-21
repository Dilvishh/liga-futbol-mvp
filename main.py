from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from database import engine, Base, get_db, SessionLocal
import models

Base.metadata.create_all(bind=engine)

def sembrar_datos_completos():
    db = SessionLocal()
    try:
        if db.query(models.Torneo).count() == 0:
            print("🌱 Sembrando estructura de Torneo, Series y Partidos...")

            torneo = models.Torneo(nombre="Copa de Campeones 2026", temporada="2026")
            db.add(torneo)
            db.commit()
            db.refresh(torneo)

            serie_a = models.Categoria(nombre="Serie A (Honor)", torneo_id=torneo.id)
            serie_b = models.Categoria(nombre="Serie B (Ascenso)", torneo_id=torneo.id)
            db.add_all([serie_a, serie_b])
            db.commit()
            db.refresh(serie_a)
            db.refresh(serie_b)

            tarde = models.Equipo(nombre="La Tarde FC", categoria_id=serie_a.id, escudo_url="https://cdn-icons-png.flaticon.com/512/1165/1165187.png")
            lineas = models.Equipo(nombre="Líneas Muertas", categoria_id=serie_a.id, escudo_url="https://cdn-icons-png.flaticon.com/512/1165/1165249.png")
            cerro = models.Equipo(nombre="Cerro City", categoria_id=serie_a.id, escudo_url="https://cdn-icons-png.flaticon.com/512/1165/1165203.png")
            nueva_era = models.Equipo(nombre="Nueva Era", categoria_id=serie_a.id, escudo_url="https://cdn-icons-png.flaticon.com/512/1165/1165241.png")

            barrio = models.Equipo(nombre="Barrio Rojo", categoria_id=serie_b.id, escudo_url="https://cdn-icons-png.flaticon.com/512/1165/1165195.png")
            jerrys = models.Equipo(nombre="Jerrys FC", categoria_id=serie_b.id, escudo_url="https://cdn-icons-png.flaticon.com/512/1165/1165215.png")

            db.add_all([tarde, lineas, cerro, nueva_era, barrio, jerrys])
            db.commit()

            j1 = models.Jugador(nombre="Alejo Pérez", numero=10, posicion="Delantero", equipo_id=tarde.id, foto_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80")
            j2 = models.Jugador(nombre="Andy Crossa", numero=9, posicion="Delantero", equipo_id=cerro.id, foto_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80")
            j3 = models.Jugador(nombre="Federico Reyes", numero=5, posicion="Defensa", equipo_id=lineas.id, foto_url="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80")
            j4 = models.Jugador(nombre="Matías González", numero=8, posicion="Volante", equipo_id=barrio.id, foto_url="https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=150&auto=format&fit=crop&q=80")
            j5 = models.Jugador(nombre="Sebastián Requira", numero=7, posicion="Mediocampista", equipo_id=tarde.id, foto_url="https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=150&auto=format&fit=crop&q=80")
            db.add_all([j1, j2, j3, j4, j5])
            db.commit()

            p1 = models.Partido(
                categoria_id=serie_a.id, jornada="Fecha 1", cancha="Cancha 1", fecha_hora="Sáb 15:00",
                local_id=tarde.id, visita_id=lineas.id, goles_local=3, goles_visita=0, estado="FINALIZADO"
            )
            p2 = models.Partido(
                categoria_id=serie_a.id, jornada="Fecha 1", cancha="Cancha 2", fecha_hora="Sáb 16:30",
                local_id=cerro.id, visita_id=nueva_era.id, goles_local=4, goles_visita=1, estado="FINALIZADO"
            )
            p3 = models.Partido(
                categoria_id=serie_a.id, jornada="Fecha 2", cancha="Cancha 1", fecha_hora="Próx. Sábado",
                local_id=tarde.id, visita_id=cerro.id, goles_local=0, goles_visita=0, estado="PROGRAMADO"
            )
            p4 = models.Partido(
                categoria_id=serie_b.id, jornada="Fecha 1", cancha="Cancha 3", fecha_hora="Dom 10:00",
                local_id=barrio.id, visita_id=jerrys.id, goles_local=2, goles_visita=1, estado="FINALIZADO"
            )

            db.add_all([p1, p2, p3, p4])
            db.commit()

            inc1 = models.Incidencia(partido_id=p1.id, tipo="GOL", minuto=12, detalle="Alejo Pérez", jugador_id=j1.id)
            inc2 = models.Incidencia(partido_id=p1.id, tipo="GOL", minuto=25, detalle="Alejo Pérez", jugador_id=j1.id)
            inc3 = models.Incidencia(partido_id=p1.id, tipo="AMARILLA", minuto=32, detalle="Federico Reyes", jugador_id=j3.id)
            inc4 = models.Incidencia(partido_id=p1.id, tipo="MVP", minuto=50, detalle="Alejo Pérez", jugador_id=j1.id)
            db.add_all([inc1, inc2, inc3, inc4])
            db.commit()
            print("✅ Datos sembrados con éxito.")
    finally:
        db.close()

sembrar_datos_completos()

app = FastAPI(title="Liga de Estrellas Doradas")
templates = Jinja2Templates(directory="templates")

def calcular_tabla_categoria(db: Session, categoria_id: int):
    equipos = db.query(models.Equipo).filter(models.Equipo.categoria_id == categoria_id).all()
    partidos = db.query(models.Partido).filter(
        models.Partido.categoria_id == categoria_id,
        models.Partido.estado == "FINALIZADO"
    ).all()

    tabla = {
        eq.id: {
            "id": eq.id, "equipo": eq.nombre, "escudo": eq.escudo_url,
            "pj": 0, "pg": 0, "pe": 0, "pp": 0, "gf": 0, "gc": 0, "dg": 0, "pts": 0
        } for eq in equipos
    }

    for p in partidos:
        if p.local_id in tabla and p.visita_id in tabla:
            loc, vis = tabla[p.local_id], tabla[p.visita_id]
            loc["pj"] += 1; vis["pj"] += 1
            loc["gf"] += p.goles_local; loc["gc"] += p.goles_visita
            vis["gf"] += p.goles_visita; vis["gc"] += p.goles_local

            if p.goles_local > p.goles_visita:
                loc["pg"] += 1; loc["pts"] += 3; vis["pp"] += 1
            elif p.goles_visita > p.goles_local:
                vis["pg"] += 1; vis["pts"] += 3; loc["pp"] += 1
            else:
                loc["pe"] += 1; loc["pts"] += 1; vis["pe"] += 1; vis["pts"] += 1

    lista = list(tabla.values())
    for f in lista: f["dg"] = f["gf"] - f["gc"]
    lista.sort(key=lambda x: (x["pts"], x["dg"], x["gf"]), reverse=True)
    return lista

# ==========================================
# RUTAS PRINCIPALES
# ==========================================

@app.get("/", response_class=HTMLResponse)
def home_publica(request: Request, cat_id: Optional[int] = None, db: Session = Depends(get_db)):
    torneo = db.query(models.Torneo).filter(models.Torneo.activo == True).first()
    categorias = db.query(models.Categoria).all()

    categoria_activa = None
    if cat_id:
        categoria_activa = db.query(models.Categoria).filter(models.Categoria.id == cat_id).first()
    if not categoria_activa and categorias:
        categoria_activa = categorias[0]

    partidos = []
    tabla = []
    if categoria_activa:
        partidos = db.query(models.Partido).filter(models.Partido.categoria_id == categoria_activa.id).all()
        tabla = calcular_tabla_categoria(db, categoria_activa.id)

    return templates.TemplateResponse(
        request=request, name="index.html",
        context={
            "torneo": torneo,
            "categorias": categorias,
            "categoria_activa": categoria_activa,
            "partidos": partidos,
            "tabla": tabla,
            "pagina_activa": "inicio"
        }
    )

# VISTA: ESTADÍSTICAS Y RANKINGS (Goleadores, Fair Play)
@app.get("/estadisticas", response_class=HTMLResponse)
def vista_estadisticas(request: Request, db: Session = Depends(get_db)):
    # Ranking de Goleadores
    jugadores = db.query(models.Jugador).all()
    ranking_goleadores = []
    for j in jugadores:
        total_goles = db.query(models.Incidencia).filter(
            models.Incidencia.jugador_id == j.id, models.Incidencia.tipo == "GOL"
        ).count()
        if total_goles > 0:
            ranking_goleadores.append({
                "jugador": j,
                "equipo": j.equipo.nombre,
                "escudo": j.equipo.escudo_url,
                "goles": total_goles
            })
    ranking_goleadores.sort(key=lambda x: x["goles"], reverse=True)

    # Ranking MVP
    ranking_mvp = []
    for j in jugadores:
        total_mvp = db.query(models.Incidencia).filter(
            models.Incidencia.jugador_id == j.id, models.Incidencia.tipo == "MVP"
        ).count()
        if total_mvp > 0:
            ranking_mvp.append({
                "jugador": j,
                "equipo": j.equipo.nombre,
                "mvps": total_mvp
            })
    ranking_mvp.sort(key=lambda x: x["mvps"], reverse=True)

    return templates.TemplateResponse(
        request=request, name="estadisticas.html",
        context={
            "goleadores": ranking_goleadores,
            "mvps": ranking_mvp,
            "pagina_activa": "ligas"
        }
    )

@app.get("/equipos", response_class=HTMLResponse)
def vista_equipos(request: Request, db: Session = Depends(get_db)):
    categorias = db.query(models.Categoria).all()
    return templates.TemplateResponse(
        request=request, name="equipos.html",
        context={"categorias": categorias, "pagina_activa": "equipos"}
    )

@app.get("/equipo/{equipo_id}", response_class=HTMLResponse)
def ficha_equipo(request: Request, equipo_id: int, db: Session = Depends(get_db)):
    equipo = db.query(models.Equipo).filter(models.Equipo.id == equipo_id).first()
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    partidos = db.query(models.Partido).filter(
        (models.Partido.local_id == equipo_id) | (models.Partido.visita_id == equipo_id)
    ).all()

    return templates.TemplateResponse(
        request=request, name="equipo_detalle.html",
        context={"equipo": equipo, "partidos": partidos, "pagina_activa": "equipos"}
    )

@app.get("/jugador/{jugador_id}", response_class=HTMLResponse)
def ficha_jugador(request: Request, jugador_id: int, db: Session = Depends(get_db)):
    jugador = db.query(models.Jugador).filter(models.Jugador.id == jugador_id).first()
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    goles = db.query(models.Incidencia).filter(models.Incidencia.jugador_id == jugador_id, models.Incidencia.tipo == "GOL").count()
    amarillas = db.query(models.Incidencia).filter(models.Incidencia.jugador_id == jugador_id, models.Incidencia.tipo == "AMARILLA").count()
    rojas = db.query(models.Incidencia).filter(models.Incidencia.jugador_id == jugador_id, models.Incidencia.tipo == "ROJA").count()
    mvps = db.query(models.Incidencia).filter(models.Incidencia.jugador_id == jugador_id, models.Incidencia.tipo == "MVP").count()
    incidencias = db.query(models.Incidencia).filter(models.Incidencia.jugador_id == jugador_id).all()

    return templates.TemplateResponse(
        request=request, name="jugador_detalle.html",
        context={
            "jugador": jugador, "goles": goles, "amarillas": amarillas,
            "rojas": rojas, "mvps": mvps, "incidencias": incidencias,
            "pagina_activa": "equipos"
        }
    )

@app.get("/partido/{partido_id}", response_class=HTMLResponse)
def centro_partido(request: Request, partido_id: int, db: Session = Depends(get_db)):
    partido = db.query(models.Partido).filter(models.Partido.id == partido_id).first()
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    incidencias = db.query(models.Incidencia).filter(models.Incidencia.partido_id == partido_id).all()
    return templates.TemplateResponse(
        request=request, name="partido_detalle.html",
        context={"partido": partido, "incidencias": incidencias, "pagina_activa": "inicio"}
    )

@app.post("/partido/{partido_id}/incidencia")
def registrar_incidencia(
    partido_id: int, tipo: str = Form(...), equipo_tipo: str = Form(...),
    jugador_nombre: str = Form(...), minuto: int = Form(0), db: Session = Depends(get_db)
):
    partido = db.query(models.Partido).filter(models.Partido.id == partido_id).first()
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    equipo_actual = partido.local if equipo_tipo == "local" else partido.visita
    jugador = db.query(models.Jugador).filter(
        models.Jugador.equipo_id == equipo_actual.id,
        models.Jugador.nombre == jugador_nombre.strip()
    ).first()

    if tipo == "GOL":
        if equipo_tipo == "local": partido.goles_local += 1
        else: partido.goles_visita += 1

    incidencia = models.Incidencia(
        partido_id=partido.id, tipo=tipo, minuto=minuto,
        detalle=f"{jugador_nombre} ({equipo_actual.nombre})",
        jugador_id=jugador.id if jugador else None
    )
    db.add(incidencia)
    db.commit()
    return RedirectResponse(url=f"/partido/{partido_id}", status_code=303)

@app.post("/partido/{partido_id}/incidencia/{incidencia_id}/eliminar")
def eliminar_incidencia(partido_id: int, incidencia_id: int, db: Session = Depends(get_db)):
    inc = db.query(models.Incidencia).filter(models.Incidencia.id == incidencia_id).first()
    partido = db.query(models.Partido).filter(models.Partido.id == partido_id).first()
    if inc and partido:
        if inc.tipo == "GOL":
            if partido.local.nombre in (inc.detalle or "") and partido.goles_local > 0: partido.goles_local -= 1
            elif partido.visita.nombre in (inc.detalle or "") and partido.goles_visita > 0: partido.goles_visita -= 1
        db.delete(inc)
        db.commit()
    return RedirectResponse(url=f"/partido/{partido_id}", status_code=303)

@app.get("/veedor", response_class=HTMLResponse)
def vista_veedor(request: Request, db: Session = Depends(get_db)):
    partidos = db.query(models.Partido).all()
    return templates.TemplateResponse(request=request, name="veedor.html", context={"partidos": partidos, "pagina_activa": "login"})

@app.get("/admin", response_class=HTMLResponse)
def vista_admin(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request=request, name="admin.html",
        context={"equipos": db.query(models.Equipo).all(), "partidos": db.query(models.Partido).all(), "pagina_activa": "login"}
    )
