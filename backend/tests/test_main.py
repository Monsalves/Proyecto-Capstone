import pytest
from fastapi.testclient import TestClient
from backend.app.main import app, Base, engine, SessionLocal, ConfiguracionDB
import os

client = TestClient(app)

def test_get_estado():
    # Reset configuration to default to ensure test isolation
    db = SessionLocal()
    cfg = db.query(ConfiguracionDB).filter(ConfiguracionDB.id == 1).first()
    if cfg:
        cfg.nombre_empresa = "Buses JAC"
        cfg.capacidad_bus = 45
        db.commit()
    db.close()

    response = client.get("/api/sistema/estado")
    assert response.status_code == 200
    data = response.json()
    assert "capacidad_bus" in data
    assert "nombre_empresa" in data
    assert data["nombre_empresa"] == "Buses JAC"

def test_put_configuracion():
    response = client.put("/api/sistema/configuracion", json={
        "capacidad_bus": 50,
        "nombre_empresa": "JAC Express"
    })
    assert response.status_code == 200
    
    response = client.get("/api/sistema/estado")
    data = response.json()
    assert data["capacidad_bus"] == 50
    assert data["nombre_empresa"] == "JAC Express"

def test_cargar_csv_invalido():
    response = client.post("/api/sistema/cargar-csv", files={
        "archivo": ("test.csv", "TIPO_BOLETO,PRECIO\n1,100")
    })
    assert response.status_code == 400