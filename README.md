# AgentShield

Guard de tool calls para agentes de IA, construido con **Strands Agents**, **Strands Decider 2B** y **Amazon Bedrock**.
Antes de que un agente reembolse dinero, cancele pedidos o mande un correo, AgentShield le hace cuatro preguntas
al Decider en una sola llamada y decide si la acción **pasa, se corrige, espera a un humano o se bloquea**.

Proyecto para el *AWS Agent Experience Hackathon: Strands Decider* (entrega: 23 de octubre de 2026, 11:59 PM PDT).
Patrón declarado: `#guardrails`.

## Empieza aquí (equipo)

| Documento | Para qué |
|---|---|
| [docs/PROPUESTA.md](docs/PROPUESTA.md) | Qué construimos y por qué puede ganar |
| [docs/EQUIPO.md](docs/EQUIPO.md) | Quién hace qué, cómo nos coordinamos, contratos entre módulos |
| [docs/ESTADO.md](docs/ESTADO.md) | **Dónde vamos:** qué está hecho, qué falta y qué sigue |
| [docs/analisis.md](docs/analisis.md) | Análisis de brechas del código frente a la guía v2.1 |
| [docs/integracion.md](docs/integracion.md) | Plan de convergencia propuesto (pendiente de aprobación del equipo) |
| [docs/DIA1.md](docs/DIA1.md) | Paso a paso para dejar GitHub y AWS listos |
| [docs/BACKLOG.md](docs/BACKLOG.md) | Todas las tareas por persona y por día |

## Correr en 2 minutos (sin AWS)

Funciona desde el día 1 con un Decider simulado, para que nadie espere a que la GPU esté lista.

```bash
python -m venv .venv && source .venv/bin/activate   # requiere Python 3.10+; Windows: .venv\Scripts\activate
# En macOS el python3 del sistema es 3.9: usa `uv venv --python 3.12 .venv` (ver docs/ESTADO.md)
pip install -r requirements.txt
pytest -q                                   # 14 tests
python -m bench.run_bench                   # 12 casos contra el Decider simulado
uvicorn console.app:app --reload --port 8080  # consola en http://localhost:8080
```

Con el Decider real: pon `DECIDER_URL=http://IP-DE-LA-EC2:8000` en `.env`.
Con el agente real (requiere Bedrock): `python -m agent.run_agent "Resumeme los tickets que entraron hoy"`.

## Estructura

```
agentshield/          el guard (patrón reutilizable)
  questions.py        las 4 preguntas tipadas al Decider        ← Persona A
  combine.py          respuestas + reglas → veredicto            ← Persona A
  decider_client.py   cliente HTTP real + Decider simulado        ← Persona A
  policy.py           reglas duras desde policies/default.yaml   ← Persona A
  guard.py            Shield + InterventionHandler de Strands    ← Persona A
  audit.py            auditoría JSONL + eventos para la consola  ← Persona C
store/                herramientas y datos ficticios de ElectroNova ← Persona B
agent/                agente Strands + Bedrock                    ← Persona B
console/              consola web con SSE                         ← Persona C
bench/                casos etiquetados y benchmark               ← Persona D
policies/             reglas duras en YAML
tests/                pytest
```

## Cómo decide

1. **Reglas duras** (rol, montos, dominios de correo). Siempre mandan.
2. **Decider 2B**: ¿argumentos fundamentados? ¿coincide con lo que pidió el usuario? ¿lo pidió texto de una herramienta (inyección)? ¿qué tan irreversible es?
3. **combine()**: el Decider solo puede endurecer la decisión, nunca relajar una regla dura.
4. **Strands**: `Proceed`, `Guide`, `Confirm` o `Deny` vía `InterventionHandler.before_tool_call`.

Datos y empresa ficticios. No es una barrera de seguridad definitiva: es una capa adicional sobre IAM y reglas.
