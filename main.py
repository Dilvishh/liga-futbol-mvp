from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from database import engine, Base, get_db
import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Liga de Estrellas Doradas")

templates = Jinja2Templates(directory="templates")


# ==========================================
# FUNCIÓN AUXILIAR: CÁLCULO DE TABLA
# ==========================================
def calcular_tabla_posiciones(db: Session):
    equipos = db.query(models.Equipo).all()
    partidos_finalizados = db.query(models.Partido).filter(models.Partido.estado == "FINALIZADO").all()

    tabla = {
        eq.id: {
            "id": eq.id,
            "equipo": eq.nombre,
            "pj": 0, "pg": 0, "pe": 0, "pp": 0,
            "gf": 0, "gc": 0, "dg": 0, "pts": 0
        }
        for eq in equipos
    }

    for p in partidos_finalizados:
        if p.local_id in tabla and p.visita_id in tabla:
            loc = tabla[p.local_id]
            vis = tabla[p.visita_id]

            loc["pj"] += 1
            vis["pj"] += 1
            loc["gf"] += p.goles_local
            loc["gc"] += p.goles_visita
            vis["gf"] += p.goles_visita
            vis["gc"] += p.goles_local

            if p.goles_local > p.goles_visita:
                loc["pg"] += 1
                loc["pts"] += 3
                vis["pp"] += 1
            elif p.goles_visita > p.goles_local:
                vis["pg"] += 1
                vis["pts"] += 3
                loc["pp"] += 1
            else:
                loc["pe"] += 1
                loc["pts"] += 1
                vis["pe"] += 1
                vis["pts"] += 1

    lista_tabla = list(tabla.values())
    for fila in lista_tabla:
        fila["dg"] = fila["gf"] - fila["gc"]

    lista_tabla.sort(key=lambda x: (x["pts"], x["dg"], x["gf"]), reverse=True)
    return lista_tabla


# ==========================================
# VISTA WEB PRINCIPAL (FRONTEND VISUAL)
# ==========================================
@app.get("/", response_class=HTMLResponse)
def vista_principal(request: Request, db: Session = Depends(get_db)):
    equipos = db.query(models.Equipo).all()
    partidos = db.query(models.Partido).all()
    tabla_datos = calcular_tabla_posiciones(db)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "tabla": tabla_datos,
            "partidos": partidos,
            "equipos": equipos
        }
    )


# ==========================================
# GESTIÓN DE EQUIPOS (API)
# ==========================================
@app.post("/equipos/crear")
def crear_equipo(nombre: str, db: Session = Depends(get_db)):
    equipo_existente = db.query(models.Equipo).filter(models.Equipo.nombre == nombre).first()
    if equipo_existente:
        raise HTTPException(status_code=400, detail="Ya existe un equipo con ese nombre")
    
    nuevo_equipo = models.Equipo(nombre=nombre)
    db.add(nuevo_equipo)
    db.commit()
    db.refresh(nuevo_equipo)
    return {"mensaje": "Equipo creado con éxito", "equipo": {"id": nuevo_equipo.id, "nombre": nuevo_equipo.nombre}}

@app.get("/equipos")
def listar_equipos(db: Session = Depends(get_db)):
    equipos = db.query(models.Equipo).all()
    return [{"id": eq.id, "nombre": eq.nombre, "total_jugadores": len(eq.jugadores)} for eq in equipos]


# ==========================================
# GESTIÓN DE PLANTELES (JUGADORES)
# ==========================================
@app.post("/jugadores/crear")
def inscribir_jugador(
    nombre: str, 
    equipo_id: int, 
    numero: Optional[int] = None, 
    posicion: Optional[str] = "Delantero", 
    db: Session = Depends(get_db)
):
    equipo = db.query(models.Equipo).filter(models.Equipo.id == equipo_id).first()
    if not equipo:
        raise HTTPException(status_code=404, detail="El equipo especificado no existe")

    nuevo_jugador = models.Jugador(
        nombre=nombre,
        equipo_id=equipo_id,
        numero=numero,
        posicion=posicion
    )
    db.add(nuevo_jugador)
    db.commit()
    db.refresh(nuevo_jugador)

    return {
        "mensaje": "Jugador inscrito correctamente",
        "jugador": {
            "id": nuevo_jugador.id,
            "nombre": nuevo_jugador.nombre,
            "numero": nuevo_jugador.numero,
            "posicion": nuevo_jugador.posicion,
            "equipo": equipo.nombre
        }
    }

@app.get("/equipos/{equipo_id}/plantel")
def ver_plantel_equipo(equipo_id: int, db: Session = Depends(get_db)):
    equipo = db.query(models.Equipo).filter(models.Equipo.id == equipo_id).first()
    if not equipo:
        raise HTTPException(status_code=404, detail="El equipo no existe")

    plantel = [
        {
            "id": j.id,
            "nombre": j.nombre,
            "numero": j.numero,
            "posicion": j.posicion
        }
        for j in equipo.jugadores
    ]

    return {
        "equipo": equipo.nombre,
        "total_inscritos": len(plantel),
        "plantel": plantel
    }


# ==========================================
# GESTIÓN DE PARTIDOS
# ==========================================
@app.post("/partidos/crear")
def crear_partido(local_id: int, visita_id: int, db: Session = Depends(get_db)):
    if local_id == visita_id:
        raise HTTPException(status_code=400, detail="Un equipo no puede jugar contra sí mismo")
    
    local = db.query(models.Equipo).filter(models.Equipo.id == local_id).first()
    visita = db.query(models.Equipo).filter(models.Equipo.id == visita_id).first()
    if not local or not visita:
        raise HTTPException(status_code=404, detail="Uno o ambos equipos no existen")

    nuevo_partido = models.Partido(
        local_id=local_id,
        visita_id=visita_id,
        estado="PROGRAMADO"
    )
    db.add(nuevo_partido)
    db.commit()
    db.refresh(nuevo_partido)
    return {
        "mensaje": "Partido programado",
        "partido": {
            "id": nuevo_partido.id,
            "local": local.nombre,
            "visita": visita.nombre,
            "estado": nuevo_partido.estado
        }
    }

@app.get("/partidos")
def listar_partidos(db: Session = Depends(get_db)):
    partidos = db.query(models.Partido).all()
    return [
        {
            "id": p.id,
            "local": p.local.nombre,
            "visita": p.visita.nombre,
            "marcador": f"{p.goles_local} - {p.goles_visita}",
            "estado": p.estado
        }
        for p in partidos
    ]

@app.post("/partidos/{partido_id}/finalizar")
def finalizar_partido(partido_id: int, goles_local: int, goles_visita: int, db: Session = Depends(get_db)):
    partido = db.query(models.Partido).filter(models.Partido.id == partido_id).first()
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    partido.goles_local = goles_local
    partido.goles_visita = goles_visita
    partido.estado = "FINALIZADO"
    db.commit()

    return {
        "mensaje": "Resultado guardado y partido finalizado",
        "resultado": f"{partido.local.nombre} {partido.goles_local} - {partido.goles_visita} {partido.visita.nombre}"
    }


# ==========================================
# TABLA DE POSICIONES (API)
# ==========================================
@app.get("/tabla-posiciones")
def obtener_tabla(db: Session = Depends(get_db)):
    return calcular_tabla_posiciones(db)
from fastapi import Form
from fastapi.responses import RedirectResponse

# Vista del panel de administración
@app.get("/admin", response_class=HTMLResponse)
def vista_admin(request: Request, db: Session = Depends(get_db)):
    equipos = db.query(models.Equipo).all()
    partidos = db.query(models.Partido).all()
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "equipos": equipos,
            "partidos": partidos
        }
    )

# Procesar creación de equipo desde formulario
@app.post("/admin/equipos/crear")
def form_crear_equipo(nombre: str = Form(...), db: Session = Depends(get_db)):
    if nombre.strip():
        nuevo_equipo = models.Equipo(nombre=nombre.strip())
        db.add(nuevo_equipo)
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

# Procesar inscripción de jugador desde formulario
@app.post("/admin/jugadores/crear")
def form_crear_jugador(
    nombre: str = Form(...),
    equipo_id: int = Form(...),
    numero: Optional[int] = Form(None),
    posicion: str = Form("Delantero"),
    db: Session = Depends(get_db)
):
    nuevo_jugador = models.Jugador(
        nombre=nombre.strip(),
        equipo_id=equipo_id,
        numero=numero,
        posicion=posicion
    )
    db.add(nuevo_jugador)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)

# Procesar programación de partido desde formulario
@app.post("/admin/partidos/crear")
def form_crear_partido(
    local_id: int = Form(...),
    visita_id: int = Form(...),
    db: Session = Depends(get_db)
):
    if local_id != visita_id:
        nuevo_partido = models.Partido(
            local_id=local_id,
            visita_id=visita_id,
            estado="PROGRAMADO"
        )
        db.add(nuevo_partido)
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

# Procesar resultado de partido desde formulario
@app.post("/admin/partidos/{partido_id}/finalizar")
def form_finalizar_partido(
    partido_id: int,
    goles_local: int = Form(...),
    goles_visita: int = Form(...),
    db: Session = Depends(get_db)
):
    partido = db.query(models.Partido).filter(models.Partido.id == partido_id).first()
    if partido:
        partido.goles_local = goles_local
        partido.goles_visita = goles_visita
        partido.estado = "FINALIZADO"
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)