# Memoria de Traspaso: Estado Actual y Siguiente Etapa Backend

## Contexto

Este proyecto originalmente era un sandbox de revenue management con:

- FastAPI backend
- frontend estático en `frontend/index.html`
- simulación basada en:
  - tarifa promedio
  - cupos de protección
  - modelo ML de ocupación

En esta etapa se rehízo el **frontend** para cambiar el enfoque desde sliders simples a una lógica visual basada en:

- tarifa base
- tramos comerciales
- asignación automática de asientos por tramo
- visualización de bus/asientos

La idea ahora es continuar con un chat limpio para rehacer el **backend** y alinearlo con esta nueva UI.

---

## Estado actual del frontend

Archivo principal:

- `frontend/index.html`

### Flujo actual

1. El usuario selecciona:
   - ruta
   - hora
   - temporada
   - tipo de día

2. Define una `tarifa base` manual.

3. Puede agregar múltiples `tramos`.

4. Cada tramo tiene:
   - nombre editable
   - cantidad de asientos
   - precio CLP

5. Los asientos del bus se asignan automáticamente:
   - los primeros asientos disponibles se pintan según los tramos
   - los no asignados quedan como `Base`

6. El bus se muestra horizontalmente, con cada columna como:
   - 2 asientos
   - pasillo interno
   - 2 asientos

7. El bloque `Escenario Actual` muestra:
   - asientos tarifados
   - tarifa promedio
   - asientos libres

8. El botón principal es:
   - `Simular escenario`

---

## Decisiones de UI ya tomadas

### Estructura general

- La barra `Salida a Simular` va arriba, full width.
- El contenido principal se divide en:
  - izquierda: `Tramos Comerciales`
  - derecha: `Mapa del Bus` + `Escenario Actual`
- Los resultados de simulación aparecen debajo, en ancho completo.

### Tramos

- No existen tramos al inicio.
- Se agrega un tramo con botón `Añadir tramo`.
- El nombre del tramo es editable.
- Si se elimina un tramo, los otros **no se renombran**.
- Los colores de tramos nuevos intentan no repetirse mientras haya colores disponibles.
- El botón `Añadir tramo` quedó debajo del último tramo.

### Scroll del panel de tramos

- El panel de tramos debe crecer de forma natural al principio.
- Cuando llega a la altura del bloque derecho superior, debe activar scroll interno.
- Hay una implementación inicial para esto usando medición del bloque derecho.

### Bus

- Se eliminó por completo el concepto de `asiento protegido` en el frontend.
- En el bus:
  - asiento con color = tramo
  - asiento sin color = base

### Acciones eliminadas por decisión de UX

Ya no deben volver salvo que se decida explícitamente:

- `Reasignar asientos`
- `Reiniciar distribución`
- `Limpiar bus` dentro de `Escenario Actual`

---

## Problema actual del backend

El backend **todavía no representa fielmente la nueva lógica del frontend**.

Hoy la simulación real sigue resumida a:

- `tarifa`
- `cupos_proteccion`

Y el frontend, al simular, termina enviando una versión simplificada:

- una tarifa derivada (`simulationFare`)
- `cupos_proteccion: 0`

Eso significa que:

- el backend **no sabe realmente qué asientos están en qué tramo**
- no sabe cuántos asientos quedaron en `Base`
- no distingue entre múltiples niveles de precio
- no modela una estructura completa de inventario por asiento o por bloque

---

## Objetivo de la siguiente etapa

Rehacer la simulación backend para que use la estructura nueva del frontend.

### Idea funcional deseada

Regla propuesta:

- asiento con tramo asignado => se vende al precio del tramo
- asiento sin tramo => se vende a tarifa base
- ya no usar `cupos_proteccion`

### Lo que debería enviar el frontend idealmente

En vez de mandar sólo una tarifa promedio, debería mandar algo como:

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
    },
    {
      "id": "tier-3",
      "name": "Tramo alto",
      "targetSeats": 5,
      "price": 6200,
      "color": "#8b5cf6"
    }
  ],
  "seatPlan": [
    "tier-1", "tier-1", "tier-1", "...", null, null
  ]
}
```

Donde:

- `null` en `seatPlan` = asiento base
- string con id = asiento asignado a un tramo

---

## Recomendación técnica para el backend

### Etapa 1: dejar de depender de `cupos_proteccion`

Modificar el endpoint de simulación para aceptar una estructura nueva, separada del modelo viejo.

Sugerencia:

- mantener el endpoint viejo temporalmente si hace falta
- crear un endpoint nuevo, por ejemplo:

`POST /api/simulacion/proyectar-v2`

### Etapa 2: construir métricas reales desde la composición del bus

Calcular al menos:

- cantidad de asientos por tramo
- cantidad de asientos base
- ingreso potencial por tramo
- ingreso potencial base
- tarifa promedio ponderada real

### Etapa 3: usar esa composición para alimentar la lógica de ocupación / ingreso

Opciones:

1. Solución rápida:
   - usar la mezcla de precios para construir una tarifa efectiva ponderada
   - seguir ocupando el modelo actual como aproximación

2. Solución mejor:
   - modelar demanda por bloques/tramos
   - estimar conversión distinta por nivel de precio

Para avanzar rápido, la opción 1 es suficiente como puente.

---

## Archivos clave para la próxima conversación

- `frontend/index.html`
- `backend/app/main.py`
- `backend/tests/test_main.py`

---

## Siguiente tarea sugerida en chat nuevo

Prompt sugerido:

> Quiero adaptar el backend a la nueva UI. Revisa `MEMORIA_BACKEND.md`, `frontend/index.html` y `backend/app/main.py`. Necesito que el backend deje de usar `cupos_proteccion` y acepte una simulación basada en `tarifa_base`, `tramos` y `seatPlan`.

