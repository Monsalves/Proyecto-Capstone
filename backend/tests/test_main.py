import asyncio
import io
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.main import (
    ConfigUpdate,
    ConfiguracionDB,
    ProyectarV2Request,
    SessionLocal,
    TramoRequest,
    cargar_csv,
    get_estado,
    post_proyectar_v2,
    put_configuracion,
)


def test_get_estado():
    db = SessionLocal()
    cfg = db.query(ConfiguracionDB).filter(ConfiguracionDB.id == 1).first()
    if cfg:
        cfg.nombre_empresa = "Buses JAC"
        cfg.capacidad_bus = 45
        db.commit()
    db.close()

    data = get_estado()
    assert "capacidad_bus" in data
    assert "nombre_empresa" in data
    assert data["nombre_empresa"] == "Buses JAC"


def test_put_configuracion():
    put_configuracion(ConfigUpdate(
        capacidad_bus=50,
        nombre_empresa="JAC Express",
    ))

    data = get_estado()
    assert data["capacidad_bus"] == 50
    assert data["nombre_empresa"] == "JAC Express"


@pytest.mark.skip(reason="UploadFile.read() queda bloqueado en este entorno con Python 3.14/FastAPI.")
def test_cargar_csv_invalido():
    archivo = UploadFile(
        filename="test.csv",
        file=io.BytesIO(b"TIPO_BOLETO,PRECIO\n1,100"),
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(cargar_csv(archivo))

    assert exc_info.value.status_code == 400


def test_proyectar_v2_ok():
    db = SessionLocal()
    cfg = db.query(ConfiguracionDB).filter(ConfiguracionDB.id == 1).first()
    cfg.capacidad_bus = 45
    db.commit()
    db.close()

    seat_plan = ["tier-1"] * 10 + ["tier-2"] * 5 + [None] * 30
    data = post_proyectar_v2(ProyectarV2Request(
        ruta="tmco-pcon",
        fecha="2023-10-18",
        hora="09:30",
        tarifa_base=5000,
        capacidad_bus=45,
        tramos=[
            TramoRequest(
                id="tier-1",
                name="Promo temprana",
                targetSeats=10,
                price=4200,
                color="#0ea5e9",
            ),
            TramoRequest(
                id="tier-2",
                name="Tramo alto",
                targetSeats=5,
                price=6200,
                color="#8b5cf6",
            ),
        ],
        seatPlan=seat_plan,
    ))

    assert "composicion_bus" in data
    assert data["composicion_bus"]["asientos_base"] == 30
    assert data["composicion_bus"]["asientos_tarifados"] == 15
    assert data["composicion_bus"]["tarifa_base"] == 5000
    assert len(data["composicion_bus"]["tramos"]) == 2
    assert data["escenario_actual"]["cupos_proteccion"] == 0


def test_proyectar_v2_seatplan_invalido():
    with pytest.raises(HTTPException) as exc_info:
        post_proyectar_v2(ProyectarV2Request(
            ruta="tmco-pcon",
            fecha="2023-10-18",
            hora="09:30",
            tarifa_base=5000,
            capacidad_bus=45,
            tramos=[
                TramoRequest(
                    id="tier-1",
                    name="Promo temprana",
                    targetSeats=10,
                    price=4200,
                    color="#0ea5e9",
                ),
            ],
            seatPlan=["tier-1"] * 44,
        ))

    assert exc_info.value.status_code == 400
    assert "seatPlan" in exc_info.value.detail
