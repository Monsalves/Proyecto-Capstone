# Contexto de Continuidad

## Estado actual del proyecto

Este proyecto ya no está orientado como un sandbox manual de simulación.

La dirección actual es:

- entrenar un modelo con histórico de ventas
- usar ese modelo para estimar demanda por salida
- generar automáticamente una recomendación de tramos comerciales
- pintar esos tramos sugeridos sobre el mapa del bus en frontend

El frontend sigue mostrando el bus con asientos coloreados, pero ahora el flujo principal es:

1. elegir ruta / hora / temporada / tipo de día
2. pedir recomendación
3. recibir tramos sugeridos
4. ver esos tramos aplicados sobre el bus

## Cambio de enfoque ya decidido

Antes:

- el usuario definía manualmente `tramos`
- el sistema simulaba el escenario

Ahora:

- el sistema recomienda los `tramos`
- el frontend los muestra y permite inspeccionarlos

Todavía existe soporte técnico para simulación `v2`, pero el flujo principal ya es recomendación automática.

## Archivos clave

- `backend/app/main.py`
- `backend/tests/test_main.py`
- `frontend/index.html`
- `README.md`
- `MEMORIA_BACKEND.md`

## Backend: estado actual

### Endpoint nuevo principal

Existe este endpoint:

- `POST /api/recomendacion/tramos`

Request:

```json
{
  "ruta": "tmco-pcon",
  "fecha": "2023-10-18",
  "hora": "09:30",
  "capacidad_bus": 45,
  "tarifa_base": 4954
}
```

Respuesta:

- incluye proyección comercial
- incluye `recomendacion`
- incluye `composicion_bus`
- incluye `seat_plan_sugerido`

### Lógica actual de recomendación

La recomendación se construye en `backend/app/main.py`.

Puntos importantes:

- el modelo actual sigue prediciendo ocupación agregada, no tramos reales
- la recomendación todavía es heurística + evaluación de ingreso esperado
- se comparan perfiles con distinta cantidad de tramos
- se elige la alternativa con mejor ingreso esperado

### Regla estructural de inventario ya incorporada

Esto ya está implementado:

- el primer corte comercial debe ser de `10` asientos
- después vienen bloques de `5` asientos
- los tramos sugeridos pueden agrupar varios bloques de `5`, pero no romper esa secuencia base

Ejemplo válido:

- `10`
- `20`
- `15`

porque equivale a:

- `10`
- `5 + 5 + 5 + 5`
- `5 + 5 + 5`

### Importante sobre la heurística actual

La cantidad de tramos ya no es fija.

El sistema puede sugerir entre `2` y `4` tramos según demanda esperada y perfil evaluado.

Pero esto sigue siendo una heurística, no un optimizador entrenado end-to-end.

## Frontend: estado actual

Archivo:

- `frontend/index.html`

### Flujo vigente

- botón principal: `Generar recomendación`
- consume `POST /api/recomendacion/tramos`
- recibe `recomendacion.tramos_sugeridos`
- recibe `recomendacion.seat_plan_sugerido`
- actualiza `pricingTiers`
- actualiza `seatPlan`
- pinta los asientos con los colores de los tramos sugeridos

### Ajustes ya hechos

- se cambió branding de `Sandbox` a `Optimizer`
- se eliminó el uso de optional chaining en el script inline porque `babel-standalone` fallaba
- el panel de tramos ahora representa principalmente tramos sugeridos, aunque todavía permite edición manual

## Tests

Archivo:

- `backend/tests/test_main.py`

Estado al cierre de esta sesión:

- `5 passed`
- `1 skipped`

Se validó:

- estado del sistema
- actualización de configuración
- simulación `v2`
- recomendación automática de tramos

La prueba de CSV sigue en `skip` por comportamiento del entorno con `UploadFile.read()`.

## Decisiones ya tomadas

- el producto debe evolucionar desde sandbox a recomendador comercial
- el frontend debe seguir mostrando el bus pintado
- la cantidad de tramos debe poder variar
- la estructura comercial base debe respetar:
  - primer tramo de `10`
  - luego tramos construidos sobre bloques de `5`

## Limitaciones actuales

### Modelo

El modelo actual:

- predice ocupación agregada
- usa tarifa promedio como feature
- no aprende realmente escalones comerciales ni elasticidad por tramo

Eso implica que la recomendación actual es una aproximación útil, pero no una optimización “verdadera” aprendida desde datos detallados por tramo.

### Frontend

Todo el frontend sigue en un único `index.html` con React inline.

Eso vuelve más lenta la iteración y hace más frágiles cambios grandes de UI.

### Backend

`backend/app/main.py` concentra demasiadas cosas:

- modelos DB
- API
- entrenamiento
- seeding demo
- recomendación
- simulación

Si el proyecto sigue creciendo, conviene separar:

- lógica ML
- lógica de pricing/recomendación
- endpoints
- persistencia

## Ideas de siguiente iteración

Opciones razonables para la próxima sesión:

1. mejorar la lógica que decide cuántos tramos convienen
2. hacer que los precios sugeridos dependan más explícitamente de estacionalidad, hora y demanda
3. mostrar mejor en frontend por qué se eligió esa recomendación
4. guardar recomendaciones generadas para compararlas entre salidas
5. reemplazar heurísticas por una optimización más formal
6. reestructurar backend para separar recomendación y simulación

## Si la próxima sesión parte desde cero

Prompt sugerido:

> Revisa `CONTEXTO_PROXIMA_SESION.md`, `backend/app/main.py`, `backend/tests/test_main.py` y `frontend/index.html`. Este proyecto ya no es un sandbox manual: ahora genera recomendaciones automáticas de tramos para una salida de bus, manteniendo el bus pintado en frontend. Quiero seguir iterando sobre la lógica del recomendador.

## Estado operativo al cierre

- no deben quedar procesos activos de la app en `8002`, `8010` ni `8022`
- la última validación funcional mostró que el recomendador ya puede devolver algo como `10 + 20 + 15`
- no se dejó la app corriendo
