# Backlog por día y por persona

Entrega: **jueves 22** (el viernes 23 es colchón). Cierre oficial: 23 de octubre, 11:59 PM PDT = 12:59 AM del sábado 24 en Guatemala.
`scripts/crear_issues.sh` crea estos issues en GitHub con su etiqueta y milestone.

## Sáb 17 · Día 1: base

| Persona | Tarea |
|---|---|
| A | Confirmar reglas (elegibilidad, equipos), crear repo, subir base, invitar al equipo, tablero |
| A | Correr `examples/strands/` del repo oficial del Decider y comparar con `guard.py` |
| B | Probar `agent/run_agent.py` con Bedrock en cuanto haya credenciales |
| C | Levantar la consola local y proponer el diseño de la pantalla del video (boceto) |
| D | Cuenta AWS, MFA, presupuesto, usuarios IAM, acceso a Bedrock, pedir cuota de GPU |

## Dom 18 · El guard con el modelo real

| Persona | Tarea |
|---|---|
| A | Probar las 4 preguntas con el Decider real y ajustar redacción y `criteria` |
| A | Si la latencia lo pide: medir 4 preguntas juntas vs. separadas |
| B | Agente completo con las 8 herramientas; escenarios AS-01 a AS-06 reproducibles por CLI |
| B | Pasar a la consola el contexto real del agente (mensajes y salidas de herramientas) |
| C | Consola: línea de tiempo por SSE, semáforo, detalle de las 4 respuestas con barras |
| D | EC2 con GPU + `strands-decider serve`; compartir `DECIDER_URL` |
| Todos | 10 casos nuevos cada uno en `bench/cases.jsonl` (ataques para módulos que no hiciste) |

## Lun 19 · Humano en el ciclo y explicación

| Persona | Tarea |
|---|---|
| A | Explicación al operador con Bedrock cuando el veredicto no es Proceed |
| B | Flujo `Confirm`: el agente pausa y la consola aprueba o rechaza |
| C | Botón aprobar/rechazar, interruptor sombra/enforce, formulario "ticket del atacante" |
| D | Auditoría a DynamoDB; desplegar consola + agente en la EC2 (o ECS) |

## Mar 20 · Medición

| Persona | Tarea |
|---|---|
| D | Benchmark Decider vs. LLM juez con los ~50 casos; CSV y gráficas |
| A | Curva de umbral 0.6–0.97; elegir umbral final y documentar errores del Decider |
| B | Correr los 6 escenarios de punta a punta con el modelo real; arreglar lo que falle |
| C | Pulir la consola para grabar: tipografía grande, colores, transiciones |

## Mié 21 · Patrón, video y artículo

| Persona | Tarea |
|---|---|
| A | README del patrón (`agentshield/`) con nota de uso y ejemplo de 30 líneas; borrador del artículo |
| C | Grabar el video (guion en PROPUESTA) con B como operador y D como atacante |
| D | Sección de resultados del artículo con tablas y gráficas |
| B | Ensayo completo del demo y lista de comandos para el video |

## Jue 22 · Entrega

| Persona | Tarea |
|---|---|
| A | Publicar artículo con tags `#strands-decider-2b` y `#guardrails`; enviar el proyecto |
| C | Editar y subir video público (< 3:00), subtítulos en inglés |
| D | Verificar repo público, licencia, README, CI en verde; apagar recursos que no se usen |
| B | Probar todos los links en ventana privada; checklist final |
