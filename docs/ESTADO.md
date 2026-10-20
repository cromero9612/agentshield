# Estado del proyecto

**Revisión:** 19 de octubre de 2026. **Base revisada:** main `96aade888e36afaa626d6b64d98d85cb1eed41ba`.

Esta actualización acompaña la rama de consolidación que incorpora el código visual del PR #35 y los tests del PR #36. Los resultados de 139 tests corresponden a esa rama; el main base tenía 131. Su incorporación efectiva a main depende del merge del PR de consolidación. No se modificaron recursos AWS ni reglas de protección durante esta revisión.

## Estado comprobado

| Área | Implementado / verificado | Límite actual |
|---|---|---|
| Dominio | Diez pedidos, tres herramientas canónicas, transiciones, versión e historial. | Sin contexto autenticado ni alcance por actor/organización. |
| Conector mock | Puerto de pedidos y SQLite; reapertura conserva datos, reset transaccional. | El servicio global sigue usando memoria por defecto. |
| Guard | Rechaza scores inválidos, obliga confirmación para cancelar, audita errores, omite inferencia en hard deny. | Incertidumbre aún produce confirm; falta política de permisos y contexto del alcance final. |
| Auditoría | JSONL, listeners/SSE y redacción recursiva de campos sensibles. | Sin aprobación durable, correlación E2E ni efectos unidos a la decisión; no filtra texto libre. |
| Consola | FastAPI/HTML/SSE; en esta consolidación se recuperan temas y diseño del PR #35. | Evalúa fixtures, no ejecuta el agente/tools; formulario atacante histórico. |
| Agente | Constructor Strands/Bedrock, tools mock, intervención y aprobación CLI. | Sin evidencia E2E Bedrock/Decider/AWS reproducida en esta sesión. |
| Tests | Main base: 131. Consolidación: 139, incluidas ocho pruebas del hook con Strands real. | ScriptedModel y MockDecider sustituyen inferencia; no son E2E AWS. |
| Benchmark | Siete registros EVAL-* de unified-1, 7/7 con mock. | No es accuracy ni latencia medida del checkpoint real. |
| REST staging | Puerto preparado para otro adapter. | Sin RestOrderConnector, registry, GET real, dry-run o controles de producción. |

## Evidencia ejecutada

- `venv/Scripts/python.exe -m pytest -q`: **139 passed**, dos advertencias existentes de FastAPI por `on_event`; Windows, Python 3.13.16.
- Benchmark explícitamente con MockDecider: **7/7** sobre EVAL-001…007; no se presentan sus latencias como inferencia real.
- El CI del main base estaba verde en Linux/Windows. El estado remoto de la consolidación se consulta en su PR; no se hereda automáticamente el verde de otro commit.
- No se invocaron Bedrock, Decider real ni APIs empresariales en esta revisión. La disponibilidad de cuenta, cuotas, modelo y despliegue requiere verificación del responsable AWS.

## Procedencia de cambios

| PR | Destino original | Tratamiento |
|---|---|---|
| #33: contratos/backlog | a/analisis-integracion | No se promueve el snapshot documental antiguo. Esta actualización describe hechos actuales y separa contratos futuros. |
| #35: consola visual | a/consola-visual | Se recupera el commit de código, recursos y capturas en esta consolidación, conservando autoría. |
| #36: tests Strands | b/dominio-pedidos | Se recuperan tests/strands_stub.py y tests/test_strands_hook.py; se actualiza la aserción de fallo auditado al guard actual. |
| #37 | main | Tests de consola con EVAL-* y .vscode ignorado. |
| #38 | main | Persistencia mock y reset transaccional. |
| #39 | main | Redacción recursiva de auditoría. |
| #40 | main | Filtros CI para main y PR hacia main. |
| #41 | main | Denegación determinista antes de Decider. |

Un PR marcado Merged solo acredita su rama destino; los cambios que llegan después a una rama ya fusionada no se propagan a main. Los commits originales #35/#36 se incorporan mediante cherry-pick; no se vuelve a ejecutar su implementación.

## Pendientes centrales

1. Evidencia de lectura Bedrock → hook → Decider real → tool mock → respuesta, con región/modelos y errores registrados.
2. Contexto confiable, ejecutor autorizado y aprobación durable: argumentos/versiones vinculados, identidad, expiración y consumo único.
3. GET REST real de staging por el mismo guard; registry y destinos administrados, secretos del servidor, producción bloqueada y dry-run sin escrituras.
4. Consola conectada a ejecución y efectos; fuente fixture/agente explícita, correlación y consulta de decisiones.
5. Política alineada a tres tools y semántica de incertidumbre; corpus mínimo de 16 variantes y evaluación real separada de calibración.
6. Patrón autocontenido, runbook AWS, artículo, video y enlaces verificados.

El detalle y responsables propuestos están en [BACKLOG.md](BACKLOG.md). Las correcciones de IDs, timeouts o presentación se priorizan según si bloquean alguno de estos resultados.

## Qué demuestra el test del hook

Se usa un Agent de Strands real con tools y SQLite reales, pero un modelo generativo guionizado y MockDecider. Comprueba lectura, bloqueo/corrección, inyección desde una nota, cancelación aprobada/rechazada, actualización, fallo de Decider y comportamiento shadow.

Una cancelación ejecutada una vez en ese guion no prueba idempotencia de una aprobación durable. El test de shadow documenta que la protección se omite; esa modalidad debe mantenerse aislada al mock.

## Datos externos e históricos

Las notas anteriores sobre cuenta AWS, GPU y modelos son reportes históricos, no una comprobación vigente de acceso. No se deben repetir como estado actual sin una prueba nueva. [analisis.md](analisis.md) conserva el diagnóstico del commit 22d1311; sus hallazgos resueltos se contrastan con esta página y el código.

Los issues existentes nacieron del backlog inicial. No se cerraron, reasignaron ni recrearon issues con esta actualización. No ejecutar de nuevo `scripts/crear_issues.sh` sobre este repositorio: no deduplica y crearía tareas repetidas.
