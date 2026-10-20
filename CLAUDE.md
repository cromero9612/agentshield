# AgentShield — instrucciones para Claude Code

Proyecto de 4 personas para el AWS Agent Experience Hackathon (Strands Decider). Entrega: 22 de octubre de 2026.
Lee `docs/ESTADO.md` (dónde vamos), `docs/PROPUESTA.md`, `docs/EQUIPO.md` y `docs/BACKLOG.md` antes de proponer cambios grandes.

## Reglas del proyecto

- Responde y comenta en español; el código y los nombres van en inglés.
- No cambies los contratos de `docs/EQUIPO.md` (GuardAnswers, Verdict, Shield.evaluate, evento de auditoría, formato de casos) sin decírmelo primero: otros 3 compañeros dependen de ellos.
- `combine()` es una función pura: una regla dura `deny` prevalece y un `confirm` no convierte un `guide` semántico en aprobable. Todo cambio ahí va con test.
- Si cambias el comportamiento del guard, agrega o ajusta un caso en `bench/cases.jsonl`.
- Solo toca los archivos del módulo de la persona que te habla, salvo que lo pida.
- Datos y empresa ficticios (ElectroNova). Nunca uses datos reales ni subas `.env`, llaves o credenciales.
- Trabaja en una rama (`<persona>/<tema>`), nunca directo en `main`.

## Comandos

- Tests: `pytest -q`
- Benchmark: `python -m bench.run_bench` (mock si `DECIDER_URL` está vacío)
- Consola: `uvicorn console.app:app --reload --port 8080`
- Agente (requiere Bedrock): `python -m agent.run_agent "Consulta el pedido ORD-1001."`

El catálogo de entrega tiene tres herramientas de pedidos. La consola evalúa fixtures; los tests con ScriptedModel usan Strands real y generación/Decider simulados. Los contratos actuales y los futuros se distinguen en `docs/EQUIPO.md`; `docs/analisis.md` es histórico. No reejecutar el generador inicial de issues sobre el repo existente.

## APIs de referencia

- Strands interventions: `from strands.interventions import InterventionHandler, Proceed, Guide, Confirm, Deny`. `before_tool_call(self, event)` recibe `event.tool_use` (`name`, `input`, `toolUseId`) y `event.agent.messages`.
- Decider: `POST /v1/systemone` con `{"state": ..., "questions": {nombre: {"type": "noul"|"choice"|"score", "instructions": ..., "criteria": ...}}}`. Respuestas: `noul` → float, `choice` → `choice` + `probabilities` + `confidence`, `score` → `score` + `confidence`.
- Ante dudas sobre estas APIs, revisa el código instalado en el entorno virtual antes de suponer.
