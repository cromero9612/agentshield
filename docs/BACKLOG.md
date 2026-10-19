# Backlog por día y por persona (v2, alcance unificado)

Entrega: **jueves 22** (el viernes 23 es colchón). Cierre oficial: 23 de octubre, 11:59 PM PDT = 12:59 AM del sábado 24 en Guatemala.
Reemplaza al backlog original (conservado en [legacy/BACKLOG-v0.md](legacy/BACKLOG-v0.md)) tras adoptar [integracion.md](integracion.md).
Las etapas **U-01 a U-08** están definidas en integracion.md §13; aquí se reparten por día. Las prioridades P0/P1 vienen de [analisis.md](analisis.md) §17.

> `scripts/crear_issues.sh` lee las tablas de este archivo. **No lo vuelvas a correr sobre el repo actual:** crearía
> duplicados de los 28 issues del backlog original. Los issues nuevos se crean a mano o con un filtro.

## Dom 18 · U-01 contratos y U-02 smoke real

| Persona | Tarea |
|---|---|
| A | U-01: revisar y aprobar el alcance unificado, los contratos v2 y este backlog con B, C y D |
| A | Correcciones de seguridad del guard: valores inválidos, fallo del Decider, cancelación siempre con aprobación, carga de `.env` (G-01/02/03/04/09) |
| B | U-02: smoke de Bedrock con un modelo disponible en la cuenta y el hook de Strands (una traza real) |
| C | Consola presentable: recorrido de decisión, medidores y modo sombra (PR de la consola) |
| D | U-02: cuota de GPU y despliegue del Decider; mientras tanto, Decider local para medir |
| Todos | Leer integracion.md y marcar en el PR lo que no se entienda o no se esté de acuerdo |

## Lun 19 · U-03 dominio de pedidos y U-04 política

| Persona | Tarea |
|---|---|
| B | U-03: seed de 10 pedidos (ORD-1001 a ORD-1010), máquina de estados, tres herramientas y backend mock detrás de un puerto |
| A | U-04: política única de pedidos; entradas inválidas, GUIDE sin pasar a CONFIRM y caídas del Decider terminan sin mutación |
| C | Eventos de auditoría v2 en la consola: fuente, modo del Decider, backend y efecto |
| D | Corpus del benchmark en el esquema `unified-1` (al menos 16 casos etiquetados) y ajuste del runner |
| Todos | Dos casos nuevos cada uno, en módulos que no hicieron |

## Mar 20 · U-05 ejecución y aprobación, U-06 REST de lectura

| Persona | Tarea |
|---|---|
| B | U-05: ejecutor autorizado, persistencia SQLite y aprobaciones vinculadas a la operación (consumo único, vencimiento, revalidación) |
| A | U-05: contexto confiable y permisos por rol (viewer, operator, approver) en el guard |
| B | U-06: adaptador REST de solo lectura (GET) a una API de staging, con destino administrado y sin escrituras |
| D | U-06: API de staging independiente de los fixtures; pruebas de aislamiento y de `dry_run` (cero HTTP de escritura) |
| C | Consola conectada al flujo real: agente, aprobación y efecto antes/después |

## Mié 21 · U-07 evaluación y U-08 patrón, video y artículo

| Persona | Tarea |
|---|---|
| D | U-07: evaluación honesta con el Decider real (aciertos, latencia, falsos bloqueos) y evidencia E2E en AWS |
| A | U-08: patrón reutilizable en `patterns/grounded_tool_call_guard/` con README y ejemplo; borrador del artículo con métricas reales |
| C | U-08: grabar el video (guion único en integracion.md §14.2) |
| B | U-08: ensayo completo de la demo y lista de comandos |
| D | Calibrar el umbral con un conjunto de calibración separado del de evaluación |

## Jue 22 · Entrega

| Persona | Tarea |
|---|---|
| A | Publicar el artículo con los tags `#strands-decider-2b` y `#guardrails`; enviar el proyecto |
| C | Editar y subir el video público (menos de 3:00) con subtítulos en inglés |
| D | Verificar repo público, licencia, README y CI en verde en Linux y Windows; apagar recursos de AWS |
| B | Probar todos los links en una ventana privada; checklist final |

## Orden de recorte (si falta tiempo)

Se recorta de abajo hacia arriba y se conserva el guard real, las tres herramientas en mock, la aprobación, el GET de
staging, AWS y los entregables: UI avanzada, comparador de LLM, gráficas, escrituras REST, IaC sofisticada.
Si no se logra el GET de staging, se declara alcance reducido; **nunca se etiqueta un fixture como integración real.**
