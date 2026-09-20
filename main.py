from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from database import engine, Base, get_db
import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Liga de Estrellas Doradas")
templates = Jinja2Templates(directory="templates")

# ==========================================
# CÁLCULO DE TABLA
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

# Vista 1: Lista de Partidos del Veedor (estilo video)
@app.get("/veedor", response_class=HTMLResponse)
def vista_veedor(request: Request, db: Session = Depends(get_db)):
    partidos = db.query(models.Partido).all()
    return templates.TemplateResponse(
        request=request, name="veedor.html",
        context={"partidos": partidos}
    )

# Vista 2: Centro de Partido individual
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

# Acción: Registrar Incidencia (Gol, Tarjeta, MVP)
@app.post("/partido/{partido_id}/incidencia")
def registrar_incidencia(
    partido_id: int,
    tipo: str = Form(...),
    equipo_tipo: str = Form(...), # "local" o "visita"
    jugador_nombre: str = Form(...),
    minuto: int = Form(0),
    db: Session = Depends(get_db)
):
    partido = db.query(models.Partido).filter(models.Partido.id == partido_id).first()
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    # Actualizar marcador si es gol
    if tipo == "GOL":
        if equipo_tipo == "local":
            partido.goles_local += 1
        else:
            partido.goles_visita += 1

    incidencia = models.Incidencia(
        partido_id=partido.id,
        tipo=tipo,
        minuto=minuto,
        detalle=f"{jugador_nombre} ({partido.local.nombre if equipo_tipo == 'local' else partido.visita.nombre})"
    )
    db.add(incidencia)
    db.commit()

    return RedirectResponse(url=f"/partido/{partido_id}", status_code=303)

# Acción: Eliminar incidencia
@app.post("/partido/{partido_id}/incidencia/{incidencia_id}/eliminar")
def eliminar_incidencia(partido_id: int, incidencia_id: int, db: Session = Depends(get_db)):
    inc = db.query(models.Incidencia).filter(models.Incidencia.id == incidencia_id).first()
    partido = db.query(models.Partido).filter(models.Partido.id == partido_id).first()
    if inc and partido:
        if inc.tipo == "GOL":
            # Si se borra un gol, se descuenta
            if partido.local.nombre in (inc.detalle or "") and partido.goles_local > 0:
                partido.goles_local -= 1
            elif partido.visita.nombre in (inc.detalle or "") and partido.goles_visita > 0:
                partido.goles_visita -= 1
        db.delete(inc)
        db.commit()
    return RedirectResponse(url=f"/partido/{partido_id}", status_code=303)

# Mantener rutas de admin para crear equipos y partidos
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