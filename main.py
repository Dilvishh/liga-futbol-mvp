from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from database import engine, Base, get_db, SessionLocal
import models

# 1. Crear tablas si no existen
Base.metadata.create_all(bind=engine)

# 2. Función de Sembrado Automático de Datos de Ejemplo
def sembrar_datos_iniciales():
    db = SessionLocal()
    try:
        # Solo inserta si la tabla de equipos está totalmente vacía
        if db.query(models.Equipo).count() == 0:
            print("🌱 Sembrando datos iniciales de la liga...")

            # Crear Equipos
            tarde_fc = models.Equipo(nombre="La Tarde FC")
            lineas = models.Equipo(nombre="Líneas Muertas")
            cerro = models.Equipo(nombre="Cerro City")
            nueva_era = models.Equipo(nombre="Nueva Era")

            db.add_all([tarde_fc, lineas, cerro, nueva_era])
            db.commit()

            # Crear Jugadores de ejemplo
            j1 = models.Jugador(nombre="Alejo Pérez", equipo_id=tarde_fc.id, numero=10, posicion="Delantero")
            j2 = models.Jugador(nombre="Sebastián Requira", equipo_id=tarde_fc.id, numero=7, posicion="Mediocampista")
            j3 = models.Jugador(nombre="Andy Crossa", equipo_id=cerro.id, numero=9, posicion="Delantero")
            j4 = models.Jugador(nombre="Federico Reyes", equipo_id=lineas.id, numero=5, posicion="Defensa")

            db.add_all([j1, j2, j3, j4])
            db.commit()

            # Crear Partidos de ejemplo con resultados
            p1 = models.Partido(
                local_id=tarde_fc.id,
                visita_id=lineas.id,
                goles_local=3,
                goles_visita=0,
                estado="FINALIZADO",
                minuto_actual=50
            )
            p2 = models.Partido(
                local_id=cerro.id,
                visita_id=nueva_era.id,
                goles_local=4,
                goles_visita=1,
                estado="FINALIZADO",
                minuto_actual=50
            )
            p3 = models.Partido(
                local_id=tarde_fc.id,
                visita_id=cerro.id,
                goles_local=0,
                goles_visita=0,
                estado="PROGRAMADO",
                minuto_actual=0
            )

            db.add_all([p1, p2, p3])
            db.commit()

            # Crear Incidencias del primer partido
            inc1 = models.Incidencia(partido_id=p1.id, tipo="GOL", minuto=12, detalle="Alejo Pérez (La Tarde FC)")
            inc2 = models.Incidencia(partido_id=p1.id, tipo="GOL", minuto=24, detalle="Alejo Pérez (La Tarde FC)")
            inc3 = models.Incidencia(partido_id=p1.id, tipo="GOL", minuto=38, detalle="Sebastián Requira (La Tarde FC)")
            inc4 = models.Incidencia(partido_id=p1.id, tipo="AMARILLA", minuto=41, detalle="Federico Reyes (Líneas Muertas)")
            inc5 = models.Incidencia(partido_id=p1.id, tipo="MVP", minuto=50, detalle="Alejo Pérez (La Tarde FC)")

            db.add_all([inc1, inc2, inc3, inc4, inc5])
            db.commit()
            print("✅ Datos iniciales cargados con éxito.")
    finally:
        db.close()

# Ejecutar el sembrado al iniciar la aplicación
sembrar_datos_iniciales()

app = FastAPI(title="Liga de Estrellas Doradas")
templates = Jinja2Templates(directory="templates")


# ==========================================
# CÁLCULO DE TABLA DE POSICIONES
# ==========================================
def calcular_tabla_posiciones(db: Session):
    equipos = db.query(models.Equipo).all()
    partidos_finalizados = db.query(models.Partido).filter(models.Partido.estado == "FINALIZADO").all()

    tabla = {
        eq.id: {
            "id": eq.id, "equipo": eq.nombre,
            "pj": 0, "pg": 0, "pe": 0, "pp": 0,
            "gf": 0, "gc": 0, "dg": 0, "pts": 0
        } for eq in equipos
    }

    for p in partidos_finalizados:
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
# VISTAS DE NAVEGACIÓN
# ==========================================
@app.get("/", response_class=HTMLResponse)
def vista_principal(request: Request, db: Session = Depends(get_db)):
    partidos = db.query(models.Partido).all()
    tabla = calcular_tabla_posiciones(db)
    return templates.TemplateResponse(
        request=request, name="index.html",
        context={"tabla": tabla, "partidos": partidos, "equipos": db.query(models.Equipo).all()}
    )

@app.get("/veedor", response_class=HTMLResponse)
def vista_veedor(request: Request, db: Session = Depends(get_db)):
    partidos = db.query(models.Partido).all()
    return templates.TemplateResponse(
        request=request, name="veedor.html",
        context={"partidos": partidos}
    )

@app.get("/partido/{partido_id}", response_class=HTMLResponse)
def centro_partido(request: Request, partido_id: int, db: Session = Depends(get_db)):
    partido = db.query(models.Partido).filter(models.Partido.id == partido_id).first()
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    
    incidencias = db.query(models.Incidencia).filter(models.Incidencia.partido_id == partido_id).all()
    return templates.TemplateResponse(
        request=request, name="partido_detalle.html",
        context={"partido": partido, "incidencias": incidencias}
    )

@app.post("/partido/{partido_id}/incidencia")
def registrar_incidencia(
    partido_id: int,
    tipo: str = Form(...),
    equipo_tipo: str = Form(...),
    jugador_nombre: str = Form(...),
    minuto: int = Form(0),
    db: Session = Depends(get_db)
):
    partido = db.query(models.Partido).filter(models.Partido.id == partido_id).first()
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    if tipo == "GOL":
        if equipo_tipo == "local":
            partido.goles_local += 1
        else:
            partido.goles_visita += 1

    equipo_nombre = partido.local.nombre if equipo_tipo == "local" else partido.visita.nombre
    incidencia = models.Incidencia(
        partido_id=partido.id,
        tipo=tipo,
        minuto=minuto,
        detalle=f"{jugador_nombre} ({equipo_nombre})"
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
            if partido.local.nombre in (inc.detalle or "") and partido.goles_local > 0:
                partido.goles_local -= 1
            elif partido.visita.nombre in (inc.detalle or "") and partido.goles_visita > 0:
                partido.goles_visita -= 1
        db.delete(inc)
        db.commit()
    return RedirectResponse(url=f"/partido/{partido_id}", status_code=303)

@app.get("/admin", response_class=HTMLResponse)
def vista_admin(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request=request, name="admin.html",
        context={"equipos": db.query(models.Equipo).all(), "partidos": db.query(models.Partido).all()}
    )

@app.post("/admin/equipos/crear")
def form_crear_equipo(nombre: str = Form(...), db: Session = Depends(get_db)):
    if nombre.strip():
        db.add(models.Equipo(nombre=nombre.strip()))
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/jugadores/crear")
def form_crear_jugador(nombre: str = Form(...), equipo_id: int = Form(...), numero: Optional[int] = Form(None), posicion: str = Form("Delantero"), db: Session = Depends(get_db)):
    db.add(models.Jugador(nombre=nombre.strip(), equipo_id=equipo_id, numero=numero, posicion=posicion))
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/partidos/crear")
def form_crear_partido(local_id: int = Form(...), visita_id: int = Form(...), db: Session = Depends(get_db)):
    if local_id != visita_id:
        db.add(models.Partido(local_id=local_id, visita_id=visita_id, estado="PROGRAMADO"))
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/partidos/{partido_id}/finalizar")
def form_finalizar_partido(partido_id: int, goles_local: int = Form(...), goles_visita: int = Form(...), db: Session = Depends(get_db)):
    p = db.query(models.Partido).filter(models.Partido.id == partido_id).first()
    if p:
        p.goles_local = goles_local; p.goles_visita = goles_visita; p.estado = "FINALIZADO"
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)
