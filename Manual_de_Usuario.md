# Manual de Usuario — JAC Revenue Optimizer

---

> **Proyecto:** JAC Revenue Optimizer
> **Versión:** 1.0
> **Fecha:** Junio 2026
> **Repositorio:** Proyecto-Capstone (Buses JAC)

---

## Tabla de Contenido

1. [Introducción](#1-introducción)
2. [Requisitos del Sistema](#2-requisitos-del-sistema)
3. [Instalación e Implementación](#3-instalación-e-implementación)
4. [Configuración](#4-configuración)
5. [Primer Inicio del Sistema](#5-primer-inicio-del-sistema)
6. [Inicio de Sesión y Acceso](#6-inicio-de-sesión-y-acceso)
7. [Navegación por la Interfaz](#7-navegación-por-la-interfaz)
8. [Funcionalidades](#8-funcionalidades)
9. [Explicación de Gráficos, Indicadores y Métricas](#9-explicación-de-gráficos-indicadores-y-métricas)
10. [Flujo Completo de Uso](#10-flujo-completo-de-uso)
11. [Casos de Uso](#11-casos-de-uso)
12. [Preguntas Frecuentes (FAQ)](#12-preguntas-frecuentes-faq)
13. [Solución de Problemas](#13-solución-de-problemas)
14. [Buenas Prácticas](#14-buenas-prácticas)
15. [Mantenimiento](#15-mantenimiento)
16. [Actualización del Sistema](#16-actualización-del-sistema)
17. [Desinstalación](#17-desinstalación)
18. [Glosario](#18-glosario)

---

## 1. Introducción

### 1.1 Qué es el sistema

**JAC Revenue Optimizer** es una aplicación web de optimización comercial diseñada para operadores de buses. Combina un motor de Machine Learning con una interfaz visual interactiva que permite gestionar la estrategia de precios de cada salida de bus de forma automática y basada en datos históricos reales.

El sistema permite definir **tramos comerciales de precios** (tiers) para cada servicio: distintos bloques de asientos con distintos precios de mayor a menor según el momento de compra. Esta lógica, conocida como *Revenue Management* o gestión de ingresos, permite maximizar los ingresos por salida al capturar pasajeros con distintas disposiciones a pagar.

### 1.2 Para qué sirve

El sistema sirve para que los equipos de pricing y operaciones de Buses JAC puedan:

- Recibir **recomendaciones automáticas** de cómo distribuir los precios de una salida en bloques comerciales.
- **Visualizar el mapa del bus** con los asientos coloreados según el tramo comercial asignado.
- **Proyectar ingresos y ocupación** esperados para cada configuración de precios antes de aplicarla.
- **Analizar la sensibilidad** del ingreso ante cambios en precio o estructura de asientos.
- **Comparar** la proyección sugerida contra el escenario histórico base.
- **Entrenar el motor predictivo** con datos históricos de ventas propios de la empresa.

### 1.3 Problema que resuelve

En la gestión tradicional de buses, los precios de los boletos se definen de forma fija o con escasa diferenciación. Esto genera dos problemas frecuentes:

1. **Subutilización de la capacidad:** pasajeros que hubieran comprado a un precio menor no lo hacen porque el precio único es muy alto.
2. **Pérdida de margen:** pasajeros dispuestos a pagar más compran al precio más bajo disponible.

JAC Revenue Optimizer resuelve ambos problemas al sugerir automáticamente una escalera de precios por tramos, basada en la demanda histórica de cada combinación de ruta/hora/temporada/tipo de día.

### 1.4 Beneficios

| Beneficio | Descripción |
|---|---|
| Incremento de ingresos | Captura pasajeros en distintas bandas de precio |
| Ahorro de tiempo | Recomendaciones automáticas en segundos |
| Basado en datos | El motor aprende del historial real de ventas |
| Visualización intuitiva | Mapa del bus coloreado, gráficos de proyección |
| Sin configuración compleja | Interfaz web, sin instalación en el equipo cliente |
| Adaptable | Acepta datos reales de cualquier período |

### 1.5 Público Objetivo

Este manual está dirigido a:

- **Analistas de Revenue Management** que definen estrategias de pricing.
- **Administradores del sistema** que gestionan la configuración, la carga de datos y el mantenimiento.
- **Personal de operaciones** que consulta recomendaciones por salida.
- **Equipos de TI** responsables del despliegue y mantenimiento técnico.

---

## 2. Requisitos del Sistema

### 2.1 Requisitos de Software

#### Para ejecución local (sin Docker)

| Componente | Versión mínima | Notas |
|---|---|---|
| Python | 3.11 o superior | Se recomienda 3.11 |
| pip | Cualquier versión reciente | Incluido con Python |
| Git | Cualquier versión | Para clonar el repositorio |
| Entorno virtual | — | Recomendado: `.venv` |

#### Para ejecución con Docker

| Componente | Versión mínima | Notas |
|---|---|---|
| Docker Engine | 24.x o superior | Incluye Docker CLI |
| Docker Compose | 2.x o superior | Incluido en Docker Desktop |

### 2.2 Dependencias Python (instaladas automáticamente)

| Librería | Versión | Uso |
|---|---|---|
| `fastapi` | 0.136.3 | Framework del API backend |
| `uvicorn` | 0.49.0 | Servidor ASGI |
| `sqlalchemy` | 2.0.50 | ORM y gestión de base de datos |
| `pandas` | 3.0.3 | Procesamiento de datos CSV |
| `numpy` | 2.4.6 | Cálculos numéricos |
| `scikit-learn` | 1.9.0 | Modelo de Machine Learning |
| `joblib` | 1.5.3 | Serialización del modelo |
| `python-multipart` | 0.0.30 | Carga de archivos CSV |
| `pytest` | 9.0.3 | Suite de pruebas automatizadas |
| `httpx` | 0.28.1 | Cliente HTTP para tests |

### 2.3 Requisitos de Hardware

| Recurso | Mínimo recomendado | Notas |
|---|---|---|
| CPU | 2 núcleos | El entrenamiento del modelo es intensivo en CPU |
| RAM | 2 GB libres | 4 GB recomendados para CSV grandes |
| Disco | 500 MB libres | Incluye Python, dependencias y base de datos |
| Red | Acceso a internet (inicial) | Solo para instalar dependencias y cargar CDN |

### 2.4 Navegadores Compatibles

| Navegador | Soporte |
|---|---|
| Google Chrome | Recomendado |
| Mozilla Firefox | Compatible |
| Microsoft Edge | Compatible |
| Safari | Compatible |
| Internet Explorer | No soportado |

> **IMPORTANTE:** El navegador debe tener JavaScript habilitado. La aplicación no funciona sin JavaScript.

### 2.5 Requisitos de Red

- **Puerto 8001** (Docker) o **8002** (local): el servidor FastAPI escucha en este puerto.
- Si el sistema se despliega en un servidor remoto (Azure VM u otro), el firewall debe permitir tráfico entrante en el puerto correspondiente.
- El frontend requiere acceso a internet para cargar librerías externas (Bootstrap, React, Plotly) desde CDN en el primer acceso o si el caché del navegador está vacío.

---

## 3. Instalación e Implementación

### 3.1 Clonar el Repositorio

**Objetivo:** Obtener el código fuente del proyecto en la máquina local.

```bash
git clone https://github.com/<organización>/Proyecto-Capstone.git
cd Proyecto-Capstone
```

**Resultado esperado:** Se crea el directorio `Proyecto-Capstone` con todos los archivos del proyecto.

**Posibles errores:**
- `git: command not found` — Instalar Git desde https://git-scm.com
- Permisos denegados — Verificar credenciales de acceso al repositorio.

---

### 3.2 Instalación Local (Sin Docker)

Esta opción es ideal para desarrollo y pruebas.

#### Paso 1: Crear entorno virtual

**Objetivo:** Aislar las dependencias del proyecto.

```bash
# Linux/macOS:
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell):
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Windows (cmd):
python -m venv .venv
.venv\Scripts\activate.bat
```

**Resultado esperado:** El prompt del terminal cambia para mostrar `(.venv)` al inicio.

**Posibles errores:**

| Error | Solución |
|---|---|
| `python3: command not found` | En Windows usar `python`. Verificar instalación de Python |
| Error de permisos en Windows | Ejecutar: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |

---

#### Paso 2: Instalar dependencias

**Objetivo:** Instalar todas las librerías Python necesarias.

```bash
pip install -r requirements.txt
```

**Resultado esperado:** Al finalizar se muestra `Successfully installed ...`.

**Posibles errores:**

| Error | Causa | Solución |
|---|---|---|
| `pip: command not found` | pip no instalado | Ejecutar `python -m ensurepip` |
| Errores de compilación | Faltan herramientas de compilación | Linux: `sudo apt-get install build-essential python3-dev`. Windows: instalar Microsoft C++ Build Tools |
| Versión incompatible | Python < 3.11 | Verificar versión: `python --version` |
| Timeout | Conexión lenta | Usar `pip install -r requirements.txt --timeout 120` |

---

#### Paso 3: Levantar el servidor

**Objetivo:** Iniciar el servidor web FastAPI.

```bash
# Linux/macOS:
PYTHONPATH=. .venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8002

# Windows (PowerShell):
$env:PYTHONPATH = "."
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8002
```

**Resultado esperado:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8002 (Press CTRL+C to quit)
```

Al arrancar por primera vez con la base de datos vacía, el sistema genera datos demo para la ruta `tmco-pcon` y entrena el modelo automáticamente. Este proceso puede tardar entre 5 y 30 segundos.

**Abrir en navegador:** http://127.0.0.1:8002

**Posibles errores:**

| Error | Causa | Solución |
|---|---|---|
| `Address already in use` | Puerto 8002 ocupado | Cambiar el puerto: `--port 8003` |
| `ModuleNotFoundError: No module named 'backend'` | PYTHONPATH no configurado | Asegurar `PYTHONPATH=.` al ejecutar |
| Pantalla en blanco | `frontend/index.html` no existe | Verificar que el archivo existe en `frontend/` |

---

#### Paso 4: Reiniciar el servidor local

```bash
# Detener:
pkill -f "uvicorn backend.app.main:app" || true

# Volver a iniciar:
PYTHONPATH=. .venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8002
```

---

### 3.3 Instalación con Docker

Opción recomendada para ambientes de producción.

#### Paso 1: Construir y levantar el contenedor

```bash
docker compose up -d --build
```

**Resultado esperado:**
```
[+] Building XX.Xs (12/12) FINISHED
[+] Running 1/1
 Container jac_revenue_sandbox  Started
```

**Abrir en navegador:** http://localhost:8001

**Posibles errores:**

| Error | Causa | Solución |
|---|---|---|
| `Cannot connect to the Docker daemon` | Docker no corre | Iniciar Docker Desktop |
| `port is already allocated` | Puerto 8001 en uso | Cambiar en `docker-compose.yml`: `"8080:8001"` |
| `Build failed` | Error de compilación | Revisar: `docker compose logs` |

---

#### Paso 2: Verificar que el contenedor corre

```bash
docker ps
```

**Resultado esperado:** Aparece `jac_revenue_sandbox` en estado `Up`.

---

#### Paso 3: Ver logs del contenedor

```bash
docker compose logs -f
```

Presionar `Ctrl+C` para salir del seguimiento.

---

#### Paso 4: Detener el contenedor

```bash
docker compose down
```

La base de datos y el modelo se conservan en el volumen `jac_data`. No se pierden datos.

---

#### Paso 5: Eliminar datos (uso con precaución)

> **ADVERTENCIA:** El siguiente comando elimina todos los datos persistidos de forma irreversible.

```bash
docker compose down -v
```

---

### 3.4 Verificación de la Instalación

Tras iniciar el sistema, verificar que la API responde:

```bash
# Estado del sistema:
curl http://127.0.0.1:8002/api/sistema/estado

# Rutas disponibles:
curl http://127.0.0.1:8002/api/rutas

# Documentación automática de la API (abrir en navegador):
# http://127.0.0.1:8002/docs
```

**Resultado esperado para `/api/sistema/estado`:**

```json
{
  "modelo_activo": true,
  "fecha_entrenamiento": "2026-06-30T...",
  "registros_procesados": 1080,
  "mae": 1.23,
  "rmse": 1.67,
  "r2": 0.85,
  "capacidad_bus": 45,
  "nombre_empresa": "Buses JAC",
  "rutas_disponibles": 1
}
```

---

### 3.5 Despliegue en Producción (Azure VM con CI/CD)

El proyecto incluye un flujo de CI/CD automático mediante GitHub Actions (`.github/workflows/deploy.yml`).

**Flujo automático:**
1. Se realiza un `push` a la rama `main`.
2. GitHub Actions instala dependencias y ejecuta los tests.
3. Si los tests pasan, se conecta por SSH a la Azure VM configurada.
4. En la VM ejecuta: `git fetch`, `git reset --hard origin/main`, `docker compose down`, `docker compose up -d --build`.

**Secrets requeridos en GitHub (Settings → Secrets → Actions):**

| Secret | Descripción |
|---|---|
| `AZURE_VM_HOST` | IP o hostname de la Azure VM |
| `AZURE_VM_USER` | Usuario SSH de la VM |
| `AZURE_VM_KEY` | Clave privada SSH (formato PEM) |
| `AZURE_VM_PORT` | Puerto SSH (opcional, por defecto 22) |

---

## 4. Configuración

### 4.1 Variables de Entorno

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `DATA_DIR` | `.` (directorio actual) | Ruta donde se almacenan `db.sqlite3` y `model.joblib` |
| `DATABASE_URL` | `sqlite:///./db.sqlite3` | URL de conexión a la base de datos |
| `TZ` | No definido | Zona horaria. Docker Compose lo fija en `America/Santiago` |

**Para definir en entorno local (Linux/macOS):**
```bash
export DATA_DIR=/ruta/personalizada
```

**Para definir en Docker Compose** (editar `docker-compose.yml`):
```yaml
environment:
  - DATA_DIR=/app/data
  - TZ=America/Santiago
```

---

### 4.2 Archivos de Configuración Principales

| Archivo | Descripción |
|---|---|
| `requirements.txt` | Lista de dependencias Python |
| `Dockerfile` | Instrucciones para construir la imagen Docker |
| `docker-compose.yml` | Orquestación del servicio Docker |
| `backend/app/main.py` | Código principal: API, modelo, base de datos |
| `frontend/index.html` | Interfaz web completa (React inline) |

---

### 4.3 Configuración de Capacidad y Empresa

Gestionadas desde la interfaz web (sección Configuración) y persistidas en la base de datos.

| Parámetro | Por defecto | Rango | Descripción |
|---|---|---|---|
| `capacidad_bus` | 45 | 1 a 100 | Número total de asientos. Afecta el mapa visual y los cálculos |
| `nombre_empresa` | "Buses JAC" | 1 a 100 caracteres | Nombre mostrado en el encabezado de la aplicación |

> **ADVERTENCIA:** Cambiar la capacidad del bus afecta todos los cálculos. Asegurarse de que el valor coincide con la flota real antes de generar recomendaciones.

---

### 4.4 Puertos del Servidor

| Modo | Puerto | URL de acceso |
|---|---|---|
| Local (uvicorn) | 8002 | http://127.0.0.1:8002 |
| Docker Compose | 8001 | http://localhost:8001 |

Para cambiar el puerto en Docker, editar `docker-compose.yml`:
```yaml
ports:
  - "NUEVO_PUERTO:8001"
```

---

### 4.5 Base de Datos

El sistema utiliza **SQLite**. El archivo `db.sqlite3` se crea automáticamente al arrancar. No requiere instalación adicional.

**Tablas creadas automáticamente:**

| Tabla | Descripción |
|---|---|
| `configuracion_sistema` | Configuración global y métricas del modelo |
| `registros_historicos` | Boletos individuales cargados desde CSV |
| `salidas_agregadas` | Salidas agrupadas por ruta/fecha/hora (para entrenar el modelo) |

En Docker, el archivo se persiste en el volumen `jac_data` (ruta interna: `/app/data/db.sqlite3`).

---

### 4.6 Modelo de Machine Learning

| Parámetro | Valor |
|---|---|
| Algoritmo | Random Forest Regressor |
| Variable objetivo | `asientos_vendidos` por salida |
| Variables de entrada | `ruta_encoded`, `dia_semana`, `es_fin_de_semana`, `mes`, `hora_salida_minutos`, `tarifa_promedio` |
| Estimadores | 30 árboles |
| División train/test | 80% / 20% |
| Elasticidad precio | -1.2 (por cada 1% de aumento en precio, la demanda cae 1.2%) |

El modelo entrenado se guarda en `model.joblib` en el directorio definido por `DATA_DIR`.

> **Nota:** Si la base de datos está vacía al arrancar, el sistema genera datos demo sintéticos y entrena automáticamente.

---

## 5. Primer Inicio del Sistema

### 5.1 Arranque con Datos Demo

Al iniciar el sistema por primera vez con la base de datos vacía, el backend automáticamente:

1. Genera 30 días de datos de venta sintéticos para la ruta `tmco-pcon` (Temuco a Puerto Montt).
2. Crea registros de salidas agregadas.
3. Entrena el modelo de Machine Learning.

Este proceso ocurre en segundo plano durante el arranque y puede tardar entre 5 y 30 segundos.

**Parámetros de los datos demo generados:**
- Ruta: `tmco-pcon`
- Horarios: 06:30, 07:00, 09:30, 13:00, 17:30, 19:00
- Precio promedio: $4.500 CLP
- Pasajeros promedio por salida: ~8 asientos
- Capacidad del bus: 45 asientos

### 5.2 Verificación del Primer Inicio

**En la terminal**, al arrancar el servidor:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8002
```
No deben aparecer errores en rojo.

**En el navegador**, al abrir la URL:
- El encabezado muestra "Buses JAC - Revenue Optimizer".
- El panel central muestra los selectores de ruta, hora, temporada y tipo de día.
- El panel "Recomendación Actual" muestra métricas de asientos y tarifa.

> **[Captura de pantalla sugerida: Pantalla principal del sistema con modelo activo]**

Si en cambio aparece una pantalla de "Cargue datos históricos para entrenar el motor...", significa que el modelo no está activo. Cargar el archivo CSV desde la sección Configuración.

### 5.3 Errores Frecuentes en el Primer Inicio

| Síntoma | Posible causa | Solución |
|---|---|---|
| Página en blanco | JavaScript deshabilitado | Habilitar JavaScript en el navegador |
| "Cannot GET /" | Servidor no iniciado | Verificar que uvicorn está corriendo |
| `modelo_activo: false` en la API | Seeder automático falló | Cargar CSV en la sección Configuración |
| Spinner indefinido | Error al cargar CDN | Verificar conexión a internet |

---

## 6. Inicio de Sesión y Acceso

> **Nota:** El sistema actual **no implementa autenticación de usuarios** (login/contraseña). Cualquier persona con acceso a la URL del servidor puede utilizarlo.

Si el sistema se despliega en un ambiente accesible desde internet, se recomienda:

1. **Restringir el acceso por IP** mediante firewall del servidor.
2. **Agregar autenticación HTTP básica** a través de un proxy inverso (nginx, Caddy, etc.).
3. **Utilizar una VPN** para acceder al servidor de forma segura.

La gestión de usuarios, roles y permisos no está implementada en la versión actual y debería considerarse como mejora futura si el sistema se expone públicamente.

---

## 7. Navegación por la Interfaz

### 7.1 Encabezado

El encabezado superior contiene:
- **Ícono y nombre:** emoji de bus + nombre de la empresa + "Revenue Optimizer".
- **Botón "Dashboard Sandbox":** Accede a la vista principal de recomendaciones.
- **Botón "Configuración":** Accede a la configuración del sistema y carga de CSV.

El botón activo se muestra con fondo rojo oscuro; el inactivo con borde gris.

> **[Captura de pantalla sugerida: Encabezado de la aplicación]**

---

### 7.2 Vista Principal: Dashboard Sandbox

#### Sección 1 — Salida a Recomendar (barra superior)

Cuatro selectores en línea horizontal:

| Campo | Opciones disponibles | Descripción |
|---|---|---|
| **Ruta** | Rutas disponibles en el modelo | Selecciona el origen y destino del servicio |
| **Hora del Servicio** | Horas disponibles para esa ruta | Selecciona el horario de salida |
| **Temporada** | Temporada Media, Verano, Invierno | Determina el contexto estacional |
| **Tipo de Día** | Semana, Fin de semana | Afecta la demanda estimada |

Las combinaciones de Temporada y Tipo de Día se mapean internamente a fechas concretas:

| Temporada | Tipo de Día | Fecha utilizada |
|---|---|---|
| Temporada Media | Semana | 2023-10-18 |
| Temporada Media | Fin de semana | 2023-10-21 |
| Verano | Semana | 2023-01-18 |
| Verano | Fin de semana | 2023-01-21 |
| Invierno | Semana | 2023-07-19 |
| Invierno | Fin de semana | 2023-07-22 |

> **[Captura de pantalla sugerida: Barra de selectores "Salida a Recomendar"]**

---

#### Sección 2 — Panel Principal (dos columnas)

**Columna izquierda — Tramos Sugeridos:**

| Elemento | Descripción |
|---|---|
| Encabezado del panel | Muestra la ruta y hora seleccionadas |
| Botón de reinicio (↺) | Limpia todos los tramos y el bus |
| Tarifa de referencia | Campo editable: precio base para calcular multiplicadores de tramo |
| Lista de tramos | Cada tramo con nombre, asientos y precio |
| Botón "Añadir tramo manual" | Agrega un tramo adicional manualmente |

**Columna derecha — Mapa del Bus + Recomendación Actual:**

| Elemento | Descripción |
|---|---|
| Mapa del Bus | Visualización horizontal del bus con asientos coloreados por tramo |
| Recomendación Actual | Métricas: asientos tarifados, tarifa promedio, asientos base |
| Estrategia y justificación | Aparece tras generar una recomendación |
| Botón "Generar recomendación" | Llama al motor de recomendación automática |

> **[Captura de pantalla sugerida: Vista principal con mapa del bus y tramos coloreados]**

---

#### Sección 3 — Resultados (aparece tras generar una recomendación)

1. **KPI de Ingreso Total Proyectado** con variación vs. base.
2. **KPI de Ocupación Proyectada** con gráfico donut.
3. **Cuatro gráficos de análisis** (detallados en la sección 9).

---

### 7.3 Vista de Configuración

Accesible desde el botón "Configuración" del encabezado. Contiene:

- **Formulario de configuración:** Editar capacidad del bus y nombre de empresa.
- **Estado del Modelo Activo:** Métricas del modelo (fecha, registros, MAE, RMSE, R²).
- **Área de carga de CSV:** Para subir datos históricos y reentrenar el modelo.

> **[Captura de pantalla sugerida: Vista de Configuración del sistema]**

---

## 8. Funcionalidades

### 8.1 Generación de Recomendación Automática de Tramos

#### Objetivo
Obtener automáticamente una propuesta de estructura de precios por tramos para una salida específica.

#### Descripción
El sistema analiza la ruta, hora, temporada y tipo de día seleccionados, estima la demanda base con el modelo de ML, y construye entre 2 y 4 tramos comerciales cuyos precios maximizan el ingreso esperado.

**Regla estructural de inventario (siempre respetada):**
- El primer tramo tiene exactamente **10 asientos**.
- Los tramos siguientes se construyen en bloques de **5 asientos**.
- Ejemplo válido: `10 + 20 + 15 = 45 asientos`.

**Estrategias según demanda estimada:**

| Ocupación base estimada | Estrategia | Tramos | Rango de precios |
|---|---|---|---|
| Menor de 35% de capacidad | Estimular demanda | 2 a 3 | 82% a 108% de tarifa base |
| Entre 35% y 70% | Balancear volumen y yield | 2 a 4 | 90% a 118% de tarifa base |
| Mayor de 70% | Proteger yield | 3 a 4 | 95% a 134% de tarifa base |

**Nombre de tramos sugeridos:** Apertura, Impulso, Consolidación, Cierre.

#### Cómo acceder
1. Ir a la vista **Dashboard Sandbox**.
2. Seleccionar Ruta, Hora, Temporada y Tipo de Día.
3. Verificar o ajustar la **Tarifa de referencia**.
4. Hacer clic en el botón **"Generar recomendación"**.

#### Procedimiento paso a paso

1. El botón muestra "Generando recomendación..." con spinner.
2. Se llama al endpoint `POST /api/recomendacion/tramos`.
3. El panel **Tramos Sugeridos** se rellena con los tramos generados.
4. El **Mapa del Bus** se colorea con los asientos asignados a cada tramo.
5. Se muestran los KPIs de ingreso y ocupación proyectados.
6. Se renderizan los cuatro gráficos de análisis.

#### Resultado esperado

- Mapa del bus con asientos coloreados por tramo.
- Panel izquierdo con tramos: nombre, asientos y precio.
- Sección de resultados con ingreso, ocupación proyectada y gráficos.

> **[Captura de pantalla sugerida: Resultado de la recomendación con bus pintado y gráficos]**

#### Posibles errores

| Error | Causa | Solución |
|---|---|---|
| "Seleccione una ruta y una salida" | No hay ruta u hora seleccionada | Seleccionar ruta y hora en la barra superior |
| "El modelo no ha sido entrenado" | No hay modelo activo | Cargar CSV en Configuración |
| "Ruta no encontrada en el modelo" | La ruta no está en los datos de entrenamiento | Verificar que el CSV contiene esa ruta |

#### Recomendaciones
- Ingresar una tarifa de referencia cercana al precio de mercado actual de esa ruta.
- Si la recomendación no parece óptima, ajustar la tarifa de referencia y volver a generar.

---

### 8.2 Edición Manual de Tramos

#### Objetivo
Ajustar manualmente los tramos sugeridos o crear una estructura de precios personalizada.

#### Cómo acceder
Los tramos se editan directamente en el panel izquierdo "Tramos Sugeridos".

#### Procedimiento paso a paso

**Para editar un tramo existente:**
1. Hacer clic en el campo **Nombre** para renombrarlo.
2. Modificar el campo **Asientos** (el bus se redistribuye automáticamente).
3. Modificar el campo **Precio CLP**.
4. Los cambios se reflejan instantáneamente en el mapa y las métricas.

**Para agregar un tramo:**
1. Hacer clic en **"Añadir tramo manual"**.
2. Editar nombre, asientos y precio del nuevo tramo.

**Para eliminar un tramo:**
1. Hacer clic en el ícono de papelera del tramo.
2. El botón está deshabilitado si solo queda un tramo.

**Para reiniciar todos los tramos:**
1. Hacer clic en el botón **↺** en la esquina superior del panel.
2. Se eliminan todos los tramos y el bus vuelve a mostrar todos los asientos como "Base".

#### Nota
Al modificar la cantidad de asientos de un tramo, el mapa del bus se recalcula automáticamente distribuyendo los asientos en orden secuencial (tramo 1 primero, luego tramo 2, etc.). Si la suma supera la capacidad, los asientos sobrantes simplemente no se asignan.

---

### 8.3 Mapa Visual del Bus

#### Objetivo
Visualizar de forma intuitiva cómo están distribuidos los tramos de precios asiento por asiento.

#### Descripción

El mapa del bus muestra una representación horizontal del vehículo:

- **Frente del bus** a la izquierda: ícono del volante y precio base visible.
- **Columnas de asientos:** cada columna tiene 4 asientos (2 arriba + pasillo + 2 abajo).
- **Asientos con color:** pertenecen a un tramo comercial. El color coincide con el del tramo.
- **Asientos neutros (beige):** asientos base que se venden a la tarifa de referencia.
- **Número de asiento:** mostrado dentro de cada botón.
- **Etiqueta de tramo:** mostrada bajo el número ("Base", "T1", "T2", etc.).

**Colores por defecto de los tramos:**

| Tramo | Color | Código hexadecimal |
|---|---|---|
| Tramo 1 (Apertura) | Azul cielo | #0ea5e9 |
| Tramo 2 (Impulso) | Naranja | #f97316 |
| Tramo 3 (Consolidación) | Morado | #8b5cf6 |
| Tramo 4 (Cierre) | Verde | #22c55e |

> **[Captura de pantalla sugerida: Mapa del bus con asientos coloreados por tramo]**

> **Nota:** En la versión actual, los asientos del mapa son de solo lectura. No se puede hacer clic en ellos para asignarlos individualmente. La asignación se gestiona mediante la cantidad de asientos en cada tramo del panel izquierdo.

---

### 8.4 Carga de Datos Históricos (CSV)

#### Objetivo
Alimentar el sistema con datos reales de ventas para entrenar el modelo de ML con información propia.

#### Descripción
Al cargar un CSV, el sistema:
1. Elimina todos los datos anteriores (incluyendo datos demo).
2. Inserta los boletos válidos del CSV.
3. Reconstruye las salidas agregadas.
4. Reentrena el modelo de Machine Learning.

#### Formato requerido del CSV

**Columnas obligatorias:**

| Columna | Descripción | Formato |
|---|---|---|
| `NRO_BOLETO` | Número de boleto | Entero |
| `VALOR` | Precio del boleto en CLP | Entero |
| `ORIGEN_DESTINO` | Ruta en formato "origen-destino" | Texto: `tmco-pcon` |
| `FECHA_SALIDA_SERVICIO` | Fecha de la salida | `YYYYMMDD` (ej: `20231018`) |
| `HORA_SALIDA_SERVICIO` | Hora de la salida | `HHMM` (ej: `0930`) |
| `FECHA_COMPRA` | Fecha de compra del boleto | `YYYYMMDD` |

**Columnas opcionales:**

| Columna | Descripción |
|---|---|
| `LINEA` | Número de línea del servicio |
| `TIPO_ASIENTO` | Tipo de asiento ("Clas.Cort.", "Semi Cama", etc.) |
| `CANAL_VENTA` | Canal de venta ("Presencial", "Online", etc.) |
| `SUBCANAL_VENTA` | Subcanal de venta |

> **Nota:** El archivo `OCTUBRE23_ANON.csv` en la raíz del proyecto sirve como referencia del formato correcto.

#### Cómo acceder
- Botón **"Configuración"** en el encabezado → Sección inferior "Entrenar nuevamente con un nuevo CSV".
- También disponible en la pantalla de bienvenida si el modelo no está activo.

#### Procedimiento paso a paso

1. Ir a la sección **Configuración**.
2. Hacer clic en el área de carga de archivos (borde punteado).
3. Seleccionar el archivo CSV desde el explorador.
4. Esperar el procesamiento ("Cargando CSV y entrenando modelo...").
5. Al finalizar, aparece: "Modelo entrenado exitosamente con los datos del CSV."
6. Las métricas del modelo se actualizan.

> **[Captura de pantalla sugerida: Área de carga de CSV con indicador de progreso]**

#### Resultado esperado

- "Registros Procesados" muestra el número de boletos cargados.
- Las métricas MAE, RMSE y R² del modelo se actualizan.
- "Rango Temporal de Ventas" muestra las fechas del dataset.
- "Rutas Únicas" muestra el número de rutas en el CSV.

#### Posibles errores

| Error | Causa | Solución |
|---|---|---|
| "Faltan columnas obligatorias: ..." | CSV sin formato correcto | Verificar columnas requeridas |
| "No se cargó ningún boleto válido" | Todos los registros tienen errores | Revisar formato de fechas y valores |
| Error al procesar CSV | Datos corruptos o encoding incorrecto | Guardar el CSV en UTF-8 y verificar integridad |

---

### 8.5 Configuración del Sistema

#### Objetivo
Ajustar los parámetros base del sistema: capacidad del bus y nombre de empresa.

#### Cómo acceder
Botón **"Configuración"** en el encabezado → Sección "Configuración del Sistema".

#### Procedimiento paso a paso

1. Ir a la sección **Configuración**.
2. Modificar **Capacidad Total de Bus** (1 a 100).
3. Modificar **Nombre de la Empresa** (texto libre).
4. Hacer clic en **"Guardar Configuración"**.
5. Aparece la alerta: "Configuración actualizada."

#### Impacto de los cambios

- **Capacidad del bus:** El mapa del bus se reconstruye. Los cálculos de ocupación e ingreso usan el nuevo valor. Las recomendaciones usan la nueva capacidad.
- **Nombre de empresa:** Solo afecta el texto del encabezado.

---

### 8.6 Consulta del Estado del Modelo

#### Objetivo
Verificar el estado y la calidad del modelo de Machine Learning activo.

#### Cómo acceder
Botón **"Configuración"** → Sección "Estado del Modelo Activo".

#### Información mostrada

| Campo | Descripción |
|---|---|
| Fecha de Último Entrenamiento | Cuándo se entrenó el modelo por última vez |
| Registros Procesados del CSV | Número de boletos usados para entrenar |
| MAE (Error Medio Absoluto) | Error promedio del modelo en asientos |
| RMSE (Raíz de Error Cuadrático Medio) | Error cuadrático medio |
| R² (Coeficiente de Determinación) | Qué porcentaje de la variabilidad explica el modelo |
| Rango Temporal de Ventas | Fechas mínima y máxima del dataset |
| Rutas Únicas | Número de rutas distintas en el dataset |

#### Interpretación de métricas del modelo

| Métrica | Valor ideal | Interpretación |
|---|---|---|
| MAE | Menor de 3 asientos | El modelo se equivoca en promedio en menos de 3 asientos |
| RMSE | Menor de 4 asientos | Los errores grandes son infrecuentes |
| R² | Mayor de 0.7 | El modelo explica más del 70% de la variabilidad de la demanda |

---

### 8.7 Simulación Manual por API (Uso Avanzado)

Para usuarios avanzados o integraciones externas, existe un endpoint de simulación directa sin usar el recomendador automático.

**Endpoint:** `POST /api/simulacion/proyectar-v2`

**Estructura del request:**

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
  "seatPlan": ["tier-1", "tier-1", ..., null, null]
}
```

El `seatPlan` es un array de N elementos (donde N es `capacidad_bus`). Cada elemento es el `id` del tramo o `null` (asiento base).

La documentación completa de todos los endpoints está disponible en: `http://127.0.0.1:8002/docs`

---

## 9. Explicación de Gráficos, Indicadores y Métricas

### 9.1 KPI 1: Ingreso Total Proyectado

**Qué representa:** El ingreso total esperado en CLP para esa salida, si se vende según la ocupación proyectada con la estructura de tramos actual.

**Fórmula:**
```
Ingreso Proyectado = Ingreso Potencial Total × (Ocupación Proyectada / Capacidad)
```

donde `Ingreso Potencial Total = Σ(asientos_tramo × precio_tramo) + (asientos_base × tarifa_base)`

**Badge de variación:**
- Verde con (arriba) +X%: la estrategia de tramos mejora el ingreso respecto al base histórico.
- Rojo con (abajo) -X%: la estrategia propuesta genera menos ingreso que el base.

**Interpretación de valores:**
- **Positivo alto (+10% o más):** Estrategia muy efectiva. El diferencial de precios por tramos captura bien la disposición a pagar.
- **Positivo moderado (+1% a +10%):** Mejora incrementa el ingreso. Vale la pena implementar.
- **Negativo:** Puede ocurrir legítimamente en estrategias de "Estimular demanda" donde el objetivo es aumentar ocupación aunque baje el ingreso unitario.

---

### 9.2 KPI 2: Ocupación Proyectada

**Qué representa:** El porcentaje de asientos que el modelo estima que se venderán para esa salida con la estructura de precios propuesta.

**Gráfico donut:**
- Arco relleno: porcentaje de ocupación estimada.
- Color del arco:
  - Verde: 80% o más de ocupación (demanda fuerte).
  - Amarillo/ámbar: entre 50% y 79% (demanda media).
  - Rojo: menos del 50% (demanda débil).

**Badge de variación:**
- Diferencia en puntos porcentuales (pp) respecto al escenario base.
- Ejemplo: "▲ +3.2 pp vs. Base" significa que la estrategia proyecta 3.2 puntos más de ocupación que el escenario histórico base.

**Interpretación:**
- Ocupación alta con ingreso bajo: los precios son demasiado bajos. Considerar aumentar los tramos superiores.
- Ocupación baja con ingreso alto: los precios son altos. El sistema está priorizando yield sobre volumen. Evaluar si el negocio lo permite.
- Ocupación y ingreso altos: escenario ideal.

---

### 9.3 Gráfico 1: Comparativa de Ingresos (Base vs Simulado)

> **[Captura de pantalla sugerida: Gráfico de barras comparativo]**

**Tipo:** Gráfico de barras agrupadas.

**Eje X:** Categoría "Ingreso Proyectado ($)".

**Eje Y:** Monto en CLP.

**Series:**

| Serie | Color | Descripción |
|---|---|---|
| Histórico Base | Gris (#94a3b8) | Ingreso estimado sin estructura de tramos (precio histórico promedio × ocupación base) |
| Escenario Simulado | Rojo (#dc2626) | Ingreso proyectado con la estructura de tramos generada |

**Cómo interpretar:**
- Barra roja más alta que la barra gris: la estrategia de tramos supera al escenario base.
- Barra roja más baja: la estrategia propuesta genera menos ingreso absoluto (puede ser aceptable si aumenta la ocupación).
- Los valores en CLP se muestran sobre cada barra.

**Cómo usar para la toma de decisiones:**
- Usar este gráfico para justificar ante la gestión si una nueva estrategia de precios es rentable.
- Comparar escenarios generando múltiples recomendaciones con distintas tarifas de referencia.

---

### 9.4 Gráfico 2: Booking Curve (Ritmo de Venta)

> **[Captura de pantalla sugerida: Gráfico de curvas de booking]**

**Tipo:** Gráfico de líneas con área rellena.

**Eje X:** Días de anticipación (de -30 a 0, donde 0 es el día de la salida).

**Eje Y:** Asientos vendidos acumulados.

**Series:**

| Serie | Color | Tipo | Descripción |
|---|---|---|---|
| Histórico Promedio | Gris (#94a3b8) | Línea continua con área | Promedio histórico de ventas acumuladas antes de la salida |
| Proyección Escenario | Rojo (#dc2626) | Línea punteada con área | Proyección escalada según la ocupación estimada del escenario actual |
| Capacidad | Negro punteado | Línea horizontal | Límite de capacidad del bus (N asientos) |

**Cómo interpretar:**
- El eje X va de -30 (30 días antes) a 0 (día de la salida). Los valores negativos son "días de anticipación".
- Una curva histórica que sube abruptamente cerca del día 0: ventas concentradas de última hora.
- Una curva que sube gradualmente: compras con anticipación distribuida.
- La proyección escala la curva histórica para que el punto final (día 0) coincida con la ocupación proyectada.
- Si la proyección está muy por encima de la histórica: el escenario asume una tasa de compra significativamente mejor que el histórico.

**Cómo usar para la toma de decisiones:**
- Si las ventas se concentran en los últimos días (-5 a 0), los tramos baratos ("Apertura") pueden venderse muy cerca del viaje, reduciendo la oportunidad de capturar precio más alto.
- Ajustar los tamaños de los tramos según el patrón de compra histórico.

---

### 9.5 Gráfico 3: Análisis de Sensibilidad — Tornado Chart

> **[Captura de pantalla sugerida: Gráfico tornado]**

**Tipo:** Gráfico de barras horizontales (formato tornado).

**Eje X:** Variación del Ingreso en CLP respecto al escenario actual (positivo o negativo).

**Eje Y:** Variables analizadas.

**Variables analizadas en la simulación v2:**

| Variable | Qué mide |
|---|---|
| Tarifa promedio ponderada | Efecto de subir o bajar toda la estructura de precios un 10% |
| Asientos base | Efecto de mover asientos entre la tarifa base y los tramos con precio |

**Series:**

| Serie | Color | Descripción |
|---|---|---|
| Subida +10% | Verde (#16a34a) | Impacto en ingreso si se sube esa variable un 10% |
| Bajada -10% | Rojo (#dc2626) | Impacto en ingreso si se baja esa variable un 10% |

**Cómo interpretar:**
- Barras más largas: variables con mayor impacto en el ingreso.
- Barra verde larga hacia la derecha: subir ese parámetro aumenta significativamente el ingreso.
- Barra roja larga hacia la izquierda: bajar ese parámetro reduce significativamente el ingreso.
- Si ambas barras son cortas: el ingreso es poco sensible a esa variable (la variable no es la palanca principal).
- Asimetría entre la barra verde y la roja: el impacto no es proporcional (efecto no lineal de la elasticidad).

**Cómo usar para la toma de decisiones:**
- Si "Tarifa promedio" domina (barra verde larga): el precio es la palanca principal. Considerar subir los tramos superiores.
- Si "Asientos base" domina: la composición del bus es la palanca principal. Evaluar reducir los asientos base para aumentar los asientos de tramos con precio.

---

### 9.6 Gráfico 4: Sensibilidad Cruzada (Precio vs Asientos Base)

> **[Captura de pantalla sugerida: Gráfico de sensibilidad cruzada]**

**Tipo:** Gráfico de líneas con marcadores.

**Eje X:** Cantidad de Asientos Base (variaciones del valor actual: -5, 0, +5, +10 asientos).

**Eje Y:** Ingreso Total proyectado en CLP.

**Series (cuatro líneas, una por nivel de precio):**

| Serie | Color | Descripción |
|---|---|---|
| -5% precio | Cian (#4db6ac) | Ingreso si se baja la estructura de precios un 5% |
| 0% precio | Naranja (#e28743) | Ingreso con la estructura actual (sin cambios) |
| +5% precio | Azul (#5c6bc0) | Ingreso si se sube la estructura de precios un 5% |
| +10% precio | Rosa (#ec4899) | Ingreso si se sube la estructura de precios un 10% |

**Cómo interpretar:**
- Si las líneas tienen pendiente negativa (descienden de izquierda a derecha): reducir los asientos base (aumentar asientos de tramo) mejora el ingreso.
- Si las líneas tienen pendiente positiva: aumentar los asientos base mejora el ingreso (situación poco común).
- Las líneas más altas corresponden al mayor precio. Si las líneas están muy juntas: el precio tiene poco efecto marginal en el ingreso.
- El punto óptimo es la combinación de precio y asientos base donde la línea más alta alcanza su valor máximo.

**Qué eje representa qué:**
- Eje X ("Asientos Base"): cuántos asientos se venden al precio base sin tramo asignado.
- Eje Y ("Ingreso Total CLP"): el ingreso proyectado total de la salida.
- Cada línea ("Nivel de precio"): escenario con toda la estructura de tramos subida o bajada en ese porcentaje.

**Cómo usar para la toma de decisiones:**
- Encontrar la combinación óptima de precio y proporción de asientos base vs. tarifados.
- Evaluar si es rentable "sacrificar" asientos base para aumentar los asientos en tramos con precio.
- Identificar si el sistema es más sensible a cambios de precio o a cambios de composición de asientos.

---

### 9.7 Panel "Recomendación Actual" — Métricas Instantáneas

Calculadas en tiempo real en el frontend, se actualizan con cada cambio en los tramos:

| Métrica | Descripción | Fórmula |
|---|---|---|
| Asientos tarifados | Asientos con tramo asignado | Σ(asientos_por_tramo) |
| Tarifa promedio | Precio promedio ponderado de todos los asientos | (Σ(asientos_tramo × precio_tramo) + asientos_base × tarifa_base) / capacidad |
| Asientos base | Asientos sin tramo, al precio base | capacidad - asientos_tarifados |

Si hay una recomendación cargada, también muestra:

| Campo | Descripción |
|---|---|
| Estrategia elegida | Nombre de la estrategia del sistema |
| Justificación | Texto explicando por qué se eligió esa estrategia |
| Demanda base estimada | Asientos que el modelo predice se venderían al precio base |
| Tarifa sugerida promedio | Tarifa promedio de la estructura recomendada |

---

### 9.8 Panel "Tramos Sugeridos" — Métricas por Tramo

Para cada tramo individual se muestran:

| Métrica | Descripción |
|---|---|
| Nombre | Nombre editable del tramo |
| Asientos objetivo | Cantidad de asientos que se quiere asignar |
| Precio CLP | Precio de venta de los asientos de este tramo |
| Asientos asignados | Asientos efectivamente asignados en el mapa del bus |
| Subtotal | `asientos_asignados × precio` = ingreso potencial bruto del tramo |

---

## 10. Flujo Completo de Uso

### Contexto
Un analista de Revenue Management de Buses JAC quiere obtener una recomendación de precios para el servicio de las 09:30 de la ruta Temuco a Puerto Montt, un día de semana en temporada media.

---

**Paso 1: Acceder al sistema**

1. Abrir el navegador y navegar a la URL del sistema (ej: http://localhost:8001).
2. Verificar que la interfaz carga con el encabezado "Buses JAC - Revenue Optimizer".

---

**Paso 2: Verificar que el modelo está activo**

1. Confirmar que se muestra la vista principal del Dashboard (no la pantalla de carga de CSV).
2. Opcionalmente, ir a Configuración y verificar que "Fecha de Último Entrenamiento" tiene una fecha válida.

---

**Paso 3: Seleccionar la salida a analizar**

1. En la barra superior, seleccionar:
   - Ruta: `TMCO -> PCON`
   - Hora del Servicio: `09:30`
   - Temporada: `Temporada Media`
   - Tipo de Día: `Semana`
2. El sistema actualiza automáticamente los datos de referencia de esa salida.

---

**Paso 4: Establecer la tarifa de referencia**

1. En el panel izquierdo, localizar el campo "Precio referencia CLP".
2. Ingresar el precio base de referencia (por ejemplo: $4.954 CLP según el historial de esa ruta).

---

**Paso 5: Generar la recomendación**

1. En el panel "Recomendación Actual", hacer clic en **"Generar recomendación"**.
2. Esperar 2 a 5 segundos mientras el sistema procesa.

---

**Paso 6: Analizar los tramos sugeridos**

1. Revisar en el panel izquierdo los tramos sugeridos. Ejemplo de resultado:
   - Apertura: 10 asientos a $4.100 CLP
   - Impulso: 15 asientos a $4.700 CLP
   - Cierre: 20 asientos a $5.200 CLP
2. Revisar el mapa del bus: primeros 10 asientos en azul, siguientes 15 en naranja, últimos 20 en morado.
3. Revisar la estrategia: "Balancear volumen y yield" con su justificación.

---

**Paso 7: Analizar los resultados proyectados**

1. Revisar los KPIs superiores:
   - Ingreso proyectado: $42.350 CLP (+8.2% vs. Base)
   - Ocupación proyectada: 67.4% (con variación vs. Base)
2. Analizar el Gráfico Comparativo de Ingresos para confirmar que la propuesta supera al base.
3. Analizar el Booking Curve para entender el patrón de venta esperado.
4. Analizar el Tornado Chart para identificar la palanca de mayor impacto.
5. Analizar la Sensibilidad Cruzada para evaluar si ajustar precios o composición de asientos.

---

**Paso 8: Ajustar si es necesario**

1. Para explorar variantes:
   - Cambiar la tarifa de referencia y volver a generar la recomendación.
   - Modificar manualmente el número de asientos de algún tramo y observar el cambio en métricas.
2. Los gráficos y KPIs solo se actualizan al hacer clic en "Generar recomendación" nuevamente.

---

**Paso 9: Documentar la decisión**

1. Registrar la estructura de tramos aprobada (nombre, asientos, precio por tramo).
2. Implementar la configuración en el sistema de venta de boletos correspondiente.

---

## 11. Casos de Uso

### Caso 1: Ruta con Alta Demanda (Fin de Semana en Verano)

**Objetivo:** Maximizar el yield en una salida con alta demanda esperada.

**Pasos:**
1. Seleccionar Temporada: Verano, Tipo de Día: Fin de semana.
2. Seleccionar el horario de mayor demanda (09:30 o 17:30).
3. Generar recomendación.

**Resultado esperado:**
- Estrategia "Proteger yield" con 3 a 4 tramos.
- Precios escalonados hacia arriba (hasta 130% de la tarifa base).
- Ocupación proyectada alta (mayor de 75%).
- Ingreso proyectado significativamente superior al base.

---

### Caso 2: Ruta con Baja Demanda (Día de Semana, Horario Poco Popular)

**Objetivo:** Estimular ventas con precios atractivos en la primera parte del inventario.

**Pasos:**
1. Seleccionar horario de menor demanda (13:00 en día de semana).
2. Generar recomendación.

**Resultado esperado:**
- Estrategia "Estimular demanda" con 2 tramos.
- Primer tramo con precio por debajo de la tarifa base (82-85%).
- Menor ingreso unitario pero potencialmente mayor ocupación.

---

### Caso 3: Carga de Nuevos Datos y Reentrenamiento

**Objetivo:** Actualizar el modelo con datos históricos recientes.

**Pasos:**
1. Obtener el archivo CSV de ventas del período más reciente.
2. Ir a Configuración y cargar el CSV.
3. Verificar las métricas del modelo actualizado (MAE, R²).
4. Regresar al Dashboard y generar recomendaciones con el modelo actualizado.

**Resultado esperado:**
- El modelo se reentrena con los nuevos datos.
- Las rutas disponibles reflejan el nuevo CSV.
- Las recomendaciones incorporan los patrones del período reciente.

---

### Caso 4: Ajuste de Capacidad de Bus

**Objetivo:** Configurar el sistema para una flota con distinta capacidad de asientos.

**Pasos:**
1. Ir a Configuración.
2. Cambiar "Capacidad Total de Bus" al nuevo valor (ej: 50).
3. Guardar la configuración.
4. Regresar al Dashboard y verificar el mapa del bus.
5. Generar una recomendación para confirmar el funcionamiento con la nueva capacidad.

**Resultado esperado:**
- El mapa del bus muestra la nueva cantidad de asientos.
- Los tramos sugeridos suman exactamente la nueva capacidad total.

---

### Caso 5: Exploración de Sensibilidad de Precios

**Objetivo:** Evaluar cuánto impacto tiene aumentar los precios en una salida de demanda media.

**Pasos:**
1. Generar una recomendación para la salida objetivo.
2. Observar el Tornado Chart: identificar si "Tarifa promedio" tiene mayor impacto.
3. En el panel izquierdo, aumentar manualmente el precio de los tramos superiores un 5 a 10%.
4. Observar los cambios en las métricas del panel "Recomendación Actual".
5. Revisar la Sensibilidad Cruzada para encontrar el punto óptimo.

---

## 12. Preguntas Frecuentes (FAQ)

**¿El sistema genera la estrategia de precios definitiva que debo aplicar?**

No. El sistema genera una recomendación basada en modelos estadísticos. Los resultados proyectados son estimaciones, no garantías. La decisión final siempre debe tomarse considerando el contexto operativo, acuerdos comerciales y criterio del equipo.

---

**¿Puedo tener más de una ruta en el sistema?**

Sí. Al cargar un CSV con múltiples rutas, el modelo entrena con todas ellas y el selector de rutas muestra todas las disponibles. Los datos demo incluyen solo la ruta `tmco-pcon`.

---

**¿Los datos se pierden si reinicio el servidor?**

No. La base de datos SQLite se persiste en disco. En Docker, el volumen `jac_data` preserva los datos entre reinicios. Solo se pierden datos si se elimina el volumen (`docker compose down -v`) o el archivo `db.sqlite3` manualmente.

---

**¿Puedo tener datos demo y datos reales al mismo tiempo?**

No. Al cargar un CSV, el sistema elimina todos los datos anteriores y los reemplaza con los del CSV.

---

**¿Por qué el sistema siempre pone 10 asientos en el primer tramo?**

Es una regla estructural de inventario: el primer bloque comercial debe tener exactamente 10 asientos. Los bloques siguientes se construyen en múltiplos de 5. Esto garantiza consistencia estructural en las escaleras de precios.

---

**¿Qué significa que la ocupación baje al subir precios?**

Es el efecto de la elasticidad precio-demanda. El modelo usa un factor de elasticidad de -1.2: por cada 1% de aumento en el precio, la demanda cae 1.2%. Si el aumento de precio compensa la caída de demanda en ingreso total, la estrategia sigue siendo rentable.

---

**¿Qué formato deben tener las fechas en el CSV?**

Formato `YYYYMMDD` (8 dígitos, sin guiones). Ejemplo: `20231018` para el 18 de octubre de 2023.

---

**¿Qué sucede si el CSV tiene errores en algunas filas?**

El sistema descarta las filas con errores e inserta las válidas. El campo "Registros Descartados" en Configuración indica cuántas filas fueron omitidas.

---

**¿El sistema funciona sin conexión a internet?**

El backend funciona sin internet. Sin embargo, el frontend carga Bootstrap, React y Plotly desde CDN. Si no hay internet y esas librerías no están en caché del navegador, la interfaz no funcionará correctamente.

---

**¿Puedo usar el sistema desde múltiples equipos simultáneamente?**

Sí, si el sistema está desplegado en un servidor accesible por red. Se recomienda coordinar las cargas de CSV ya que una carga borra los datos anteriores.

---

## 13. Solución de Problemas

### Problema 1: La interfaz no carga (pantalla en blanco o error 404)

**Síntomas:** La página está en blanco o muestra "404 Not Found".

| Causa | Solución |
|---|---|
| Servidor no iniciado | Iniciar uvicorn o `docker compose up` |
| Puerto incorrecto | Local: usar puerto 8002. Docker: usar puerto 8001 |
| `frontend/index.html` no existe | Verificar que el archivo existe en `frontend/` |
| PYTHONPATH no configurado | Incluir `PYTHONPATH=.` al iniciar |

---

### Problema 2: "El modelo no ha sido entrenado" al simular

**Síntomas:** Al hacer clic en "Generar recomendación", aparece mensaje de error.

| Causa | Solución |
|---|---|
| `model.joblib` no existe | Cargar CSV en Configuración para entrenar |
| `DATA_DIR` apunta a directorio sin modelo | Verificar variable `DATA_DIR` |
| Seeder automático falló | Revisar los logs del servidor. Cargar CSV manualmente |

---

### Problema 3: Métricas de modelo muy bajas (R² menor de 0.5)

**Síntomas:** Métricas del modelo en Configuración muestran R² bajo o MAE alto.

| Causa | Solución |
|---|---|
| Pocos datos de entrenamiento | Cargar CSV con más registros históricos |
| Solo hay datos demo | Cargar datos reales de ventas |
| Una sola ruta en los datos | Más rutas y variedad mejoran el modelo |

---

### Problema 4: El CSV no se carga correctamente

**Síntomas:** Mensaje de error al cargar el CSV.

| Causa | Solución |
|---|---|
| Faltan columnas obligatorias | Verificar las seis columnas requeridas |
| Formato de fecha incorrecto | Usar `YYYYMMDD` (8 dígitos sin guiones) |
| Formato de hora incorrecto | Usar `HHMM` (4 dígitos, ej: `0930`) |
| Encoding incorrecto | Guardar el CSV en UTF-8 |

---

### Problema 5: El mapa del bus no muestra asientos coloreados

**Síntomas:** El mapa del bus muestra todos los asientos en color neutro.

| Causa | Solución |
|---|---|
| No se ha generado una recomendación | Hacer clic en "Generar recomendación" |
| Los tramos tienen 0 asientos | Verificar que al menos un tramo tiene asientos mayor de 0 |
| Capacidad del bus mal configurada | Verificar la capacidad en Configuración |

---

### Problema 6: Los gráficos no se muestran

**Síntomas:** Las secciones de gráficos aparecen en blanco tras generar una recomendación.

| Causa | Solución |
|---|---|
| Plotly no cargó desde CDN | Verificar conexión a internet y recargar la página |
| Error de JavaScript | Abrir la consola del navegador (F12) y verificar errores |
| Navegador desactualizado | Usar Chrome, Firefox o Edge en versión actualizada |

---

### Problema 7: Docker no levanta correctamente

**Síntomas:** `docker compose up` falla o el contenedor se detiene.

| Causa | Solución |
|---|---|
| Puerto 8001 en uso | Cambiar el mapeo de puertos en `docker-compose.yml` |
| Docker no tiene permisos | En Linux: `sudo docker compose up` o agregar usuario al grupo `docker` |
| Error en la imagen | Revisar logs: `docker compose logs` |

---

## 14. Buenas Prácticas

### 14.1 Gestión de Datos

- **Actualizar el modelo regularmente:** Cargar datos históricos recientes (al menos mensualmente) para que el modelo refleje patrones actuales.
- **Hacer backup del CSV antes de cargar uno nuevo**, ya que la carga reemplaza los datos anteriores.
- **Verificar la calidad del CSV** antes de cargarlo: fechas correctas, precios razonables, sin filas en blanco masivas.

### 14.2 Uso del Recomendador

- **No usar el recomendador como único criterio:** Complementar con el conocimiento del negocio, eventos especiales, feriados y contexto comercial.
- **Experimentar con la tarifa de referencia:** Si la tarifa es muy diferente al precio de mercado, los resultados serán menos precisos.
- **Respetar la estructura de bloques:** El sistema funciona bien con tramos de 10 asientos (primero) y luego bloques de 5.

### 14.3 Interpretación de Resultados

- **Revisar el R² del modelo:** Un R² bajo (menor de 0.5) indica alta incertidumbre en las proyecciones.
- **Comparar múltiples escenarios:** Generar recomendaciones con distintas tarifas de referencia.
- **No interpretar los resultados como exactos:** Son estimaciones estadísticas. Usar márgenes de error al tomar decisiones.

### 14.4 Mantenimiento del Sistema

- **Hacer backup de `db.sqlite3` y `model.joblib`** periódicamente.
- **Monitorear el espacio en disco:** La base de datos puede crecer con el tiempo.
- **Revisar los logs** periódicamente para detectar errores silenciosos.
- **Ejecutar los tests** después de cualquier actualización del sistema.

---

## 15. Mantenimiento

### 15.1 Backup de Datos

**Base de datos (local):**
```bash
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d)
```

**Base de datos (Docker):**
```bash
docker cp jac_revenue_sandbox:/app/data/db.sqlite3 ./backup/db.sqlite3.backup.$(date +%Y%m%d)
```

**Modelo entrenado (local):**
```bash
cp model.joblib model.joblib.backup.$(date +%Y%m%d)
```

**Modelo entrenado (Docker):**
```bash
docker cp jac_revenue_sandbox:/app/data/model.joblib ./backup/model.joblib.backup.$(date +%Y%m%d)
```

---

### 15.2 Verificación del Estado del Sistema

```bash
curl http://localhost:8001/api/sistema/estado
```

Verificar que `modelo_activo: true` y que `fecha_entrenamiento` es reciente.

---

### 15.3 Monitoreo de Logs

**Local:** Los logs aparecen en la terminal donde corre uvicorn.

**Docker:**
```bash
docker compose logs --tail=100 -f
```

---

### 15.4 Ejecución de Tests

Para verificar el funcionamiento correcto del sistema:

```bash
.venv/bin/pytest -q backend/tests/test_main.py
```

**Resultado esperado:**
```
5 passed, 1 skipped in X.XXs
```

El test marcado como `skipped` corresponde a la carga de CSV (comportamiento de `UploadFile.read()` en el entorno de test).

---

### 15.5 Limpieza de la Base de Datos

La base de datos crece solo si se cargan múltiples CSV. Cada carga reemplaza los datos anteriores, por lo que no debería acumular registros duplicados. Si el archivo `db.sqlite3` crece inesperadamente, verificar que no haya cargas repetidas fallidas.

---

## 16. Actualización del Sistema

### 16.1 Actualización Local

```bash
# 1. Hacer backup de datos
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d)
cp model.joblib model.joblib.backup.$(date +%Y%m%d)

# 2. Detener el servidor
pkill -f "uvicorn backend.app.main:app" || true

# 3. Obtener cambios del repositorio
git fetch origin main
git reset --hard origin/main

# 4. Actualizar dependencias (si hay cambios en requirements.txt)
.venv/bin/pip install -r requirements.txt

# 5. Reiniciar el servidor
PYTHONPATH=. .venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8002
```

---

### 16.2 Actualización con Docker

```bash
# 1. Obtener los cambios
git fetch origin main
git reset --hard origin/main

# 2. Reconstruir y levantar
docker compose down
docker compose up -d --build
```

> **IMPORTANTE:** El volumen `jac_data` se conserva entre actualizaciones. La base de datos y el modelo entrenado NO se pierden al hacer `docker compose down` (sin `-v`).

---

### 16.3 Verificación Post-Actualización

1. Verificar que el servidor inicia correctamente.
2. Abrir la URL del sistema y comprobar que la interfaz carga.
3. Verificar que `GET /api/sistema/estado` responde con `modelo_activo: true`.
4. Ejecutar los tests: `.venv/bin/pytest -q backend/tests/test_main.py`.
5. Generar una recomendación de prueba para verificar el flujo completo.

---

## 17. Desinstalación

### 17.1 Desinstalación Local

```bash
# 1. Detener el servidor
pkill -f "uvicorn backend.app.main:app" || true

# 2. Hacer backup de datos si se desean conservar
cp db.sqlite3 ~/backup_jac_db.sqlite3
cp model.joblib ~/backup_jac_model.joblib

# 3. Desactivar el entorno virtual
deactivate

# 4. Eliminar el directorio del proyecto
cd ..
rm -rf Proyecto-Capstone
```

---

### 17.2 Desinstalación con Docker

```bash
# 1. Detener y eliminar el contenedor y volumen de datos
docker compose down -v

# 2. Eliminar la imagen Docker
docker rmi $(docker images | grep jac | awk '{print $3}')

# 3. Verificar que no quedan volúmenes residuales
docker volume ls | grep jac

# 4. Eliminar el directorio del proyecto
cd ..
rm -rf Proyecto-Capstone
```

> **ADVERTENCIA:** El comando `docker compose down -v` elimina permanentemente todos los datos (base de datos y modelo entrenado). Realizar backup antes de ejecutarlo.

---

## 18. Glosario

| Término | Definición |
|---|---|
| **API** | Interfaz de Programación de Aplicaciones. El conjunto de endpoints HTTP que el backend expone para que el frontend u otros sistemas puedan consumir sus funcionalidades. |
| **Asientos Base** | Asientos del bus que no están asignados a ningún tramo comercial y se venden al precio base de referencia. |
| **Asientos Tarifados** | Asientos del bus asignados a un tramo comercial específico con un precio diferente al base. |
| **Backend** | Componente del sistema que procesa la lógica de negocio, gestiona la base de datos y expone la API. Implementado con FastAPI en Python. |
| **Booking Curve** | Curva de reservas. Gráfico que muestra cómo se acumula la venta de asientos en función de los días previos a la salida del servicio. |
| **Bootstrap** | Librería CSS y JavaScript de diseño de interfaces web, usada en el frontend del sistema. |
| **CLP** | Peso chileno. Moneda usada en todos los cálculos de precio e ingreso del sistema. |
| **CSV** | Comma-Separated Values. Formato de archivo de texto para datos tabulares, usado para cargar el historial de ventas al sistema. |
| **DATA_DIR** | Variable de entorno que define la ruta donde se almacenan la base de datos y el modelo entrenado. |
| **Docker** | Plataforma de contenedores que permite empaquetar el sistema y sus dependencias en un entorno aislado y reproducible. |
| **Docker Compose** | Herramienta para definir y ejecutar múltiples contenedores Docker mediante el archivo `docker-compose.yml`. |
| **Elasticidad precio-demanda** | Medida de cuánto cambia la demanda ante un cambio en el precio. El sistema usa un valor de -1.2, significando que al subir el precio 1%, la demanda cae 1.2%. |
| **Endpoint** | URL específica de la API a la que se envía una solicitud HTTP con un método determinado. |
| **FastAPI** | Framework web de Python de alto rendimiento usado para construir la API del backend del sistema. |
| **Frontend** | La interfaz de usuario web del sistema, implementada como un único archivo HTML con React inline. |
| **Heurística** | Técnica de resolución de problemas que usa reglas prácticas basadas en la experiencia, no en una optimización matemática exacta. La generación de tramos del sistema es heurística. |
| **Ingreso Potencial Total** | El máximo ingreso posible si todos los asientos del bus se vendieran, considerando el precio de cada tramo. |
| **joblib** | Librería Python usada para serializar (guardar y cargar) el modelo de Machine Learning entrenado. |
| **MAE** | Mean Absolute Error, Error Medio Absoluto. Métrica del modelo que indica cuántos asientos se equivoca en promedio. |
| **Machine Learning (ML)** | Rama de la inteligencia artificial donde los modelos aprenden patrones a partir de datos históricos. |
| **modelo_activo** | Campo de la API que indica si hay un modelo de ML entrenado disponible para hacer predicciones. |
| **Numpy** | Librería Python para cálculos numéricos, usada internamente por el backend. |
| **Pandas** | Librería Python para manipulación y análisis de datos tabulares, usada para procesar el CSV. |
| **Plotly** | Librería JavaScript de visualización de datos interactivos, usada en el frontend para los gráficos. |
| **Puerto** | Número que identifica un canal de comunicación de red. El sistema usa el puerto 8001 (Docker) o 8002 (local). |
| **R²** | Coeficiente de determinación. Métrica del modelo entre 0 y 1. Un valor de 0.85 indica que el modelo explica el 85% de la variabilidad de la demanda. |
| **Random Forest** | Algoritmo de Machine Learning que combina múltiples árboles de decisión para hacer predicciones robustas. Es el algoritmo que usa el sistema. |
| **React** | Librería JavaScript para construir interfaces de usuario reactivas, usada en el frontend. |
| **Revenue Management** | Gestión de ingresos. Disciplina de pricing que busca maximizar ingresos vendiendo el inventario correcto al cliente correcto al precio correcto en el momento correcto. |
| **RMSE** | Root Mean Square Error, Raíz del Error Cuadrático Medio. Métrica que penaliza más los errores grandes del modelo. |
| **ruta_encoded** | Valor numérico que representa cada ruta única para ser usada como variable de entrada por el modelo de ML. |
| **scikit-learn** | Librería Python de Machine Learning que implementa el algoritmo Random Forest usado en el sistema. |
| **SeatPlan** | Array de N elementos (donde N es la capacidad del bus) que representa la asignación de tramos a cada asiento. Cada elemento es el identificador del tramo o `null` si es asiento base. |
| **SQLite** | Sistema de base de datos embebido que almacena todos los datos en un único archivo (`db.sqlite3`). No requiere servidor separado. |
| **SQLAlchemy** | ORM (Object-Relational Mapper) Python usado para interactuar con la base de datos SQLite. |
| **Tarifa Base** | Precio de referencia a partir del cual se calculan los precios de los tramos usando multiplicadores. |
| **Tarifa Promedio Ponderada** | Precio promedio considerando todos los asientos del bus, ponderado por la cantidad de asientos en cada tramo. |
| **Tier** | Sinónimo de Tramo Comercial. |
| **Tornado Chart** | Gráfico de barras horizontales usado para comparar el impacto de distintas variables sobre el ingreso. |
| **Tramo Comercial** | Bloque de asientos del bus con un precio específico, parte de una escalera de precios. Sinónimo de Tier. |
| **uvicorn** | Servidor ASGI para Python, usado para servir la aplicación FastAPI. |
| **Yield** | En Revenue Management, el ingreso por asiento vendido. "Proteger el yield" significa preservar el margen por asiento. |

---

*Manual generado a partir del análisis exhaustivo del código fuente, arquitectura y documentación interna del proyecto JAC Revenue Optimizer.*

*Fecha de redacción: Junio 2026.*

