import os
import io
import math
import joblib
from fastapi import FastAPI, HTTPException, status, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DATA_DIR = os.getenv("DATA_DIR", ".")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(DATA_DIR, 'db.sqlite3')}")
MODEL_PATH = os.path.join(DATA_DIR, "model.joblib")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
TIER_COLORS = ["#0ea5e9", "#f97316", "#8b5cf6", "#22c55e", "#ec4899", "#f59e0b", "#14b8a6", "#6366f1"]

class ConfiguracionDB(Base):
    __tablename__ = "configuracion_sistema"
    id = Column(Integer, primary_key=True)
    capacidad_bus = Column(Integer, default=45, nullable=False)
    nombre_empresa = Column(String(100), default="Buses JAC", nullable=False)
    fecha_ultimo_entrenamiento = Column(String(50), nullable=True)
    registros_procesados = Column(Integer, default=0)
    registros_descartados = Column(Integer, default=0)
    mae_modelo = Column(Float, nullable=True)
    rmse_modelo = Column(Float, nullable=True)
    r2_modelo = Column(Float, nullable=True)
    fecha_min_dataset = Column(String(50), nullable=True)
    fecha_max_dataset = Column(String(50), nullable=True)
    rutas_disponibles = Column(Integer, default=0)

class RegistroHistoricoDB(Base):
    __tablename__ = "registros_historicos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nro_boleto = Column(Integer, nullable=False)
    linea = Column(Integer, nullable=True)
    origen = Column(String(20), nullable=False)
    destino = Column(String(20), nullable=False)
    ruta = Column(String(50), nullable=False)
    fecha_salida = Column(String(20), nullable=False)
    hora_salida = Column(String(10), nullable=False)
    hora_salida_minutos = Column(Integer, nullable=True)
    dia_semana = Column(Integer, nullable=True)
    es_fin_de_semana = Column(Boolean, nullable=True)
    mes = Column(Integer, nullable=True)
    tipo_asiento = Column(String(50), nullable=True)
    canal_venta = Column(String(50), nullable=True)
    subcanal_venta = Column(String(50), nullable=True)
    valor = Column(Integer, nullable=False)
    fecha_compra = Column(String(20), nullable=False)
    dias_anticipacion = Column(Integer, nullable=True)
    fecha_carga = Column(String(50), nullable=False)

class SalidaAgregadaDB(Base):
    __tablename__ = "salidas_agregadas"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ruta = Column(String(50), nullable=False)
    fecha_salida = Column(String(20), nullable=False)
    hora_salida = Column(String(10), nullable=False)
    hora_salida_minutos = Column(Integer, nullable=True)
    dia_semana = Column(Integer, nullable=True)
    es_fin_de_semana = Column(Boolean, nullable=True)
    mes = Column(Integer, nullable=True)
    asientos_vendidos = Column(Integer, nullable=True)
    tarifa_promedio = Column(Float, nullable=True)
    ingreso_total = Column(Float, nullable=True)
    fecha_carga = Column(String(50), nullable=False)

Base.metadata.create_all(bind=engine)

# Seed config
db = SessionLocal()
if not db.query(ConfiguracionDB).filter(ConfiguracionDB.id == 1).first():
    db.add(ConfiguracionDB(id=1, capacidad_bus=45, nombre_empresa="Buses JAC"))
    db.commit()
db.close()

# ── Shared: Train ML model from SalidaAgregadaDB ──────────────────────────
def train_and_save_model(db_session, fecha_carga, discarded=0):
    """Train RandomForest on SalidaAgregadaDB, persist model.joblib, update ConfiguracionDB."""
    agg_rows = db_session.query(SalidaAgregadaDB).all()
    if not agg_rows:
        return {"status": "no_data"}

    model_df = pd.DataFrame([{
        "ruta": r.ruta,
        "dia_semana": r.dia_semana,
        "es_fin_de_semana": int(r.es_fin_de_semana),
        "mes": r.mes,
        "hora_salida_minutos": int(r.hora_salida_minutos or 0),
        "tarifa_promedio": float(r.tarifa_promedio or 0.0),
        "asientos_vendidos": r.asientos_vendidos
    } for r in agg_rows])

    unique_routes = sorted(list(model_df["ruta"].unique()))
    route_to_idx = {r: i for i, r in enumerate(unique_routes)}
    model_df["ruta_encoded"] = model_df["ruta"].map(route_to_idx)

    X = model_df[["ruta_encoded", "dia_semana", "es_fin_de_semana", "mes", "hora_salida_minutos", "tarifa_promedio"]]
    y = model_df["asientos_vendidos"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=30, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(mean_squared_error(y_test, y_pred) ** 0.5)
    r2 = float(r2_score(y_test, y_pred))

    payload = {
        "model": model,
        "route_to_idx": route_to_idx,
        "unique_routes": unique_routes
    }
    joblib.dump(payload, MODEL_PATH)

    all_tickets = db_session.query(RegistroHistoricoDB).all()
    config = db_session.query(ConfiguracionDB).filter(ConfiguracionDB.id == 1).first()
    config.fecha_ultimo_entrenamiento = fecha_carga
    config.registros_procesados = len(all_tickets)
    config.registros_descartados = discarded
    config.mae_modelo = mae
    config.rmse_modelo = rmse
    config.r2_modelo = r2
    config.fecha_min_dataset = min(t.fecha_salida for t in all_tickets) if all_tickets else None
    config.fecha_max_dataset = max(t.fecha_salida for t in all_tickets) if all_tickets else None
    config.rutas_disponibles = len(unique_routes)
    db_session.commit()

    return {"mae": mae, "rmse": rmse, "r2": r2}

# ── Demo-data seeder: tmco-pcon only, 30 days, realistic distributions ────
def seed_demo_data_if_empty():
    """Generate 30 days of realistic tmco-pcon demo data if DB is empty."""
    from datetime import timedelta

    db_seed = SessionLocal()
    try:
        existing = db_seed.query(RegistroHistoricoDB).count()
        config = db_seed.query(ConfiguracionDB).filter(ConfiguracionDB.id == 1).first()
        if existing > 0 or (config and config.fecha_ultimo_entrenamiento is not None):
            db_seed.close()
            return  # already has data — idempotent

        RUTA = "tmco-pcon"
        ORIGEN = "tmco"
        DESTINO = "pcon"
        HOURS = ["06:30", "07:00", "09:30", "13:00", "17:30", "19:00"]
        HOUR_MINUTES = [390, 420, 570, 780, 1050, 1140]
        DAYS = 30
        CAPACITY = 45
        AVG_PAX = 8.1
        AVG_PRICE = 4500
        PRICE_STD = 500
        PRICE_MIN = 2500
        PRICE_MAX = 7000

        fecha_carga = datetime.now().isoformat()
        end_date = datetime.now().date() - timedelta(days=1)
        start_date = end_date - timedelta(days=DAYS - 1)

        np.random.seed(42)
        boleto_counter = 100000

        current_date = start_date
        while current_date <= end_date:
            dt_salida = datetime.combine(current_date, datetime.min.time())
            dia_sem = current_date.weekday()
            is_wk = dia_sem >= 5
            mes = current_date.month

            for hour_str, hour_min in zip(HOURS, HOUR_MINUTES):
                # Time-of-day pricing: morning/evening peaks cost more
                base_price = AVG_PRICE + (hour_min - 570) * 0.25 + np.random.normal(0, 200)
                base_price = max(PRICE_MIN, min(PRICE_MAX, round(base_price / 100) * 100))

                # Price elasticity: cheaper → more passengers, expensive → fewer
                price_deviation = (base_price - AVG_PRICE) / 100
                elasticity_effect = -price_deviation * 0.4
                n_tickets = int(np.random.poisson(AVG_PAX) + elasticity_effect)
                n_tickets = max(1, min(CAPACITY, n_tickets))

                for _ in range(n_tickets):
                    valor = int(round(np.random.normal(base_price, 300) / 100) * 100)
                    valor = max(PRICE_MIN, min(PRICE_MAX, valor))

                    dias_ant = int(np.random.exponential(7))
                    dias_ant = min(dias_ant, 30)
                    dt_compra = dt_salida - timedelta(days=dias_ant)
                    if dt_compra.date() > datetime.now().date():
                        dt_compra = datetime.now() - timedelta(days=dias_ant)

                    tipo_asiento = np.random.choice(
                        ["Clas.Cort.", "Semi Cama", "Salon Cama"],
                        p=[0.75, 0.20, 0.05]
                    )
                    canal_venta = np.random.choice(
                        ["Presencial", "Online", "Telefonico"],
                        p=[0.50, 0.40, 0.10]
                    )

                    ticket = RegistroHistoricoDB(
                        nro_boleto=boleto_counter,
                        linea=None,
                        origen=ORIGEN,
                        destino=DESTINO,
                        ruta=RUTA,
                        fecha_salida=dt_salida.strftime("%Y-%m-%d"),
                        hora_salida=hour_str,
                        hora_salida_minutos=hour_min,
                        dia_semana=dia_sem,
                        es_fin_de_semana=is_wk,
                        mes=mes,
                        tipo_asiento=tipo_asiento,
                        canal_venta=canal_venta,
                        subcanal_venta="",
                        valor=valor,
                        fecha_compra=dt_compra.strftime("%Y-%m-%d"),
                        dias_anticipacion=dias_ant,
                        fecha_carga=fecha_carga
                    )
                    db_seed.add(ticket)
                    boleto_counter += 1

            current_date += timedelta(days=1)

        db_seed.commit()

        # Build SalidaAgregadaDB
        tickets_db = db_seed.query(RegistroHistoricoDB).filter(
            RegistroHistoricoDB.ruta == RUTA
        ).all()

        agg_df = pd.DataFrame([{
            "ruta": t.ruta,
            "fecha_salida": t.fecha_salida,
            "hora_salida": t.hora_salida,
            "dia_semana": t.dia_semana,
            "es_fin_de_semana": t.es_fin_de_semana,
            "mes": t.mes,
            "hora_salida_minutos": t.hora_salida_minutos,
            "valor": t.valor
        } for t in tickets_db])

        groups = agg_df.groupby(["ruta", "fecha_salida", "hora_salida"]).agg(
            asientos_vendidos=("valor", "count"),
            tarifa_promedio=("valor", "mean"),
            ingreso_total=("valor", "sum")
        ).reset_index()

        for _, row in groups.iterrows():
            dt_s = datetime.strptime(row["fecha_salida"], "%Y-%m-%d")
            h_parts = row["hora_salida"].split(":")
            h_min = int(h_parts[0]) * 60 + int(h_parts[1]) if len(h_parts) == 2 else 0
            agg = SalidaAgregadaDB(
                ruta=row["ruta"],
                fecha_salida=row["fecha_salida"],
                hora_salida=row["hora_salida"],
                hora_salida_minutos=h_min,
                dia_semana=dt_s.weekday(),
                es_fin_de_semana=dt_s.weekday() >= 5,
                mes=dt_s.month,
                asientos_vendidos=int(row["asientos_vendidos"]),
                tarifa_promedio=float(row["tarifa_promedio"]),
                ingreso_total=float(row["ingreso_total"]),
                fecha_carga=fecha_carga
            )
            db_seed.add(agg)
        db_seed.commit()

        # Train model
        train_and_save_model(db_seed, fecha_carga, discarded=0)

    except Exception as e:
        db_seed.rollback()
        import traceback
        print(f"[seed_demo_data] Error: {e}")
        traceback.print_exc()
    finally:
        db_seed.close()

app = FastAPI(title="JAC Revenue Sandbox API", version="1.0.0")

# Seed demo data at import time so it works with uvicorn, TestClient, and pytest
seed_demo_data_if_empty()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
def read_root():
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "index.html")
    if os.path.exists(frontend_path):
        with open(frontend_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Frontend index.html not found on disk."

class ConfigUpdate(BaseModel):
    capacidad_bus: int = Field(..., ge=1, le=100)
    nombre_empresa: str = Field(..., min_length=1, max_length=100)

class ProyectarRequest(BaseModel):
    ruta: str
    fecha: str
    hora: str
    tarifa: float
    cupos_proteccion: int

class TramoRequest(BaseModel):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    targetSeats: int = Field(..., ge=0)
    price: float = Field(..., gt=0)
    color: Optional[str] = None

class ProyectarV2Request(BaseModel):
    ruta: str
    fecha: str
    hora: str
    tarifa_base: float = Field(..., gt=0)
    capacidad_bus: int = Field(..., ge=1, le=100)
    tramos: List[TramoRequest] = Field(default_factory=list)
    seatPlan: List[Optional[str]] = Field(default_factory=list)

class RecomendacionTramosRequest(BaseModel):
    ruta: str
    fecha: str
    hora: str
    capacidad_bus: int = Field(..., ge=1, le=100)
    tarifa_base: Optional[float] = Field(default=None, gt=0)

def _predict_occupancy(model, route_to_idx, ruta, fecha, hora, capacidad, tarifa_base_modelo, tarifa_efectiva):
    dt = datetime.strptime(fecha, "%Y-%m-%d")
    dia_sem = dt.weekday()
    is_wk = int(dia_sem >= 5)
    mes = dt.month

    parts = hora.split(":")
    h_min = int(parts[0]) * 60 + int(parts[1]) if len(parts) > 1 else 0

    route_enc = route_to_idx[ruta]
    features_base = [[route_enc, dia_sem, is_wk, mes, h_min, float(tarifa_base_modelo)]]
    pred_base = model.predict(features_base)[0]
    ocup_base_val = max(0.0, min(float(capacidad), float(pred_base)))

    elasticidad = -1.2
    ratio_precio = float(tarifa_efectiva) / float(tarifa_base_modelo) if tarifa_base_modelo > 0 else 1.0
    ocup_final = ocup_base_val * (ratio_precio ** elasticidad)
    return max(0.0, min(float(capacidad), float(ocup_final)))

def _build_booking_curves(db, ruta, capacidad, ocupacion_actual):
    hist_tickets = db.query(RegistroHistoricoDB).filter(RegistroHistoricoDB.ruta == ruta).all()
    dates = set(t.fecha_salida for t in hist_tickets)
    curve_by_date = {d: {day: 0 for day in range(-30, 1)} for d in dates}
    for t in hist_tickets:
        if t.fecha_salida in curve_by_date and t.dias_anticipacion is not None and 0 <= t.dias_anticipacion <= 30:
            start_day = -t.dias_anticipacion
            for day in range(start_day, 1):
                curve_by_date[t.fecha_salida][day] += 1

    hist_curve = []
    for day in range(-30, 1):
        vals = [curve_by_date[d][day] for d in dates] if dates else [0]
        avg_val = np.mean(vals) if vals else 0.0
        hist_curve.append({"dias_anticipacion": day, "asientos_acumulados": round(float(avg_val), 1)})

    proj_curve = []
    final_hist_val = hist_curve[-1]["asientos_acumulados"] if hist_curve else 0.0
    for hc in hist_curve:
        scale = (ocupacion_actual / final_hist_val) if final_hist_val > 0 else 0.0
        proj_val = hc["asientos_acumulados"] * scale
        proj_curve.append({
            "dias_anticipacion": hc["dias_anticipacion"],
            "asientos_acumulados": round(max(0.0, min(float(capacidad), proj_val)), 1)
        })

    return hist_curve, proj_curve

def _build_legacy_projection_response(db, model, route_to_idx, ruta, fecha, hora, capacidad, tarifa_actual, cupos_actual):
    base_esc = get_escenario_base(ruta, fecha, hora)
    t_base = base_esc["tarifa_base"]
    c_base = base_esc["cupos_proteccion_sugeridos"]

    def calc_revenue(ocupacion_val, tarifa_val, cupos_val):
        cupos_efectivos = min(ocupacion_val, float(cupos_val))
        ing_prot = cupos_efectivos * tarifa_val
        ing_ant = max(0.0, ocupacion_val - cupos_efectivos) * (tarifa_val * 0.85)
        return ing_prot + ing_ant

    ocup_actual = _predict_occupancy(
        model, route_to_idx, ruta, fecha, hora, capacidad, t_base, tarifa_actual
    )
    ing_actual = calc_revenue(ocup_actual, tarifa_actual, cupos_actual)

    ocup_base = _predict_occupancy(
        model, route_to_idx, ruta, fecha, hora, capacidad, t_base, t_base
    )
    ing_base = calc_revenue(ocup_base, t_base, c_base)

    var_ing = ((ing_actual - ing_base) / ing_base * 100.0) if ing_base > 0 else 0.0
    var_ocup = (ocup_actual / capacidad * 100.0) - (ocup_base / capacidad * 100.0)

    hist_curve, proj_curve = _build_booking_curves(db, ruta, capacidad, ocup_actual)

    ocup_t_up = _predict_occupancy(
        model, route_to_idx, ruta, fecha, hora, capacidad, t_base, tarifa_actual * 1.10
    )
    ing_t_up = calc_revenue(ocup_t_up, tarifa_actual * 1.10, cupos_actual)
    impact_t_up = ing_t_up - ing_actual

    ocup_t_down = _predict_occupancy(
        model, route_to_idx, ruta, fecha, hora, capacidad, t_base, tarifa_actual * 0.90
    )
    ing_t_down = calc_revenue(ocup_t_down, tarifa_actual * 0.90, cupos_actual)
    impact_t_down = ing_t_down - ing_actual

    delta_c = max(1, int(capacidad * 0.10))
    c_up = min(capacidad, cupos_actual + delta_c)
    ocup_c_up = _predict_occupancy(
        model, route_to_idx, ruta, fecha, hora, capacidad, t_base, tarifa_actual
    )
    ing_c_up = calc_revenue(ocup_c_up, tarifa_actual, c_up)
    impact_c_up = ing_c_up - ing_actual

    c_down = max(0, cupos_actual - delta_c)
    ocup_c_down = _predict_occupancy(
        model, route_to_idx, ruta, fecha, hora, capacidad, t_base, tarifa_actual
    )
    ing_c_down = calc_revenue(ocup_c_down, tarifa_actual, c_down)
    impact_c_down = ing_c_down - ing_actual

    tornado = [
        {
            "variable": "Tarifa",
            "impacto_subida_10": round(impact_t_up),
            "impacto_bajada_10": round(impact_t_down)
        },
        {
            "variable": "Cupos de protección",
            "impacto_subida_10": round(impact_c_up),
            "impacto_bajada_10": round(impact_c_down)
        }
    ]

    ajustes_precio = [-5, 0, 5, 10]
    valores_cupos = [5, 10, 15, 20]
    sensibilidad_cruzada = []

    for adj in ajustes_precio:
        p_val = tarifa_actual * (1 + adj / 100)
        ocup_val = _predict_occupancy(
            model, route_to_idx, ruta, fecha, hora, capacidad, t_base, p_val
        )
        puntos = []
        for c in valores_cupos:
            ing = calc_revenue(ocup_val, p_val, c)
            puntos.append({
                "cupos": c,
                "ingreso": round(ing)
            })
        sensibilidad_cruzada.append({
            "etiqueta": f"{adj:+}% precio" if adj != 0 else "0% precio",
            "puntos": puntos
        })

    return {
        "escenario_base": {
            "ingreso_proyectado": round(ing_base),
            "ocupacion_proyectada": round(ocup_base, 1),
            "ocupacion_porcentaje": round(ocup_base / capacidad * 100.0, 1) if capacidad > 0 else 0.0,
            "tarifa": round(t_base),
            "cupos_proteccion": c_base
        },
        "escenario_actual": {
            "ingreso_proyectado": round(ing_actual),
            "ocupacion_proyectada": round(ocup_actual, 1),
            "ocupacion_porcentaje": round(ocup_actual / capacidad * 100.0, 1) if capacidad > 0 else 0.0,
            "tarifa": round(tarifa_actual),
            "cupos_proteccion": cupos_actual,
            "variacion_ingreso_porcentaje": round(var_ing, 1),
            "variacion_ocupacion_puntos": round(var_ocup, 1)
        },
        "booking_curve": {
            "historica": hist_curve,
            "proyectada": proj_curve
        },
        "tornado": tornado,
        "sensibilidad_cruzada": sensibilidad_cruzada
    }

def _build_bus_metrics(req: ProyectarV2Request):
    if len(req.seatPlan) != req.capacidad_bus:
        raise HTTPException(
            status_code=400,
            detail=f"seatPlan debe tener exactamente {req.capacidad_bus} posiciones."
        )

    tramo_by_id = {}
    for tramo in req.tramos:
        if tramo.id in tramo_by_id:
            raise HTTPException(status_code=400, detail=f"Tramo duplicado: '{tramo.id}'.")
        tramo_by_id[tramo.id] = tramo

    unknown_ids = sorted({seat_id for seat_id in req.seatPlan if seat_id is not None and seat_id not in tramo_by_id})
    if unknown_ids:
        raise HTTPException(
            status_code=400,
            detail=f"seatPlan contiene tramos inexistentes: {', '.join(unknown_ids)}"
        )

    counts_by_id = {tramo.id: 0 for tramo in req.tramos}
    for seat_id in req.seatPlan:
        if seat_id is not None:
            counts_by_id[seat_id] += 1

    base_seats = sum(1 for seat_id in req.seatPlan if seat_id is None)
    priced_seats = req.capacidad_bus - base_seats
    tier_metrics = []
    weighted_revenue = base_seats * float(req.tarifa_base)

    for tramo in req.tramos:
        assigned = counts_by_id[tramo.id]
        subtotal = assigned * float(tramo.price)
        weighted_revenue += subtotal
        tier_metrics.append({
            "id": tramo.id,
            "nombre": tramo.name,
            "color": tramo.color,
            "precio": round(float(tramo.price)),
            "target_seats": tramo.targetSeats,
            "asientos_asignados": assigned,
            "ingreso_potencial": round(subtotal),
            "desviacion_vs_target": assigned - tramo.targetSeats
        })

    tarifa_ponderada = weighted_revenue / req.capacidad_bus if req.capacidad_bus > 0 else 0.0
    average_tier_price = (
        sum(item["ingreso_potencial"] for item in tier_metrics) / priced_seats
        if priced_seats > 0 else float(req.tarifa_base)
    )

    return {
        "tramo_by_id": tramo_by_id,
        "base_seats": base_seats,
        "priced_seats": priced_seats,
        "tier_metrics": tier_metrics,
        "weighted_revenue": weighted_revenue,
        "tarifa_ponderada": tarifa_ponderada,
        "average_tier_price": average_tier_price
    }

def _round_price(value):
    return max(100, int(round(float(value) / 100.0) * 100))

def _build_sequential_seat_plan(capacidad, tramos):
    seat_plan = []
    for tramo in tramos:
        seat_plan.extend([tramo.id] * int(tramo.targetSeats))
    if len(seat_plan) < capacidad:
        seat_plan.extend([None] * (capacidad - len(seat_plan)))
    return seat_plan[:capacidad]

def _allowed_block_sequence(capacidad):
    if capacidad <= 0:
        return []
    remaining = capacidad
    blocks = []
    first_block = min(10, remaining)
    blocks.append(first_block)
    remaining -= first_block
    while remaining > 0:
        block = min(5, remaining)
        blocks.append(block)
        remaining -= block
    return blocks

def _select_recommended_blocks(capacidad, tier_count):
    allowed_blocks = _allowed_block_sequence(capacidad)
    if not allowed_blocks:
        return []
    bounded_count = max(1, min(int(tier_count), len(allowed_blocks)))
    if len(allowed_blocks) == 1 or bounded_count == 1:
        return [sum(allowed_blocks)]
    if bounded_count == len(allowed_blocks):
        return allowed_blocks

    # Keep the first commercial cutoff fixed at 10 seats when capacity allows it.
    result = [allowed_blocks[0]]
    tail_blocks = allowed_blocks[1:]
    remaining_tiers = bounded_count - 1
    running_total = 0
    for idx in range(remaining_tiers):
        slots_left = remaining_tiers - idx
        remaining_blocks = len(tail_blocks) - running_total
        take_count = max(1, round(remaining_blocks / slots_left))
        end_index = running_total + take_count
        result.append(sum(tail_blocks[running_total:end_index]))
        running_total = end_index

    if running_total < len(tail_blocks):
        result[-1] += sum(tail_blocks[running_total:])
    return result

def _candidate_profiles_for_demand(base_occ_ratio):
    if base_occ_ratio < 0.35:
        return [
            {
                "label": "Estimular demanda",
                "rationale": "La salida muestra demanda débil; conviene simplificar la escalera y abrir descuentos tempranos para acelerar compra.",
                "tier_count": 2,
                "price_profiles": [
                    [0.82, 1.00],
                    [0.85, 1.05],
                ],
            },
            {
                "label": "Estimular demanda con escalera extendida",
                "rationale": "La salida muestra demanda débil; un tramo adicional permite capturar rebote sin cerrar demasiado rápido el precio.",
                "tier_count": 3,
                "price_profiles": [
                    [0.82, 0.94, 1.08],
                    [0.85, 0.97, 1.12],
                ],
            },
        ]
    if base_occ_ratio < 0.70:
        return [
            {
                "label": "Balancear volumen y yield",
                "rationale": "La salida tiene demanda media; tres tramos suelen capturar volumen temprano sin perder demasiado margen al cierre.",
                "tier_count": 3,
                "price_profiles": [
                    [0.90, 1.00, 1.12],
                    [0.92, 1.03, 1.15],
                    [0.95, 1.05, 1.18],
                ],
            },
            {
                "label": "Balancear volumen con cierre corto",
                "rationale": "La salida tiene demanda media; una escalera más corta puede evitar sobresegmentar inventario cuando el pick-up es estable.",
                "tier_count": 2,
                "price_profiles": [
                    [0.92, 1.08],
                    [0.95, 1.12],
                ],
            },
            {
                "label": "Balancear volumen con microtramos",
                "rationale": "La salida tiene demanda media; un cuarto tramo permite afinar el cierre si el precio soporta más escalones.",
                "tier_count": 4,
                "price_profiles": [
                    [0.90, 0.98, 1.06, 1.16],
                    [0.92, 1.00, 1.08, 1.18],
                ],
            },
        ]
    return [
        {
            "label": "Proteger yield",
            "rationale": "La salida tiene demanda fuerte; conviene usar más escalones y reservar el tramo más caro para el cierre.",
            "tier_count": 4,
            "price_profiles": [
                [0.98, 1.06, 1.15, 1.26],
                [1.00, 1.08, 1.18, 1.30],
                [1.02, 1.10, 1.20, 1.34],
            ],
        },
        {
            "label": "Proteger yield con escalera media",
            "rationale": "La salida tiene demanda fuerte; tres tramos bastan si no conviene fragmentar demasiado el inventario premium.",
            "tier_count": 3,
            "price_profiles": [
                [0.95, 1.08, 1.20],
                [0.98, 1.10, 1.24],
            ],
        },
    ]

def _build_recommendation_request(ruta, fecha, hora, capacidad, tarifa_base_modelo, model, route_to_idx):
    ocup_base = _predict_occupancy(
        model, route_to_idx, ruta, fecha, hora, capacidad, tarifa_base_modelo, tarifa_base_modelo
    )
    demand_ratio = (ocup_base / capacidad) if capacidad > 0 else 0.0
    candidate_profiles = _candidate_profiles_for_demand(demand_ratio)
    tier_names = ["Apertura", "Impulso", "Consolidacion", "Cierre"]
    best_option = None

    for profile in candidate_profiles:
        seat_blocks = _select_recommended_blocks(capacidad, profile["tier_count"])
        for multipliers in profile["price_profiles"]:
            tramos = []
            for idx, (block_size, multiplier) in enumerate(zip(seat_blocks, multipliers), start=1):
                tramos.append(TramoRequest(
                    id=f"tier-{idx}",
                    name=tier_names[idx - 1],
                    targetSeats=block_size,
                    price=_round_price(tarifa_base_modelo * multiplier),
                    color=TIER_COLORS[(idx - 1) % len(TIER_COLORS)],
                ))

            seat_plan = _build_sequential_seat_plan(capacidad, tramos)
            recommendation_req = ProyectarV2Request(
                ruta=ruta,
                fecha=fecha,
                hora=hora,
                tarifa_base=tarifa_base_modelo,
                capacidad_bus=capacidad,
                tramos=tramos,
                seatPlan=seat_plan,
            )
            metrics = _build_bus_metrics(recommendation_req)
            ocupacion = _predict_occupancy(
                model, route_to_idx, ruta, fecha, hora, capacidad, tarifa_base_modelo, metrics["tarifa_ponderada"]
            )
            ingreso = metrics["weighted_revenue"] * (ocupacion / capacidad if capacidad > 0 else 0.0)
            option = {
                "request": recommendation_req,
                "weighted_fare": metrics["tarifa_ponderada"],
                "ocupacion": ocupacion,
                "ingreso": ingreso,
                "tramos": tramos,
                "seat_plan": seat_plan,
                "profile": profile,
            }
            if best_option is None or option["ingreso"] > best_option["ingreso"]:
                best_option = option

    return best_option["request"], {
        "estrategia": best_option["profile"]["label"],
        "razon": best_option["profile"]["rationale"],
        "demanda_base_estimada": round(ocup_base, 1),
        "ocupacion_esperada": round(best_option["ocupacion"], 1),
        "ingreso_esperado": round(best_option["ingreso"]),
        "tarifa_promedio_sugerida": round(best_option["weighted_fare"]),
        "tarifa_referencia": round(tarifa_base_modelo),
        "cantidad_tramos_sugeridos": len(best_option["tramos"]),
        "tramos_sugeridos": [tramo.model_dump() for tramo in best_option["tramos"]],
        "seat_plan_sugerido": best_option["seat_plan"],
    }

def _build_v2_projection_response(db, model, route_to_idx, req: ProyectarV2Request, capacidad):
    metrics = _build_bus_metrics(req)
    base_esc = get_escenario_base(req.ruta, req.fecha, req.hora)
    tarifa_base_modelo = base_esc["tarifa_base"]

    ocup_actual = _predict_occupancy(
        model, route_to_idx, req.ruta, req.fecha, req.hora, capacidad, tarifa_base_modelo, metrics["tarifa_ponderada"]
    )
    ocup_base = _predict_occupancy(
        model, route_to_idx, req.ruta, req.fecha, req.hora, capacidad, tarifa_base_modelo, tarifa_base_modelo
    )

    factor_ocupacion = (ocup_actual / capacidad) if capacidad > 0 else 0.0
    ingreso_actual = metrics["weighted_revenue"] * factor_ocupacion
    ingreso_base = ocup_base * tarifa_base_modelo

    var_ing = ((ingreso_actual - ingreso_base) / ingreso_base * 100.0) if ingreso_base > 0 else 0.0
    var_ocup = (ocup_actual / capacidad * 100.0) - (ocup_base / capacidad * 100.0)

    hist_curve, proj_curve = _build_booking_curves(db, req.ruta, capacidad, ocup_actual)

    ocup_t_up = _predict_occupancy(
        model, route_to_idx, req.ruta, req.fecha, req.hora, capacidad, tarifa_base_modelo, metrics["tarifa_ponderada"] * 1.10
    )
    ingreso_t_up = metrics["weighted_revenue"] * 1.10 * (ocup_t_up / capacidad if capacidad > 0 else 0.0)
    impact_t_up = ingreso_t_up - ingreso_actual

    ocup_t_down = _predict_occupancy(
        model, route_to_idx, req.ruta, req.fecha, req.hora, capacidad, tarifa_base_modelo, metrics["tarifa_ponderada"] * 0.90
    )
    ingreso_t_down = metrics["weighted_revenue"] * 0.90 * (ocup_t_down / capacidad if capacidad > 0 else 0.0)
    impact_t_down = ingreso_t_down - ingreso_actual

    delta_base = max(1, int(capacidad * 0.10))

    def potential_revenue_for_base_seats(base_seats):
        bounded_base = max(0, min(capacidad, int(base_seats)))
        priced_seats = capacidad - bounded_base
        return (bounded_base * float(req.tarifa_base)) + (priced_seats * float(metrics["average_tier_price"]))

    ingreso_base_up = potential_revenue_for_base_seats(metrics["base_seats"] + delta_base)
    impact_base_up = ingreso_base_up * factor_ocupacion - ingreso_actual

    ingreso_base_down = potential_revenue_for_base_seats(metrics["base_seats"] - delta_base)
    impact_base_down = ingreso_base_down * factor_ocupacion - ingreso_actual

    tornado = [
        {
            "variable": "Tarifa promedio ponderada",
            "impacto_subida_10": round(impact_t_up),
            "impacto_bajada_10": round(impact_t_down)
        },
        {
            "variable": "Asientos base",
            "impacto_subida_10": round(impact_base_up),
            "impacto_bajada_10": round(impact_base_down)
        }
    ]

    ajustes_precio = [-5, 0, 5, 10]
    sensibilidad_cruzada = []
    base_seat_options = sorted(set([
        max(0, metrics["base_seats"] - 5),
        metrics["base_seats"],
        min(capacidad, metrics["base_seats"] + 5),
        min(capacidad, metrics["base_seats"] + 10)
    ]))

    for adj in ajustes_precio:
        tarifa_mix = metrics["tarifa_ponderada"] * (1 + adj / 100)
        ocup_val = _predict_occupancy(
            model, route_to_idx, req.ruta, req.fecha, req.hora, capacidad, tarifa_base_modelo, tarifa_mix
        )
        puntos = []
        for base_seats in base_seat_options:
            ingreso_potencial_mix = potential_revenue_for_base_seats(base_seats)
            price_scale = (tarifa_mix / metrics["tarifa_ponderada"]) if metrics["tarifa_ponderada"] > 0 else 1.0
            ingreso_mix = ingreso_potencial_mix * price_scale * (ocup_val / capacidad if capacidad > 0 else 0.0)
            puntos.append({
                "cupos": base_seats,
                "ingreso": round(ingreso_mix)
            })
        sensibilidad_cruzada.append({
            "etiqueta": f"{adj:+}% precio" if adj != 0 else "0% precio",
            "puntos": puntos
        })

    return {
        "escenario_base": {
            "ingreso_proyectado": round(ingreso_base),
            "ocupacion_proyectada": round(ocup_base, 1),
            "ocupacion_porcentaje": round(ocup_base / capacidad * 100.0, 1) if capacidad > 0 else 0.0,
            "tarifa": round(tarifa_base_modelo),
            "cupos_proteccion": 0
        },
        "escenario_actual": {
            "ingreso_proyectado": round(ingreso_actual),
            "ocupacion_proyectada": round(ocup_actual, 1),
            "ocupacion_porcentaje": round(ocup_actual / capacidad * 100.0, 1) if capacidad > 0 else 0.0,
            "tarifa": round(metrics["tarifa_ponderada"]),
            "cupos_proteccion": 0,
            "variacion_ingreso_porcentaje": round(var_ing, 1),
            "variacion_ocupacion_puntos": round(var_ocup, 1)
        },
        "booking_curve": {
            "historica": hist_curve,
            "proyectada": proj_curve
        },
        "tornado": tornado,
        "sensibilidad_cruzada": sensibilidad_cruzada,
        "composicion_bus": {
            "capacidad_bus": capacidad,
            "asientos_base": metrics["base_seats"],
            "asientos_tarifados": capacidad - metrics["base_seats"],
            "tarifa_base": round(req.tarifa_base),
            "tarifa_promedio_ponderada": round(metrics["tarifa_ponderada"]),
            "ingreso_potencial_total": round(metrics["weighted_revenue"]),
            "tramos": metrics["tier_metrics"]
        }
    }

@app.get("/api/sistema/estado")
def get_estado():
    db = SessionLocal()
    config = db.query(ConfiguracionDB).filter(ConfiguracionDB.id == 1).first()
    res = {
        "modelo_activo": config.fecha_ultimo_entrenamiento is not None,
        "fecha_entrenamiento": config.fecha_ultimo_entrenamiento,
        "registros_procesados": config.registros_procesados or 0,
        "registros_descartados": config.registros_descartados or 0,
        "mae": config.mae_modelo,
        "rmse": config.rmse_modelo,
        "r2": config.r2_modelo,
        "capacidad_bus": config.capacidad_bus,
        "nombre_empresa": config.nombre_empresa,
        "fecha_min_dataset": config.fecha_min_dataset,
        "fecha_max_dataset": config.fecha_max_dataset,
        "rutas_disponibles": config.rutas_disponibles or 0
    }
    db.close()
    return res

@app.put("/api/sistema/configuracion")
def put_configuracion(cfg: ConfigUpdate):
    db = SessionLocal()
    config = db.query(ConfiguracionDB).filter(ConfiguracionDB.id == 1).first()
    config.capacidad_bus = cfg.capacidad_bus
    config.nombre_empresa = cfg.nombre_empresa
    db.commit()
    db.refresh(config)
    db.close()
    return {"status": "updated"}

@app.post("/api/sistema/cargar-csv")
async def cargar_csv(archivo: UploadFile = File(...)):
    db = SessionLocal()
    try:
        contents = await archivo.read()
        df = pd.read_csv(io.BytesIO(contents))
        required_cols = ["NRO_BOLETO", "VALOR", "ORIGEN_DESTINO", "FECHA_SALIDA_SERVICIO", "HORA_SALIDA_SERVICIO", "FECHA_COMPRA"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise HTTPException(status_code=400, detail=f"Faltan columnas obligatorias: {', '.join(missing)}")
        
        # Clear old rows
        db.query(RegistroHistoricoDB).delete()
        db.query(SalidaAgregadaDB).delete()
        
        discarded = 0
        inserted_tickets = []
        fecha_carga = datetime.now().isoformat()
        
        for idx, row in df.iterrows():
            try:
                # Dates
                if pd.isna(row["FECHA_SALIDA_SERVICIO"]) or pd.isna(row["FECHA_COMPRA"]):
                    discarded += 1
                    continue
                
                f_salida_str = str(row["FECHA_SALIDA_SERVICIO"]).split('.')[0].strip()
                f_compra_str = str(row["FECHA_COMPRA"]).split('.')[0].strip()
                
                if len(f_salida_str) != 8 or len(f_compra_str) != 8:
                    discarded += 1
                    continue
                
                dt_salida = datetime.strptime(f_salida_str, "%Y%m%d")
                dt_compra = datetime.strptime(f_compra_str, "%Y%m%d")
                
                # Times
                h_salida_str = str(row.get("HORA_SALIDA_SERVICIO", "0000")).split('.')[0].strip().zfill(4)
                if len(h_salida_str) == 3:
                    h_salida_str = "0" + h_salida_str
                if len(h_salida_str) != 4:
                    h_salida_str = "0000"
                h_salida_fmt = f"{h_salida_str[0:2]}:{h_salida_str[2:4]}"
                
                # Orig/Dest
                orig_dest = str(row["ORIGEN_DESTINO"]).lower().strip()
                parts = orig_dest.split("-")
                orig = parts[0] if len(parts) > 0 else "desconocido"
                dest = parts[1] if len(parts) > 1 else "desconocido"
                
                dias_ant = (dt_salida - dt_compra).days
                dia_sem = dt_salida.weekday()
                is_wk = dia_sem >= 5
                
                h_min = int(h_salida_str[0:2]) * 60 + int(h_salida_str[2:4])
                
                ticket = RegistroHistoricoDB(
                    nro_boleto=int(row["NRO_BOLETO"]),
                    linea=int(row["LINEA"]) if "LINEA" in df.columns and not pd.isna(row["LINEA"]) else None,
                    origen=orig,
                    destino=dest,
                    ruta=orig_dest,
                    fecha_salida=dt_salida.strftime("%Y-%m-%d"),
                    hora_salida=h_salida_fmt,
                    hora_salida_minutos=h_min,
                    dia_semana=dia_sem,
                    es_fin_de_semana=is_wk,
                    mes=dt_salida.month,
                    tipo_asiento=str(row.get("TIPO_ASIENTO", "")),
                    canal_venta=str(row.get("CANAL_VENTA", "")),
                    subcanal_venta=str(row.get("SUBCANAL_VENTA", "")),
                    valor=int(row["VALOR"]),
                    fecha_compra=dt_compra.strftime("%Y-%m-%d"),
                    dias_anticipacion=dias_ant,
                    fecha_carga=fecha_carga
                )
                db.add(ticket)
                inserted_tickets.append(ticket)
            except Exception:
                discarded += 1
                
        db.commit()
        
        # Build aggregated outputs
        tickets_db = db.query(RegistroHistoricoDB).all()
        if not tickets_db:
            raise HTTPException(status_code=400, detail="No se cargó ningún boleto válido del archivo CSV.")
            
        agg_df = pd.DataFrame([{
            "ruta": t.ruta,
            "fecha_salida": t.fecha_salida,
            "hora_salida": t.hora_salida,
            "dia_semana": t.dia_semana,
            "es_fin_de_semana": t.es_fin_de_semana,
            "mes": t.mes,
            "hora_salida_minutos": t.hora_salida_minutos,
            "valor": t.valor
        } for t in tickets_db])
        
        groups = agg_df.groupby(["ruta", "fecha_salida", "hora_salida"]).agg(
            asientos_vendidos=("valor", "count"),
            tarifa_promedio=("valor", "mean"),
            ingreso_total=("valor", "sum")
        ).reset_index()
        
        for idx, row in groups.iterrows():
            dt_s = datetime.strptime(row["fecha_salida"], "%Y-%m-%d")
            h_parts = row["hora_salida"].split(":")
            h_min = int(h_parts[0]) * 60 + int(h_parts[1]) if len(h_parts) == 2 else 0
            agg = SalidaAgregadaDB(
                ruta=row["ruta"],
                fecha_salida=row["fecha_salida"],
                hora_salida=row["hora_salida"],
                hora_salida_minutos=h_min,
                dia_semana=dt_s.weekday(),
                es_fin_de_semana=dt_s.weekday() >= 5,
                mes=dt_s.month,
                asientos_vendidos=int(row["asientos_vendidos"]),
                tarifa_promedio=float(row["tarifa_promedio"]),
                ingreso_total=float(row["ingreso_total"]),
                fecha_carga=fecha_carga
            )
            db.add(agg)
        db.commit()
        
        # Train ML Model (shared function)
        train_and_save_model(db, fecha_carga, discarded)
        
        db.close()
        return {"job_id": "abc123", "estado": "iniciado"}
    except HTTPException as he:
        db.rollback()
        db.close()
        raise he
    except Exception as e:
        db.rollback()
        db.close()
        raise HTTPException(status_code=500, detail=f"Error procesando CSV: {str(e)}")

@app.get("/api/sistema/progreso/{job_id}")
def get_progreso(job_id: str):
    return {
        "job_id": job_id,
        "etapa": "finalizado",
        "porcentaje": 100,
        "mensaje": "Entrenamiento completado exitosamente",
        "completado": True,
        "error": None
    }

@app.get("/api/rutas")
def get_rutas():
    db = SessionLocal()
    routes = db.query(SalidaAgregadaDB.ruta).distinct().all()
    res = []
    for r in routes:
        parts = r.ruta.split("-")
        label = f"{parts[0].upper()} -> {parts[1].upper()}" if len(parts) > 1 else r.ruta.upper()
        res.append({"codigo": r.ruta, "etiqueta": label})
    db.close()
    return res

@app.get("/api/rutas/{ruta}/horas")
def get_horas(ruta: str, fecha: str = Query(...)):
    db = SessionLocal()
    hours = db.query(SalidaAgregadaDB.hora_salida).filter(SalidaAgregadaDB.ruta == ruta).distinct().all()
    if not hours:
        hours = db.query(RegistroHistoricoDB.hora_salida).filter(RegistroHistoricoDB.ruta == ruta).distinct().all()
    res = sorted([h.hora_salida for h in hours])
    db.close()
    return res

@app.get("/api/escenario/base")
def get_escenario_base(ruta: str, fecha: str, hora: str):
    db = SessionLocal()
    agg = db.query(SalidaAgregadaDB).filter(
        SalidaAgregadaDB.ruta == ruta,
        SalidaAgregadaDB.hora_salida == hora
    ).all()
    
    if not agg:
        agg = db.query(SalidaAgregadaDB).filter(SalidaAgregadaDB.ruta == ruta).all()
        
    if not agg:
        db.close()
        return {
            "ruta": ruta,
            "fecha": fecha,
            "hora": hora,
            "tarifa_base": 5000,
            "cupos_proteccion_sugeridos": 8,
            "ocupacion_historica_promedio": 30,
            "ingreso_historico_promedio": 150000
        }
        
    asientos_vals = [r.asientos_vendidos for r in agg]
    tarifas_vals = [r.tarifa_promedio for r in agg]
    ingresos_vals = [r.ingreso_total for r in agg]
    
    tarifa_base = float(np.mean(tarifas_vals))
    ocupacion_prom = float(np.mean(asientos_vals))
    ingreso_prom = float(np.mean(ingresos_vals))
    
    cupos_sug = max(1, min(45, int(ocupacion_prom * 0.15)))
    
    db.close()
    return {
        "ruta": ruta,
        "fecha": fecha,
        "hora": hora,
        "tarifa_base": round(tarifa_base),
        "cupos_proteccion_sugeridos": cupos_sug,
        "precio_referencia": round(tarifa_base),
        "ocupacion_historica_promedio": round(ocupacion_prom, 1),
        "ingreso_historico_promedio": round(ingreso_prom)
    }

@app.post("/api/simulacion/proyectar")
def post_proyectar(req: ProyectarRequest):
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(status_code=400, detail="El modelo no ha sido entrenado. Cargue el CSV en configuración.")
        
    db = SessionLocal()
    config = db.query(ConfiguracionDB).filter(ConfiguracionDB.id == 1).first()
    capacidad = config.capacidad_bus
    
    payload = joblib.load(MODEL_PATH)
    model = payload["model"]
    route_to_idx = payload["route_to_idx"]
    
    if req.ruta not in route_to_idx:
        db.close()
        raise HTTPException(status_code=400, detail=f"Ruta '{req.ruta}' no encontrada en el modelo entrenado.")

    response = _build_legacy_projection_response(
        db, model, route_to_idx, req.ruta, req.fecha, req.hora, capacidad, req.tarifa, req.cupos_proteccion
    )
    db.close()
    return response

@app.post("/api/simulacion/proyectar-v2")
def post_proyectar_v2(req: ProyectarV2Request):
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(status_code=400, detail="El modelo no ha sido entrenado. Cargue el CSV en configuración.")

    db = SessionLocal()
    config = db.query(ConfiguracionDB).filter(ConfiguracionDB.id == 1).first()
    capacidad = config.capacidad_bus

    if req.capacidad_bus != capacidad:
        db.close()
        raise HTTPException(
            status_code=400,
            detail=f"capacidad_bus enviada ({req.capacidad_bus}) no coincide con la configuración actual ({capacidad})."
        )

    payload = joblib.load(MODEL_PATH)
    model = payload["model"]
    route_to_idx = payload["route_to_idx"]

    if req.ruta not in route_to_idx:
        db.close()
        raise HTTPException(status_code=400, detail=f"Ruta '{req.ruta}' no encontrada en el modelo entrenado.")

    response = _build_v2_projection_response(db, model, route_to_idx, req, capacidad)
    db.close()
    return response

@app.post("/api/recomendacion/tramos")
def post_recomendar_tramos(req: RecomendacionTramosRequest):
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(status_code=400, detail="El modelo no ha sido entrenado. Cargue el CSV en configuración.")

    db = SessionLocal()
    config = db.query(ConfiguracionDB).filter(ConfiguracionDB.id == 1).first()
    capacidad = config.capacidad_bus

    if req.capacidad_bus != capacidad:
        db.close()
        raise HTTPException(
            status_code=400,
            detail=f"capacidad_bus enviada ({req.capacidad_bus}) no coincide con la configuración actual ({capacidad})."
        )

    payload = joblib.load(MODEL_PATH)
    model = payload["model"]
    route_to_idx = payload["route_to_idx"]

    if req.ruta not in route_to_idx:
        db.close()
        raise HTTPException(status_code=400, detail=f"Ruta '{req.ruta}' no encontrada en el modelo entrenado.")

    base_esc = get_escenario_base(req.ruta, req.fecha, req.hora)
    tarifa_base_modelo = float(req.tarifa_base or base_esc["tarifa_base"])
    recommendation_req, recommendation_meta = _build_recommendation_request(
        req.ruta,
        req.fecha,
        req.hora,
        capacidad,
        tarifa_base_modelo,
        model,
        route_to_idx,
    )
    response = _build_v2_projection_response(db, model, route_to_idx, recommendation_req, capacidad)
    response["recomendacion"] = recommendation_meta
    db.close()
    return response
