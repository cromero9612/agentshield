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
