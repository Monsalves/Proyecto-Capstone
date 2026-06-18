# JAC Revenue Sandbox

Simulador comercial para Buses JAC con frontend estático servido por FastAPI y backend de simulación con modelo de ocupación entrenable.

El estado actual del proyecto ya no usa sliders de `tarifa + cupos_proteccion` como interfaz principal. La UI trabaja con:

- `tarifa_base`
- `tramos comerciales`
- `seatPlan` por asiento
- simulación backend `v2`

## Estado actual

### Frontend

Archivo principal:

- `frontend/index.html`

Capacidades actuales:

- selección de `ruta`, `hora`, `temporada` y `tipo de día`
- definición manual de `tarifa base`
- creación de múltiples `tramos`
- asignación automática de asientos por tramo
- visualización horizontal del bus
- resumen de `Escenario Actual`
- simulación manual con botón `Simular escenario`

### Backend

Archivo principal:

- `backend/app/main.py`

Capacidades actuales:

- API FastAPI que sirve también el frontend
- carga de CSV histórico
- persistencia local en `db.sqlite3`
- modelo entrenado guardado en `model.joblib`
- endpoint legado `POST /api/simulacion/proyectar`
- endpoint nuevo `POST /api/simulacion/proyectar-v2`

## Arquitectura

### Persistencia

- `RegistroHistoricoDB`: boletos históricos a nivel ticket
- `SalidaAgregadaDB`: salidas agregadas por ruta/fecha/hora
- `ConfiguracionDB`: configuración general y métricas del modelo

Base por defecto:

- `sqlite:///./db.sqlite3`

### Modelo de ML

Se usa:

- `RandomForestRegressor` de `scikit-learn`

Target:

- `asientos_vendidos`

Features:

- `ruta_encoded`
- `dia_semana`
- `es_fin_de_semana`
- `mes`
- `hora_salida_minutos`
- `tarifa_promedio`

Entrenamiento:

- si la base está vacía, el sistema genera un dataset demo sintético y entrena automáticamente al arrancar
- si se carga un CSV desde la UI o API, se reconstruyen las tablas agregadas y se reentrena el modelo

### Simulación `v2`

El frontend envía:

```json
{
  "ruta": "tmco-pcon",
  "fecha": "2023-10-18",
  "hora": "09:30",
  "tarifa_base": 5000,
  "capacidad_bus": 45,
  "tramos": [
    {
      "id": "tier-1",
      "name": "Promo temprana",
      "targetSeats": 10,
      "price": 4200,
      "color": "#0ea5e9"
    }
  ],
  "seatPlan": ["tier-1", null, null]
}
```

El backend:

1. valida `capacidad_bus`, `tramos` y `seatPlan`
2. calcula composición real del bus
3. construye `tarifa_promedio_ponderada`
4. estima ocupación con el modelo actual
5. devuelve ingreso, ocupación, curvas y sensibilidad

Respuesta adicional relevante:

- `composicion_bus`

Incluye:

- `asientos_base`
- `asientos_tarifados`
- `tarifa_promedio_ponderada`
- `ingreso_potencial_total`
- detalle por tramo

## Estructura del repositorio

```text
backend/
  app/
    main.py
  tests/
    test_main.py
frontend/
  index.html
.github/workflows/
  deploy.yml
Dockerfile
docker-compose.yml
requirements.txt
```

## Requisitos

- Python 3.11+ recomendado
- `pip`
- opcional: entorno virtual `.venv`
- opcional: Docker y Docker Compose para despliegue local/contenedorizado

## Ejecución local

### 1. Instalar dependencias

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

### 2. Levantar el servidor

```bash
PYTHONPATH=. ./.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8002
```

Abrir en navegador:

- `http://127.0.0.1:8002`

### 3. Verificar API

```bash
curl http://127.0.0.1:8002/openapi.json
curl http://127.0.0.1:8002/api/sistema/estado
curl http://127.0.0.1:8002/api/rutas
```

Debe existir este endpoint:

- `POST /api/simulacion/proyectar-v2`

## Pruebas

Suite actual:

```bash
.venv/bin/pytest -q backend/tests/test_main.py
```

Estado esperado actual:

- tests de backend y simulación `v2`
- un caso de carga CSV marcado como `skip` por comportamiento de `UploadFile.read()` en este entorno

## Despliegue con Docker

### Build y run local

```bash
docker compose up -d --build
```

Expone:

- `http://localhost:8001`

Persistencia Docker:

- volumen `jac_data`

## CI/CD

Workflow:

- `.github/workflows/deploy.yml`

Flujo actual:

1. `push` a `main`
2. GitHub Actions instala dependencias
3. corre `pytest backend/tests/test_main.py`
4. si pasa, hace deploy por SSH a Azure VM
5. en la VM ejecuta:
   - `git fetch`
   - `git reset --hard origin/main`
   - `docker compose down`
   - `docker compose up -d --build`

### Secrets necesarios

- `AZURE_VM_HOST`
- `AZURE_VM_USER`
- `AZURE_VM_KEY`
- `AZURE_VM_PORT` opcional

## Comandos útiles

### Reiniciar backend local

```bash
pkill -f "uvicorn backend.app.main:app" || true
PYTHONPATH=. ./.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8002
```

### Verificar endpoint `v2`

```bash
curl -X POST http://127.0.0.1:8002/api/simulacion/proyectar-v2 \
  -H "Content-Type: application/json" \
  --data '{"ruta":"tmco-pcon","fecha":"2023-10-18","hora":"09:30","tarifa_base":5000,"capacidad_bus":45,"tramos":[],"seatPlan":[null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null]}'
```

## Notas

- `MEMORIA_BACKEND.md` documenta el traspaso entre el modelo viejo y la simulación nueva basada en tramos.
- La simulación `v2` ya está integrada con el frontend actual.
- La lógica predictiva todavía usa una aproximación por `tarifa_promedio_ponderada`; el siguiente salto natural es modelar demanda por tramo o por banda de precio.
