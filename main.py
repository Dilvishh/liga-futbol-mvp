from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from database import engine, Base, get_db, SessionLocal
import models

Base.metadata.create_all(bind=engine)

# ==========================================
# SEMBRADO COMPLETO (SEGÚN DIAGRAMA)
# ==========================================
def sembrar_datos_completos():
    db = SessionLocal()
    try:
        if db.query(models.Torneo).count() == 0:
            print("🌱 Sembrando estructura de Torneo, Series y Partidos...")

            # 1. Torneo Principal
            torneo = models.Torneo(nombre="Copa de Campeones 2026", temporada="2026")
            db.add(torneo)
            db.commit()
            db.refresh(torneo)

            # 2. Categorías / Series
            serie_a = models.Categoria(nombre="Serie A (Honor)", torneo_id=torneo.id)
            serie_b = models.Categoria(nombre="Serie B (Ascenso)", torneo_id=torneo.id)
            db.add_all([serie_a, serie_b])
            db.commit()
            db.refresh(serie_a)
            db.refresh(serie_b)

            # 3. Equipos Serie A
            tarde = models.Equipo(nombre="La Tarde FC", categoria_id=serie_a.id, escudo_url="https://cdn-icons-png.flaticon.com/512/1165/1165187.png")
            lineas = models.Equipo(nombre="Líneas Muertas", categoria_id=serie_a.id, escudo_url="https://cdn-icons-png.flaticon.com/512/1165/1165249.png")
            cerro = models.Equipo(nombre="Cerro City", categoria_id=serie_a.id, escudo_url="https://cdn-icons-png.flaticon.com/512/1165/1165203.png")
            nueva_era = models.Equipo(nombre="Nueva Era", categoria_id=serie_a.id, escudo_url="https://cdn-icons-png.flaticon.com/512/1165/1165241.png")

            # Equipos Serie B
            barrio = models.Equipo(nombre="Barrio Rojo", categoria_id=serie_b.id, escudo_url="https://cdn-icons-png.flaticon.com/512/1165/1165195.png")
            jerrys = models.Equipo(nombre="Jerrys FC", categoria_id=serie_b.id, escudo_url="https://cdn-icons-png.flaticon.com/512/1165/1165215.png")

            db.add_all([tarde, lineas, cerro, nueva_era, barrio, jerrys])
            db.commit()

            # 4. Jugadores
            j1 = models.Jugador(nombre="Alejo Pérez", numero=10, posicion="Delantero", equipo_id=tarde.id)
            j2 = models.Jugador(nombre="Andy Crossa", numero=9, posicion="Delantero", equipo_id=cerro.id)
            j3 = models.Jugador(nombre="Federico Reyes", numero=5, posicion="Defensa", equipo_id=lineas.id)
            j4 = models.Jugador(nombre="Matías González", numero=8, posicion="Volante", equipo_id=barrio.id)
            db.add_all([j1, j2, j3, j4])
            db.commit()

            # 5. Partidos Serie A
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

            # Partidos Serie B
            p4 = models.Partido(
                categoria_id=serie_b.id, jornada="Fecha 1", cancha="Cancha 3", fecha_hora="Dom 10:00",
                local_id=barrio.id, visita_id=jerrys.id, goles_local=2, goles_visita=1, estado="FINALIZADO"
            )

            db.add_all([p1, p2, p3, p4])
            db.commit()

            # Incidencias
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

# ==========================================
# CÁLCULO DE TABLA FILTRADO POR CATEGORÍA
# ==========================================
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
# RUTAS PÚBLICAS Y NAVEGACIÓN DIFERIDA
# ==========================================
@app.get("/", response_class=HTMLResponse)
def home_publica(request: Request, cat_id: Optional[int] = None, db: Session = Depends(get_db)):
    torneo = db.query(models.Torneo).filter(models.Torneo.activo == True).first()
    categorias = db.query(models.Categoria).all()

    # Si no se selecciona categoría, usar la primera por defecto
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
            "tabla": tabla
        }
    )

# Vista de Veedor (Mesa)
@app.get("/veedor", response_class=HTMLResponse)
def vista_veedor(request: Request, db: Session = Depends(get_db)):
    partidos = db.query(models.Partido).all()
    return templates.TemplateResponse(request=request, name="veedor.html", context={"partidos": partidos})

# Centro de Partido individual
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
    partido_id: int, tipo: str = Form(...), equipo_tipo: str = Form(...),
    jugador_nombre: str = Form(...), minuto: int = Form(0), db: Session = Depends(get_db)
):
    partido = db.query(models.Partido).filter(models.Partido.id == partido_id).first()
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    if tipo == "GOL":
        if equipo_tipo == "local": partido.goles_local += 1
        else: partido.goles_visita += 1

    eq_nombre = partido.local.nombre if equipo_tipo == "local" else partido.visita.nombre
    incidencia = models.Incidencia(
        partido_id=partido.id, tipo=tipo, minuto=minuto,
        detalle=f"{jugador_nombre} ({eq_nombre})"
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

# Admin
@app.get("/admin", response_class=HTMLResponse)
def vista_admin(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request=request, name="admin.html",
        context={"equipos": db.query(models.Equipo).all(), "partidos": db.query(models.Partido).all()}
    )
