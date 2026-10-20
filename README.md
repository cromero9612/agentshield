# AgentShield

Guard de llamadas a herramientas para un agente de pedidos de **ElectroNova**, una empresa ficticia. El agente utiliza **Strands Agents + Amazon Bedrock**; AgentShield intercepta sus propuestas, consulta **Strands Decider 2B** y combina las señales con políticas deterministas.

El catálogo de entrega contiene exactamente tres herramientas:

| Herramienta | Contrato | Comportamiento actual |
|---|---|---|
| `get_orders` | `order_id?`, `status?`, `limit=10` | Consulta hasta diez pedidos. |
| `update_order_status` | `order_id`, `new_status` | Avanza una transición permitida e incrementa la versión. |
| `cancel_orders` | `order_ids`, `reason` | Un ID por ejecución; requiere confirmación en la ruta protegida del agente. |

El backend disponible es `MockOrderConnector`, sobre SQLite. **REST staging, ejecutor autorizado, identidad confiable y aprobaciones persistentes siguen pendientes.** Las herramientas no constituyen por sí solas una barrera de autorización.

## Arranque local

Python 3.12 recomendado. Desde la raíz del repositorio, en macOS/Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python -m bench.run_bench
python -m uvicorn console.app:app --reload --port 8080
```

Abre [http://localhost:8080](http://localhost:8080). En Windows utiliza los comandos de [WINDOWS.md](docs/WINDOWS.md).

La consola y las pruebas funcionan sin AWS. Si `DECIDER_URL` no está configurado, se usa `MockDecider`. El benchmark carga `.env`: para probar con mock deja esa variable vacía tanto en el archivo como en el entorno.

## Qué se ejecuta en cada modalidad

| Modalidad | Qué utiliza | Qué demuestra |
|---|---|---|
| Consola `/api/run` | Propuestas de `bench/cases.jsonl` + guard | Veredictos de fixtures; no ejecuta herramientas ni Bedrock. |
| Consola `/api/attack` | Texto y propuesta preparados + guard | Evaluación de inyección; el formulario aún conserva referencias del alcance anterior. |
| Tests del hook | `Agent` real de Strands, `ScriptedModel`, `MockDecider`, tools y SQLite | Intercepción y efectos reales sobre mock; generación y clasificación simuladas. |
| Agente CLI | Strands + Bedrock, guard y tools mock | Ruta preparada para ejecución real; requiere acceso AWS y un endpoint Decider para usar el clasificador real. |

Los tests locales no sustituyen la evidencia E2E en AWS. Un `PROCEED` o `effective=proceed` mostrado por la consola es un resultado de evaluación, no una confirmación de que se ejecutó una operación.

## Decider real y agente

El proyecto carga `.env` sin reemplazar variables ya definidas en el entorno. Usa [.env.example](.env.example) como referencia, sin sobrescribir un archivo de configuración existente.

```dotenv
DECIDER_URL=http://127.0.0.1:8000
```

Ejemplo de servidor local con la dependencia instalada:

```bash
strands-decider serve StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 --device cpu --port 8000
```

Mantén el servidor abierto y reinicia la consola tras cambiar su configuración. El indicador HTTP señala el endpoint configurado; no acredita por sí solo su salud ni el checkpoint efectivamente servido. El cliente tiene actualmente un timeout de cinco segundos.

Para el agente, configura un modelo disponible mediante `BEDROCK_MODEL_ID`, la región `AWS_REGION` y credenciales/rol del entorno autorizado:

```bash
python -m agent.run_agent "Consulta el pedido ORD-1001."
python -m agent.run_agent "Cancela el pedido ORD-1002; motivo: pedido duplicado."
```

La segunda solicitud puede abrir la confirmación CLI. No hay todavía una aprobación durable con TTL, identidad de aprobador o revalidación vinculada a la decisión. `--shadow` y `--no-shield` son opciones experimentales sobre datos mock; no deben conectarse a sistemas reales.

## Cómo decide

1. La política comprueba allowlist por rol y reglas duras. Un `deny` omite la construcción del estado y la llamada al Decider, y queda auditado con scores/latencia en `null`.
2. En las demás rutas se consultan cuatro preguntas en una llamada: `grounded`, `intent`, `injected` (`noul`) y `blast` (`score`).
3. `combine()` produce `proceed`, `guide`, `confirm` o `deny`. Rechaza números inválidos, conserva el cierre ante errores y no convierte un `guide` por intención/argumentos negativos en aprobable por una regla `confirm`.
4. El handler traduce la decisión a las intervenciones de Strands. La cancelación válida exige confirmación por regla dura.

La banda intermedia de scores todavía produce `confirm`; cambiarla a aclaración es un pendiente del plan unificado. La política conserva herramientas y reglas históricas que deben alinearse al catálogo de tres tools.

## Datos, auditoría y pruebas

- Diez pedidos sintéticos `ORD-1001` a `ORD-1010`, con estados, versiones e historial.
- El mock usa memoria por defecto. Al proporcionar un archivo SQLite, reabrirlo conserva sus datos; `reset()` es explícito y transaccional.
- Auditoría JSONL y SSE con redacción recursiva de credenciales por nombre de campo. No detecta secretos dentro de texto libre ni minimiza automáticamente el contexto enviado a modelos.
- Resultado de referencia de esta consolidación: **139 tests aprobados** en Windows/Python 3.13.16 y **7/7 escenarios con mock**. El main base `96aade8` tenía 131; se incorporan ocho tests del hook. Ver [ESTADO.md](docs/ESTADO.md) para alcance y procedencia.
- CI ejecuta los jobs `test` y `test-windows` en pushes a `main` y PR con destino `main`.

## Consola

Incluye temas oscuro/claro, medidores, modo shadow y timeline SSE. Las siguientes capturas son ilustrativas de la versión visual original: muestran escenarios anteriores y no acreditan el catálogo ni una ejecución E2E actual.

![Tema oscuro, captura histórica](docs/img/consola-oscuro.jpg)

![Tema claro, captura histórica](docs/img/consola-claro.jpg)

## Documentación y alcance

| Documento | Uso |
|---|---|
| [ESTADO.md](docs/ESTADO.md) | Evidencia actual, límites y trabajo integrado. |
| [BACKLOG.md](docs/BACKLOG.md) | Próximas entregas y criterios de aceptación. |
| [EQUIPO.md](docs/EQUIPO.md) | Responsabilidades y contratos realmente implementados. |
| [PROPUESTA.md](docs/PROPUESTA.md) | Producto objetivo y escenarios unificados. |
| [integracion.md](docs/integracion.md) | Plan de convergencia; contiene objetivos aún pendientes. |
| [analisis.md](docs/analisis.md) | Diagnóstico histórico contra el commit base original. |
| [DIA1.md](docs/DIA1.md) | Referencia de preparación inicial, no checklist de estado actual. |

Proyecto para AWS Agent Experience Hackathon: Strands Decider. Patrón `#guardrails`; tags de entrega `#strands-decider-2b` y `#guardrails`. El alcance de la guía incluye GET real de staging y despliegue AWS; no se consideran terminados por tener mocks o tests verdes.

Código bajo [Apache License 2.0](LICENSE). AgentShield es un prototipo experimental y requiere controles de autorización independientes.
