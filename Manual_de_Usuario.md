# Manual de Usuario — JAC Revenue Optimizer

> **Proyecto:** JAC Revenue Optimizer · **Versión:** 1.0 · **Fecha:** Junio 2026

---

## Tabla de Contenido

1. [Introducción](#1-introducción)
2. [Requisitos del Sistema](#2-requisitos-del-sistema)
3. [Instalación e Implementación](#3-instalación-e-implementación)
4. [Configuración](#4-configuración)
5. [Primer Inicio del Sistema](#5-primer-inicio-del-sistema)
6. [Navegación por la Interfaz](#6-navegación-por-la-interfaz)
7. [Funcionalidades del Sistema](#7-funcionalidades-del-sistema)
8. [Explicación de Gráficos, Indicadores y Métricas](#8-explicación-de-gráficos-indicadores-y-métricas)
9. [Flujo Completo de Uso](#9-flujo-completo-de-uso)
10. [Solución de Problemas](#10-solución-de-problemas)

---

## 1. Introducción

**JAC Revenue Optimizer** es una aplicación web de optimización de precios para operadores de buses. Combina un motor de Machine Learning con una interfaz visual que permite gestionar la estrategia de precios de cada salida de forma automática y basada en datos históricos reales.

El sistema permite definir **tramos comerciales** (bloques de asientos con distintos precios), lo que en la industria se conoce como *Revenue Management*: vender el inventario correcto al precio correcto en el momento correcto para maximizar ingresos.

### ¿Qué resuelve?

En la gestión tradicional de buses los precios son fijos, lo que genera dos problemas:
- **Subutilización de la capacidad:** pasajeros que pagarían menos no compran porque el precio único es alto.
- **Pérdida de margen:** pasajeros dispuestos a pagar más compran al precio mínimo disponible.

El sistema sugiere automáticamente una escalera de precios por tramos según la demanda histórica de cada ruta/hora/temporada.

### Beneficios principales

| Beneficio | Descripción |
|---|---|
| Mayor ingreso por salida | Captura pasajeros en distintas bandas de precio |
| Recomendaciones automáticas | Propuesta de tramos en segundos |
| Basado en datos reales | El modelo aprende del historial de ventas propio |
| Visualización intuitiva | Bus coloreado por tramos, gráficos de proyección |

---

## 2. Requisitos del Sistema

### Software

| Componente | Versión | Notas |
|---|---|---|
| Python | 3.11 o superior | Solo para ejecución local |
| Docker Engine | 24.x o superior | Recomendado para producción |
| Docker Compose | 2.x o superior | Incluido en Docker Desktop |
| Navegador | Chrome / Firefox / Edge | Con JavaScript habilitado |

### Dependencias Python (instaladas automáticamente con `pip`)

| Librería | Uso |
|---|---|
| `fastapi` + `uvicorn` | Servidor y API |
| `sqlalchemy` | Base de datos |
| `pandas` + `numpy` | Procesamiento de datos CSV |
| `scikit-learn` + `joblib` | Modelo de Machine Learning |
| `python-multipart` | Carga de archivos CSV |

### Hardware mínimo

| Recurso | Mínimo |
|---|---|
| CPU | 2 núcleos |
| RAM | 2 GB libres |
| Disco | 500 MB libres |

### Red

- Puerto **8001** (Docker) o **8002** (local) deben estar disponibles.
- El frontend carga Bootstrap, React y Plotly desde internet (CDN); se requiere conexión al primer acceso.

---

## 3. Instalación e Implementación

### Opción A — Docker (recomendado para producción)

```bash
# 1. Clonar el repositorio
git clone https://github.com/<organización>/Proyecto-Capstone.git
cd Proyecto-Capstone

# 2. Construir y levantar
docker compose up -d --build
```

**Acceso:** http://localhost:8001

Para detener el sistema (sin perder datos):
```bash
docker compose down
```

> **ADVERTENCIA:** `docker compose down -v` elimina todos los datos de forma permanente.

---

### Opción B — Ejecución local

```bash
# 1. Clonar el repositorio
git clone https://github.com/<organización>/Proyecto-Capstone.git
cd Proyecto-Capstone

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Iniciar el servidor
# Linux / macOS:
PYTHONPATH=. python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8002

# Windows (PowerShell):
$env:PYTHONPATH = "."; python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8002
```

**Acceso:** http://127.0.0.1:8002

---

### Despliegue en producción (Azure VM + CI/CD)

El proyecto incluye GitHub Actions (`.github/workflows/deploy.yml`). Cada `push` a `main` ejecuta los tests y, si pasan, despliega automáticamente en la VM vía SSH.

**Secrets requeridos en GitHub:**

| Secret | Descripción |
|---|---|
| `AZURE_VM_HOST` | IP o hostname de la VM |
| `AZURE_VM_USER` | Usuario SSH |
| `AZURE_VM_KEY` | Clave privada SSH (formato PEM) |

---

## 4. Configuración

### Variables de entorno

| Variable | Por defecto | Descripción |
|---|---|---|
| `DATA_DIR` | `.` | Ruta donde se guardan `db.sqlite3` y `model.joblib` |
| `TZ` | — | Zona horaria. Docker Compose lo fija en `America/Santiago` |

### Parámetros del sistema (editables desde la interfaz)

| Parámetro | Por defecto | Rango | Descripción |
|---|---|---|---|
| `capacidad_bus` | 45 | 1 – 100 | Asientos totales del bus. Afecta el mapa y todos los cálculos |
| `nombre_empresa` | "Buses JAC" | — | Nombre que aparece en el encabezado |

### Puertos

| Modo | Puerto | URL |
|---|---|---|
| Local | 8002 | http://127.0.0.1:8002 |
| Docker | 8001 | http://localhost:8001 |

### Base de datos

El sistema usa **SQLite** (`db.sqlite3`), creado automáticamente al arrancar. No requiere configuración adicional. En Docker se persiste en el volumen `jac_data`.

### Modelo de Machine Learning

| Parámetro | Valor |
|---|---|
| Algoritmo | Random Forest Regressor (30 árboles) |
| Variable objetivo | Asientos vendidos por salida |
| Variables de entrada | Ruta, día semana, fin de semana, mes, hora, tarifa promedio |
| Elasticidad precio | -1.2 (1% de aumento en precio → -1.2% de demanda) |

---

## 5. Primer Inicio del Sistema

Al arrancar por primera vez con la base de datos vacía, el sistema **genera automáticamente** datos demo para la ruta `tmco-pcon` (Temuco → Puerto Montt) y entrena el modelo. Este proceso puede tardar entre 5 y 30 segundos.

**Señales de inicio correcto en la terminal:**
```
INFO:  Application startup complete.
INFO:  Uvicorn running on http://127.0.0.1:8002
```

**En el navegador**, si el inicio fue exitoso:
- El encabezado muestra el nombre de la empresa y "Revenue Optimizer".
- Se ven los selectores de ruta, hora, temporada y tipo de día.
- El panel "Recomendación Actual" muestra métricas de asientos y tarifa.

Si en cambio aparece la pantalla **"Cargue datos históricos para entrenar el motor..."**, el modelo no está activo. En ese caso, ir a **Configuración** y cargar el archivo CSV.

---

## 6. Navegación por la Interfaz

### Encabezado

Contiene el nombre de la empresa y dos botones:
- **Dashboard Sandbox** → Vista principal de recomendaciones (activo por defecto).
- **Configuración** → Gestión del sistema y carga de CSV.

---

### Vista principal — Dashboard Sandbox

**Barra superior: Salida a Recomendar**

| Campo | Descripción |
|---|---|
| Ruta | Origen y destino del servicio |
| Hora del Servicio | Horario de salida |
| Temporada | Media / Verano / Invierno |
| Tipo de Día | Semana / Fin de semana |

Las combinaciones de Temporada y Tipo de Día se mapean internamente a fechas concretas del dataset histórico.

**Panel izquierdo — Tramos Sugeridos**

- Campo **Tarifa de referencia**: precio base para calcular los multiplicadores de cada tramo.
- Lista de tramos con nombre, asientos y precio por tramo.
- Botón **Añadir tramo manual**: agrega un tramo nuevo.
- Botón **↺**: reinicia todos los tramos y el mapa del bus.

**Panel derecho — Mapa del Bus + Recomendación Actual**

- Representación visual del bus con asientos coloreados por tramo.
- Métricas instantáneas: asientos tarifados, tarifa promedio, asientos base.
- Estrategia elegida y justificación (tras generar una recomendación).
- Botón **Simular tramos**: proyecta los tramos definidos manualmente.
- Botón **Generar recomendación**: solicita una propuesta automática al motor de IA.

**Sección de resultados** (aparece tras generar o simular):
- KPI de Ingreso Proyectado vs. base.
- KPI de Ocupación Proyectada con gráfico donut.
- Cuatro gráficos de análisis.

---

### Vista de Configuración

- **Formulario**: editar capacidad del bus y nombre de empresa.
- **Estado del Modelo**: fecha de entrenamiento, registros procesados, MAE, RMSE, R².
- **Área de carga CSV**: subir un nuevo archivo para reentrenar el modelo.

---

## 7. Funcionalidades del Sistema

### 7.1 Generar Recomendación Automática

El motor de IA estima la demanda de la salida seleccionada y propone entre 2 y 4 tramos con precios que maximizan el ingreso.

**Reglas estructurales:**
- El primer tramo siempre tiene **10 asientos**.
- Los siguientes se construyen en bloques de **5 asientos**.

**Estrategias según demanda estimada:**

| Ocupación estimada | Estrategia | Tramos | Precios |
|---|---|---|---|
| < 35% | Estimular demanda | 2 – 3 | 82% – 108% de la tarifa base |
| 35% – 70% | Balancear volumen y yield | 2 – 4 | 90% – 118% |
| > 70% | Proteger yield | 3 – 4 | 95% – 134% |

**Cómo usarlo:**
1. Seleccionar Ruta, Hora, Temporada y Tipo de Día.
2. Ingresar la Tarifa de referencia.
3. Clic en **"Generar recomendación"**.

> El modelo **sobreescribe** los tramos actuales con la nueva propuesta.

---

### 7.2 Simular Tramos Propios

Permite proyectar el ingreso y la ocupación de una estructura de tramos que el usuario construyó manualmente, **sin modificar los tramos actuales**.

**Cómo usarlo:**
1. Agregar tramos en el panel izquierdo con "Añadir tramo manual" o editando los existentes.
2. Clic en **"Simular tramos"**.
3. Los gráficos y KPIs se actualizan con la proyección de la configuración actual.

---

### 7.3 Editar Tramos Manualmente

En el panel izquierdo se puede modificar cualquier tramo en tiempo real:

| Acción | Cómo |
|---|---|
| Renombrar tramo | Clic en el campo de nombre |
| Cambiar asientos | Editar el campo "Asientos" (el mapa se redistribuye automáticamente) |
| Cambiar precio | Editar el campo "Precio CLP" |
| Eliminar tramo | Clic en el ícono 🗑️ |
| Agregar tramo | Clic en "Añadir tramo manual" |
| Reiniciar todo | Clic en el botón ↺ |

---

### 7.4 Cargar Datos Históricos (CSV)

Al cargar un CSV el sistema reemplaza los datos anteriores, reconstruye las salidas agregadas y reentrena el modelo.

**Columnas obligatorias del CSV:**

| Columna | Formato | Ejemplo |
|---|---|---|
| `NRO_BOLETO` | Entero | `12345` |
| `VALOR` | Entero (CLP) | `4500` |
| `ORIGEN_DESTINO` | Texto | `tmco-pcon` |
| `FECHA_SALIDA_SERVICIO` | `YYYYMMDD` | `20231018` |
| `HORA_SALIDA_SERVICIO` | `HHMM` | `0930` |
| `FECHA_COMPRA` | `YYYYMMDD` | `20231010` |

**Cómo usarlo:** Ir a **Configuración** → área de carga de archivos → seleccionar el CSV → esperar confirmación.

> El archivo de ejemplo `OCTUBRE23_ANON.csv` en la raíz del proyecto sirve como referencia de formato.

---

### 7.5 Configurar el Sistema

Desde **Configuración → Configuración del Sistema**:
- Editar la capacidad del bus y el nombre de la empresa.
- Clic en **"Guardar Configuración"**.

> Cambiar la capacidad del bus afecta el mapa visual y todos los cálculos. Volver a generar la recomendación tras el cambio.

---

### 7.6 Consultar el Estado del Modelo

Desde **Configuración → Estado del Modelo Activo** se visualizan:

| Métrica | Valor ideal | Significado |
|---|---|---|
| MAE | < 3 asientos | Error promedio del modelo |
| RMSE | < 4 asientos | Penaliza errores grandes |
| R² | > 0.7 | Porcentaje de variabilidad explicada |

---

## 8. Explicación de Gráficos, Indicadores y Métricas

### KPI — Ingreso Total Proyectado

El ingreso esperado en CLP si la salida se vende según la ocupación estimada con la estructura de tramos actual.

```
Ingreso Proyectado = Ingreso Potencial Total × (Ocupación Proyectada / Capacidad)
```

El badge de variación (▲ / ▼ %) compara contra el escenario histórico base (sin tramos).

---

### KPI — Ocupación Proyectada

Porcentaje de asientos que el modelo estima que se venderán.

**Gráfico donut:**
- 🟢 Verde: ≥ 80% de ocupación.
- 🟡 Ámbar: 50% – 79%.
- 🔴 Rojo: < 50%.

El badge muestra la diferencia en puntos porcentuales (pp) respecto al base.

---

### Gráfico 1 — Comparativa de Ingresos (Base vs Simulado)

**Tipo:** Barras agrupadas.

| Serie | Color | Descripción |
|---|---|---|
| Histórico Base | Gris | Ingreso estimado sin tramos (precio histórico × ocupación base) |
| Escenario Simulado | Rojo | Ingreso proyectado con la estructura de tramos actual |

**Cómo interpretar:** Si la barra roja supera a la gris, la estrategia de tramos mejora el ingreso respecto al histórico.

---

### Gráfico 2 — Booking Curve (Ritmo de Venta)

**Tipo:** Líneas con área.

- **Eje X:** Días de anticipación (de -30 a 0, donde 0 = día de la salida).
- **Eje Y:** Asientos vendidos acumulados.

| Serie | Descripción |
|---|---|
| Histórico Promedio (gris) | Promedio de ventas acumuladas antes de la salida en el pasado |
| Proyección Escenario (rojo punteado) | Proyección escalada según la ocupación estimada |
| Capacidad (negro punteado) | Límite de asientos del bus |

**Cómo interpretar:** Una curva que sube bruscamente cerca del día 0 indica ventas de última hora. Una subida gradual indica compras anticipadas.

---

### Gráfico 3 — Análisis de Sensibilidad (Tornado Chart)

**Tipo:** Barras horizontales.

- **Eje X:** Variación del ingreso en CLP (positivo o negativo respecto al escenario actual).
- **Eje Y:** Variables analizadas (tarifa promedio y asientos base).

| Serie | Descripción |
|---|---|
| Verde (+10%) | Impacto de subir esa variable un 10% |
| Rojo (-10%) | Impacto de bajarla un 10% |

**Cómo interpretar:** Las barras más largas son las palancas con mayor impacto. Si "Tarifa promedio" domina, el precio es la variable clave. Si "Asientos base" domina, la composición del bus es más determinante.

---

### Gráfico 4 — Sensibilidad Cruzada (Precio vs Asientos Base)

**Tipo:** Líneas con marcadores.

- **Eje X:** Cantidad de asientos base (variaciones: -5, 0, +5, +10 respecto al actual).
- **Eje Y:** Ingreso total proyectado en CLP.
- **4 líneas:** Cada una representa un nivel de ajuste de precio (-5%, 0%, +5%, +10%).

**Cómo interpretar:** El punto óptimo es la combinación de precio y asientos base donde la línea más alta alcanza su máximo valor. Si las líneas descienden de izquierda a derecha, reducir asientos base (aumentar tarifados) mejora el ingreso.

---

### Panel "Recomendación Actual" — Métricas instantáneas

Calculadas en tiempo real con cada cambio en los tramos:

| Métrica | Fórmula |
|---|---|
| Asientos tarifados | Suma de asientos asignados a tramos |
| Tarifa promedio | `(Σ asientos_tramo × precio_tramo + asientos_base × tarifa_base) / capacidad` |
| Asientos base | `capacidad - asientos_tarifados` |

---

## 9. Flujo Completo de Uso

A continuación, el flujo típico de un analista que obtiene y evalúa una recomendación de precios.

**Paso 1 — Acceder al sistema**
Abrir el navegador en la URL del sistema y verificar que el encabezado muestra el nombre de la empresa.

**Paso 2 — Verificar el modelo activo**
Confirmar que se muestra el Dashboard principal (no la pantalla de carga de CSV). Opcionalmente, ir a Configuración y revisar que "Fecha de Último Entrenamiento" tiene una fecha válida.

**Paso 3 — Seleccionar la salida**
En la barra superior elegir Ruta, Hora del Servicio, Temporada y Tipo de Día.

**Paso 4 — Establecer la tarifa de referencia**
En el panel izquierdo, ingresar el precio base de mercado actual de esa ruta.

**Paso 5 — Generar la recomendación**
Clic en **"Generar recomendación"**. Esperar 2 a 5 segundos.

**Paso 6 — Revisar los tramos sugeridos**
- Ver en el panel izquierdo los tramos propuestos (nombre, asientos, precio).
- Ver el mapa del bus coloreado por tramo.
- Leer la estrategia elegida y su justificación.

**Paso 7 — Analizar los resultados**
- **Ingreso proyectado** y su variación vs. base.
- **Ocupación proyectada** con el gráfico donut.
- **Gráfico comparativo** para confirmar que supera al histórico.
- **Booking Curve** para entender el ritmo de venta esperado.
- **Tornado Chart** para identificar la palanca de mayor impacto.
- **Sensibilidad Cruzada** para evaluar combinaciones de precio/composición.

**Paso 8 — Ajustar si es necesario**
- Modificar manualmente el precio o los asientos de algún tramo.
- Clic en **"Simular tramos"** para ver la proyección de la configuración ajustada.
- Si se quiere otra propuesta del sistema, clic en **"Generar recomendación"** nuevamente.

**Paso 9 — Documentar la decisión**
Registrar la estructura de tramos aprobada (nombre, asientos, precio) para implementarla en el sistema de venta de boletos.

---

## 10. Solución de Problemas

### La interfaz no carga (pantalla en blanco o error 404)

| Causa | Solución |
|---|---|
| Servidor no iniciado | Ejecutar `docker compose up` o el comando uvicorn |
| Puerto incorrecto | Local: 8002. Docker: 8001 |
| JavaScript deshabilitado | Habilitarlo en la configuración del navegador |
| `frontend/index.html` no existe | Verificar que el archivo está en la carpeta `frontend/` |

---

### "El modelo no ha sido entrenado" al generar recomendación

| Causa | Solución |
|---|---|
| No hay `model.joblib` | Ir a Configuración y cargar el CSV para entrenar |
| `DATA_DIR` apunta a directorio incorrecto | Verificar la variable de entorno |

---

### Error al cargar el CSV

| Causa | Solución |
|---|---|
| Faltan columnas obligatorias | Verificar las 6 columnas requeridas |
| Formato de fecha incorrecto | Usar `YYYYMMDD` sin guiones (ej: `20231018`) |
| Formato de hora incorrecto | Usar `HHMM` sin dos puntos (ej: `0930`) |
| Encoding incorrecto | Guardar el CSV en UTF-8 |

---

### Los gráficos no se muestran tras generar la recomendación

| Causa | Solución |
|---|---|
| Plotly no cargó desde CDN | Verificar conexión a internet y recargar la página |
| Error de JavaScript | Abrir la consola del navegador (F12) y revisar errores |

---

### Docker no levanta el contenedor

| Causa | Solución |
|---|---|
| Docker no está corriendo | Iniciar Docker Desktop |
| Puerto 8001 en uso | Cambiar el mapeo en `docker-compose.yml`: `"8080:8001"` |
| Error de imagen | Ejecutar `docker compose logs` para ver el detalle |

---

### Métricas del modelo muy bajas (R² < 0.5)

| Causa | Solución |
|---|---|
| Pocos datos de entrenamiento | Cargar CSV con más períodos históricos |
| Solo hay datos demo | Cargar datos reales de ventas |
| Alta variabilidad en los datos | Normal en transporte; más datos mejoran el modelo |

---

*Manual generado a partir del análisis exhaustivo del código fuente y la arquitectura del proyecto JAC Revenue Optimizer. Junio 2026.*
