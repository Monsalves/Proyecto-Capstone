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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
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

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed demo data for tmco-pcon on first launch so the app is ready immediately."""
    seed_demo_data_if_empty()
    yield

app = FastAPI(title="JAC Revenue Sandbox API", version="1.0.0", lifespan=lifespan)

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
        
    base_esc = get_escenario_base(req.ruta, req.fecha, req.hora)
    t_base = base_esc["tarifa_base"]
    c_base = base_esc["cupos_proteccion_sugeridos"]
    
    dt = datetime.strptime(req.fecha, "%Y-%m-%d")
    dia_sem = dt.weekday()
    is_wk = int(dia_sem >= 5)
    mes = dt.month
    
    parts = req.hora.split(":")
    h_min = int(parts[0]) * 60 + int(parts[1]) if len(parts) > 1 else 0
    
    def predict_occupancy(tarifa_val, _unused_cupos=None):
        route_enc = route_to_idx[req.ruta]
        features_base = [[route_enc, dia_sem, is_wk, mes, h_min, float(t_base)]]
        pred_base = model.predict(features_base)[0]
        ocup_base_val = max(0.0, min(float(capacidad), float(pred_base)))
        
        elasticidad = -1.2
        ratio_precio = float(tarifa_val) / float(t_base) if t_base > 0 else 1.0
        ocup_final = ocup_base_val * (ratio_precio ** elasticidad)
        return max(0.0, min(float(capacidad), float(ocup_final)))
        
    def calc_revenue(ocupacion_val, tarifa_val, cupos_val):
        cupos_efectivos = min(ocupacion_val, float(cupos_val))
        ing_prot = cupos_efectivos * tarifa_val
        ing_ant = max(0.0, ocupacion_val - cupos_efectivos) * (tarifa_val * 0.85)
        return ing_prot + ing_ant
        
    ocup_actual = predict_occupancy(req.tarifa, req.cupos_proteccion)
    ing_actual = calc_revenue(ocup_actual, req.tarifa, req.cupos_proteccion)
    
    ocup_base = predict_occupancy(t_base, c_base)
    ing_base = calc_revenue(ocup_base, t_base, c_base)
    
    var_ing = ((ing_actual - ing_base) / ing_base * 100.0) if ing_base > 0 else 0.0
    var_ocup = (ocup_actual / capacidad * 100.0) - (ocup_base / capacidad * 100.0)
    
    # Booking curve logic
    hist_tickets = db.query(RegistroHistoricoDB).filter(RegistroHistoricoDB.ruta == req.ruta).all()
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
    final_hist_val = hist_curve[-1]["asientos_acumulados"]
    for hc in hist_curve:
        scale = (ocup_actual / final_hist_val) if final_hist_val > 0 else 0.0
        proj_val = hc["asientos_acumulados"] * scale
        proj_curve.append({
            "dias_anticipacion": hc["dias_anticipacion"],
            "asientos_acumulados": round(max(0.0, min(float(capacidad), proj_val)), 1)
        })
        
    # Sensitivity (Tornado)
    ocup_t_up = predict_occupancy(req.tarifa * 1.10, req.cupos_proteccion)
    ing_t_up = calc_revenue(ocup_t_up, req.tarifa * 1.10, req.cupos_proteccion)
    impact_t_up = ing_t_up - ing_actual
    
    ocup_t_down = predict_occupancy(req.tarifa * 0.90, req.cupos_proteccion)
    ing_t_down = calc_revenue(ocup_t_down, req.tarifa * 0.90, req.cupos_proteccion)
    impact_t_down = ing_t_down - ing_actual
    
    delta_c = max(1, int(capacidad * 0.10))
    c_up = min(capacidad, req.cupos_proteccion + delta_c)
    ocup_c_up = predict_occupancy(req.tarifa, c_up)
    ing_c_up = calc_revenue(ocup_c_up, req.tarifa, c_up)
    impact_c_up = ing_c_up - ing_actual
    
    c_down = max(0, req.cupos_proteccion - delta_c)
    ocup_c_down = predict_occupancy(req.tarifa, c_down)
    ing_c_down = calc_revenue(ocup_c_down, req.tarifa, c_down)
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
    
    # Sensibilidad Cruzada: Precio vs Cupos
    ajustes_precio = [-5, 0, 5, 10]
    valores_cupos = [5, 10, 15, 20]
    sensibilidad_cruzada = []
    
    for adj in ajustes_precio:
        p_val = req.tarifa * (1 + adj / 100)
        ocup_val = predict_occupancy(p_val)
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
        
    db.close()
    
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
            "tarifa": round(req.tarifa),
            "cupos_proteccion": req.cupos_proteccion,
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