# Cómo trabajamos los 4

## Dónde vemos todo

Todo vive en **GitHub**. Cada uno solo necesita una cuenta gratuita de GitHub.

- **Código y documentos**: este repo. Si alguien escribe algo, lo sube aquí y todos lo ven.
- **Tareas**: Issues del repo, una por tarea, con su responsable y el día (milestone).
- **Tablero**: GitHub Projects (vista Kanban: Por hacer, En curso, En revisión, Hecho).
- **Avisos rápidos**: el grupo de chat del equipo. Lo que se decide en el chat se anota en el issue.

## Roles

| Persona | Rol | Es dueño de | Ayuda en |
|---|---|---|---|
| A · Carlos | Líder + Guard | `agentshield/` (preguntas, combine, umbral, patrón) | Artículo (dueño) |
| B | Agente y tienda | `agent/`, `store/`, integración con Bedrock, flujo de Confirm | Video |
| C | Consola y auditoría | `console/`, `audit.py`, DynamoDB, modo sombra | Video (dueño de la grabación) |
| D | AWS y benchmark | Cuenta AWS, IAM, presupuesto, EC2 del Decider, despliegue, `bench/`, CI | Artículo (resultados) |

Todos escriben casos de prueba en `bench/cases.jsonl`, pero **cada quien escribe ataques para módulos que no hizo**.

## Contratos entre módulos (no se cambian sin avisar)

Estos contratos permiten trabajar en paralelo sin pisarse.

> **Desde el 18-oct rigen los contratos v2** (sección *Contratos v2*, más abajo). Los bloques de código de esta
> sección describen la versión original (v0); lo que no se menciona como cambiado en v2 sigue igual.

```python
# 1. Lo que devuelve el Decider (agentshield/combine.py)
GuardAnswers(grounded: float, intent: float, injected: float, blast: float, latency_ms: float | None)

# 2. El veredicto (agentshield/combine.py)
Verdict(action: "proceed" | "guide" | "confirm" | "deny", reason: str, hint: str, checks: dict)

# 3. La API del guard (agentshield/guard.py)
Shield.evaluate(user_request, tool_name, tool_input, tool_outputs) -> Verdict

# 4. El evento que recibe la consola (agentshield/audit.py → SSE)
{"decision_id", "ts", "mode", "tool", "args", "hard", "answers", "latency_ms", "verdict", "reason"}

# 5. Un caso del benchmark (bench/cases.jsonl, una línea JSON)
{"id", "kind", "user_request", "tool", "args", "tool_outputs", "expected"}
```

### Contratos v2 (`unified-1`): adoptados el 18-oct según [integracion.md](integracion.md)

El alcance de la entrega pasa a **operaciones seguras sobre pedidos** (3 herramientas). Los contratos evolucionan con
compatibilidad: lo marcado "sin cambio" no se toca, y lo nuevo es **aditivo** mientras no se indique lo contrario.

| Contrato | Cambio |
|---|---|
| 1. `GuardAnswers` | **Sin cambio de campos.** El cliente del Decider valida finitud y rangos; un valor inválido produce `deny`. `blast` va de 0 a 2 y los otros tres de 0 a 1 |
| 2. `Verdict` | **Sin cambio.** `action` sigue en minúsculas (`proceed`, `guide`, `confirm`, `deny`). Se agregan códigos de razón estables (`reason_codes`) |
| 3. `Shield.evaluate` | Se mantiene la firma y se añade un **contexto confiable opcional** (actor, organización, entorno, `dry_run`) que **construye el servidor, nunca el LLM** |
| 4. Evento de auditoría | Pasa a un sobre **versionado** (`schema_version`) con `correlation_id`, `source`, `decider.mode` y `execution.status`. Los campos actuales se conservan |
| 5. Caso del benchmark | Se agregan `spec_version: "unified-1"`, `use_case_id` (AS-01 a AS-15), backend permitido y aserciones de efectos |

**Catálogo de herramientas de entrega (solo estas tres):** `get_orders(order_id?, status?, limit=10)`,
`update_order_status(order_id, new_status)` y `cancel_orders(order_ids, reason)`, con **máximo un ID por ejecución**.
Las otras cinco herramientas salen del catálogo y no hay compatibilidad silenciosa con sus firmas viejas.

**Casos:** los IDs `AS-01` a `AS-15` pasan a tener el significado de la guía v2.1 (ver integracion.md §6). Los casos
originales se conservan en [legacy/cases-v0.jsonl](legacy/cases-v0.jsonl) con prefijo `LEGACY-`. **No se comparan
métricas viejas y nuevas como una serie continua.**

**Regla de migración:** nadie cambia un contrato por su cuenta. Cada cambio es un PR pequeño que actualiza código,
tests y consumidores a la vez, y lo revisa otra persona.

## Flujo de Git

1. Nunca se sube directo a `main`.
2. Una rama por issue: `b/agente-bedrock`, `c/consola-sse`, etc.
3. Pull request pequeño, con `Closes #N`. Otro miembro lo revisa (rotamos: A→B→C→D→A).
4. Se fusiona solo si el CI (pytest) pasa.
5. Antes de empezar el día: `git pull origin main`.

## Ritmo

- **Sync de 15 min cada noche** (21:00): qué terminé, qué hago mañana, qué me bloquea.
- **Regla de la noche**: cada noche `main` corre de punta a punta, aunque sea feo.
- **Bloqueado más de 1 hora**: se avisa en el chat.

## Definición de "hecho"

- El código está en `main` vía PR revisado
- Los tests pasan
- Si cambió el comportamiento del guard, hay un caso nuevo en `bench/cases.jsonl`
- El issue está cerrado y el tablero actualizado
