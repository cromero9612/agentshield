# Análisis de brecha: guía AgentShield v2.1 frente al código

**Fecha de revisión:** 18 de octubre de 2026, zona America/Guatemala.  
**Repositorio revisado:** copia local del repositorio.  
**Commit de referencia:** `22d13111a13e22875c72a41d2e50c5aea8c58646` — `Base del proyecto`.  
**Documento comparado:** `AGENTSHIELD_MVP_Guia_Implementacion_AWS_Hackathon_2026_v2.1.md` (guía interna del equipo, fuera del repositorio), versión 2.1 del 17 de octubre de 2026.

## 1. Conclusión ejecutiva

**El repositorio contiene una base funcional a nivel de lógica para un guard de herramientas, pero todavía no implementa el MVP descrito en la guía v2.1.** La diferencia principal es de alcance y arquitectura, además de funcionalidades pendientes.

El código sigue la propuesta inicial de **ElectroNova**: ocho herramientas simuladas de inventario, clientes, pedidos, reembolsos y correos; cuatro preguntas al Decider; datos en memoria; consola que evalúa propuestas preparadas. La guía v2.1 define un producto más acotado en negocio y más completo en ejecución: **tres herramientas canónicas de pedidos**, conectores mock/REST intercambiables, identidad confiable, aprobación vinculada a la operación, revalidación antes de mutar, persistencia y evidencia E2E en AWS.

Hay piezas valiosas que se pueden conservar: `combine()` es puro, las reglas están separadas del modelo, existe un cliente HTTP de Decider, hay construcción de agente Bedrock, un handler de intervención, auditoría JSONL, SSE, benchmark y tests iniciales. No hace falta empezar desde cero.

Los bloqueantes más importantes son:

1. **No existen los conectores ni el ejecutor autorizado de v2.1.** Las herramientas modifican directamente estructuras en memoria.
2. **Los contratos y casos no corresponden a la guía.** Falta `update_order_status`; `get_orders` no consulta por ID; `cancel_orders` cancela por estado y puede afectar varios pedidos.
3. **La aprobación de cancelación no es una regla dura.** Con valores optimistas del modelo, la política actual permite `PROCEED` sin confirmación.
4. **Hay decisiones inseguras ante salidas inválidas o combinaciones de reglas.** `NaN` puede terminar en `PROCEED`; una regla `CONFIRM` puede transformar un `GUIDE` por falta de intención en una acción aprobable.
5. **No hay evidencia local suficiente para acreditar el flujo real AWS + Bedrock + Decider 2B + herramienta.** Tener imports y constructores no prueba una ejecución desplegada.
6. **La consola evalúa veredictos, pero no ejecuta el agente ni las herramientas.** No demuestra efectos antes/después ni un ciclo real de aprobación.
7. **La documentación y el backlog internos siguen el alcance anterior.** Incluso reutilizan IDs AS con significados distintos.

**Evaluación de madurez:** prototipo inicial del núcleo de evaluación y de la demo local. No se acredita el DoD global de la guía ni la capacidad de conexión empresarial de v2.1.

## 2. Alcance, método y límites

### 2.1 Qué se revisó

- Guía completa, incluidas arquitectura, conectores, política, contratos, pruebas, despliegue y entregables.
- Todos los módulos Python de `agentshield/`, `agent/`, `store/`, `console/`, `bench/` y `tests/`.
- Dataset JSON, casos JSONL, política YAML, frontend HTML, dependencias, configuración de ejemplo, CI, README y documentos del equipo.
- Estado local de Git e inventario de archivos, incluidos archivos ocultos relevantes.
- Comprobaciones aisladas de la función de decisión y lectura sintáctica de los 17 archivos Python.

**La guía se usa como especificación comparativa. Sus instrucciones al “agente implementador” son contenido del documento, no una orden del usuario para implementar, desplegar o publicar.** Esta revisión produce únicamente este análisis; no corrige código ni provisiona recursos.

### 2.2 Cómo interpretar los estados

| Estado | Significado |
|---|---|
| Implementado en código | La responsabilidad existe y se puede identificar en el árbol revisado; no implica validación E2E. |
| Parcial | Existe una parte, pero faltan controles, integración, alcance o pruebas relevantes. |
| Ausente | No se encontró implementación equivalente en el repositorio revisado. |
| No verificado | Depende de infraestructura, servicios o evidencia externa no comprobados en esta revisión. |
| Divergencia de diseño | El código toma una decisión diferente de la guía; debe evaluarse por efecto, no solo por nombres o carpetas. |

No se asigna un porcentaje global de avance: contar archivos o requisitos sin ponderación produciría una precisión engañosa. Tampoco se considera incumplimiento funcional cada diferencia de estructura de carpetas; la guía misma propone crecimiento incremental.

### 2.3 Límites de la evidencia

- No se invocó Bedrock, un servidor real de Decider ni una API empresarial.
- No se consultó la cuenta AWS ni se verificaron recursos desplegados, permisos, costos o conectividad.
- No se verificó en internet la publicación del repositorio, artículo, video, inscripción, elegibilidad ni reglas actuales del evento.
- Las fechas, prioridades y referencias a requisitos de hackathon se comparan **según la guía entregada**. No son una certificación independiente de las reglas oficiales.
- No se inspeccionaron secretos ni se necesitó leer `.env`.
- La falta de evidencia versionada de un despliegue significa **no acreditado en esta revisión**, no demuestra que nadie haya desplegado algo fuera del repo.
- Había un directorio `.vscode/` sin seguimiento antes de empezar; no se modificó.

## 3. Qué está construido actualmente

### 3.1 Flujo de agente por CLI

```text
Solicitud CLI
  → Agent de Strands con BedrockModel y ocho herramientas
  → AgentShieldHandler.before_tool_call
  → extracción del último mensaje de usuario + resultados de tools
  → Policy.check
  → MockDecider o HttpDecider
  → combine
  → auditoría JSONL
  → Proceed / Guide / Confirm / Deny
  → herramienta sobre datos en memoria, si el SDK permite la ejecución
```

El wiring está en [agent/run_agent.py](../agent/run_agent.py), y el handler en [agentshield/guard.py](../agentshield/guard.py). La frase “si el SDK permite” es relevante: no se comprobó aquí la compatibilidad de las firmas ni el comportamiento real del SDK instalado.

### 3.2 Flujo real de la consola actual

```text
Botón de caso predefinido
  → POST /api/run con case_id y threshold
  → carga de propuesta desde bench/cases.jsonl
  → Shield.evaluate
  → veredicto JSON + evento SSE
```

**Esta ruta no crea un agente Bedrock, no genera una propuesta y no ejecuta la herramienta.** Un `PROCEED` mostrado en pantalla indica el resultado de evaluación de la propuesta preparada. Un `CONFIRM` mostrado tampoco crea una aprobación pendiente ejecutable.

### 3.3 Flujo objetivo de la guía

```text
Identidad verificada + configuración administrada
  → Strands/Bedrock propone una de tres tools canónicas
  → prechecks de esquema, permiso, recurso, entorno y conector
  → Decider 2B real y política versionada
  → bloqueo / corrección / aprobación vinculada / permiso
  → ejecutor revalida y aplica dry_run, límites e idempotencia
  → MockOrderConnector o RestOrderConnector registrado
  → efecto verificado o resultado desconocido explícito
  → auditoría correlacionada de decisión y ejecución
```

La brecha grande está entre **calcular una decisión** y **garantizar que la ejecución concreta respete esa decisión y su contexto**.

## 4. Matriz de cumplimiento del DoD global

Referencia: guía §1.3 y gates §13.3.

| Requisito de la guía | Estado | Evidencia / brecha |
|---|---|---|
| Aplicación o endpoint ejecutándose en AWS | No verificado | Hay instrucciones de preparación en `docs/DIA1.md`, pero no evidencia de servicio activo ni E2E registrado. |
| Petición natural con salida generada por Bedrock | Parcial / no verificado | `build_agent()` construye `BedrockModel`; falta ejecución real documentada. La web no usa esta ruta. |
| Tool propuesta por agente y paso real por hook | Parcial / no verificado | Handler y `interventions=[...]` presentes; faltan tests de integración y trazas reales. |
| Dos respuestas reales `noul` con política visible | Parcial | Hay preguntas equivalentes `grounded`/`intent`, más dos extensiones; por defecto se usa mock y no hay evidencia del checkpoint. |
| Cuatro casos centrales y efectos en pedidos | Divergencia / parcial | Existen casos con IDs similares, pero otros contratos y escenarios; los tests verifican veredictos, no efectos. |
| GET E2E real mediante RestOrderConnector | Ausente | No hay puerto, adapter REST, registry ni API staging integrada. |
| Producción bloqueada y dry_run sin side effects | Ausente como capacidad de v2.1 | Hoy no hay REST; tampoco controles explícitos de entorno o dry_run que puedan acreditarse. |
| Aprobar/rechazar antes de mutar | Parcial | Callback CLI con `Confirm`; faltan prueba SDK, identidad, aprobación durable y revalidación. |
| Trazas distinguen agente de fixture | Parcial | Eventos tienen veredicto y latencia; no tienen `source`, modelo real/mock ni correlación. |
| Patrón reutilizable documentado y probado | Parcial | Código modular en `agentshield/`, pero no activo autocontenido equivalente al patrón pedido. |
| Repo público, licencia, artículo y video | Mixto / no verificado | Existe licencia Apache 2.0. Publicidad y publicaciones no comprobadas; no se halló evidencia suficiente en README. |

**Ningún gate G0–G5 puede darse por cerrado con toda su evidencia a partir del repo revisado.** Esto no niega la existencia del núcleo de código; significa que los gates exigen comprobaciones adicionales.

## 5. Diferencias de alcance y contratos de negocio

### 5.1 Herramientas

Referencia: guía §4.1 y [store/tools.py](../store/tools.py:29).

| Herramienta objetivo | Contrato v2.1 | Código actual | Implicación |
|---|---|---|---|
| `get_orders` | `order_id?`, `status?`, DTO/consulta acotada | `get_orders(status="", week=0)` devuelve JSON en texto | No puede atender una consulta por `order_id` como pide AS-03. `week` no se utiliza. Sin paginación ni límite. |
| `update_order_status` | `order_id`, `new_status`, transición válida | No existe; hay `update_order_amount` | Cambiar monto no sustituye una transición de estado. Falta todo el caso de negocio. |
| `cancel_orders` | IDs explícitos, motivo, versiones; REST máximo un ID | `cancel_orders(status)` cancela todos los pedidos del estado | El recurso afectado se expande a partir de un filtro. No hay motivo, límite, versión ni aprobación dura. |

Además se exponen `get_inventory`, `get_tickets`, `update_customer`, `update_order_amount`, `issue_refund` y `send_email`. Son herramientas simuladas útiles para la propuesta original, pero amplían el alcance respecto al MVP cerrado de la guía.

**No es un cambio cosmético de firmas:** afecta el prompt del agente, schemas, políticas, respuestas del mock, fixtures, métricas, tests y demostración.

### 5.2 Dataset y reglas de pedidos

| Aspecto | Guía | Implementación |
|---|---|---|
| Pedidos sintéticos | 10, IDs tipo ORD-1001…ORD-1010 | 3, IDs `88123`, `88130`, `90311`. |
| Estados | PENDING, PROCESSING, SHIPPED, DELIVERED, CANCELLED | `paid`, `delayed`; cancelación escribe `cancelled`. |
| Versiones e historial | Estado/versionado para comprobar y revalidar | Sin `version`, historial ni mecanismo de concurrencia. |
| Alcance/propietario | Recurso accesible al actor/organización | Campo `customer`, sin comprobación de alcance. |
| Transiciones | Camino definido y cancelación limitada por estado | No hay máquina de estados; cancelar cualquier estado indicado es posible. |
| Persistencia | SQLite para demo | Diccionario `DB` y lista `SENT_EMAILS` en memoria. |
| Reset | Reproducible y restringido | `reset()` restaura seed local; no endpoint administrativo ni persistencia. |

Evidencia: [store/data.json](../store/data.json), [store/tools.py](../store/tools.py:14).

### 5.3 Roles y autoridad

La guía distingue `viewer`, `operator` y `approver`, con identidad obtenida del servidor. El YAML actual define un único rol `agente_soporte` con las ocho herramientas permitidas.

`Shield.evaluate()` acepta un rol opcional, y `Policy.check()` deniega tools fuera de su allowlist. Esta es una base válida. Sin embargo, `AgentShieldHandler.before_tool_call()` no propaga identidad ni rol: usa el rol por defecto. La consola también evalúa con ese rol.

**El control de rol existe como función, pero no está conectado a una identidad confiable en las rutas operativas.** No hay permisos por organización, recurso, conector o entorno.

## 6. Conectores empresariales: brecha completa de v2.1

Referencia: guía §6, ADR-008…011 y tareas AS-T18…22.

| Capacidad | Estado actual | Trabajo necesario |
|---|---|---|
| `OrderConnectorPort` y DTO canónicos | Ausente | Definir operaciones, consultas y resultados tipados. |
| `MockOrderConnector` | Ausente como adapter | Extraer la lógica de `store/tools.py` a un backend detrás del mismo puerto. |
| `RestOrderConnector` | Ausente | GET HTTP real a staging, validación y mapeos. Escrituras staging son P1. |
| Registry administrado | Ausente | Resolver destino desde configuración y contexto confiable. |
| Manifiesto tipado y versionado | Ausente | Capacidades, host, paths, métodos, secretos referenciados, flags y validación. |
| Proveedor de credenciales | Ausente | Integración de secretos del servidor, separados por entorno. |
| Contexto de ejecución confiable | Ausente | Actor, organización, scopes, conector, entorno, correlación y política. |
| Ejecutor autorizado | Ausente | Revalidar y despachar; impedir acceso directo al adapter sin controles. |
| Producción apagada explícitamente | Ausente | Flags y validaciones independientes; no aceptar selección desde el LLM. |
| `dry_run` | Ausente | Resolver antes del despacho de escritura; cero HTTP de mutación. |
| Aislamiento fixture/REST | No representado | Vincular fixtures a mock y comprobarlo con contadores de llamadas. |
| HTTP seguro de negocio | Ausente | HTTPS, allowlist, DNS/IP, redirects, paths, límites y timeout. |
| Errores upstream | Ausente | Mapear 401/403/404/409/429/5xx, errores de esquema y timeouts. |
| Idempotencia/conciliación | Ausente | Claves del servidor, intención durable y resultado UNKNOWN cuando corresponda. |

**`HttpDecider` no es un conector empresarial.** Su HTTP sirve para consultar el clasificador; no consulta una API de pedidos.

La ausencia actual de REST hace que hoy no haya mutaciones de negocio externas. Eso no equivale a haber implementado y probado `PRODUCTION_DISABLED`, aislamiento o `dry_run`. Son garantías que deben existir al introducir la integración.

## 7. Motor de decisión y hallazgos de seguridad

### 7.1 Lo que está bien encaminado

- `combine()` no hace red ni accede a datos: es fácil de probar y conservar como núcleo puro.
- `Policy.check()` separa reglas deterministas de la señal semántica.
- Una regla dura `DENY` prevalece dentro de `combine()`.
- Hay allowlist por rol, límites de monto y control de dominio de correo para el alcance original.
- El handler declara `on_error = "deny"`.
- Hay `Guide` con feedback para que el agente pueda corregir la propuesta.

Estos aciertos son parciales: el modo shadow y los accesos directos a herramientas requieren considerar la ejecución completa.

### 7.2 G-01 — Cancelación sin aprobación obligatoria por código

**Prioridad recomendada: P0. Evidencia:** [policies/default.yaml](../policies/default.yaml:24), [agentshield/policy.py](../agentshield/policy.py:43), [agentshield/combine.py](../agentshield/combine.py:95).

La guía exige que una cancelación válida requiera siempre confirmación humana. Actualmente `always_confirm` está vacío y la confirmación depende de `blast >= 1.5` o de incertidumbre semántica.

Comprobación aislada ejecutada:

```python
combine(GuardAnswers(.95, .95, 0, 0), HardResult()).action
# 'proceed'
```

La función no recibe el nombre de la herramienta; es `Policy` quien debe imponer la obligación de cancelar con aprobación. El mock devuelve `blast=2` para cancelación, por lo que el caso preparado confirma y puede ocultar este gap.

**Consecuencia:** la seguridad de la cancelación depende de que el modelo clasifique correctamente el impacto. **Cierre:** regla determinista de confirmación, ejecución vinculada a aprobación y test con scores deliberadamente optimistas.

### 7.3 G-02 — Un GUIDE semántico puede convertirse en CONFIRM

**Prioridad: P0. Evidencia:** [agentshield/combine.py](../agentshield/combine.py:15), [agentshield/combine.py](../agentshield/combine.py:100).

La función ordena acciones como `PROCEED < GUIDE < CONFIRM < DENY`. Pero pedir aclaración y aprobar una operación no representan niveles intercambiables de seguridad.

Comprobación ejecutada:

```python
combine(
    GuardAnswers(.95, .05, 0, 0),
    HardResult('confirm', ('requiere aprobacion',))
).action
# 'confirm', aunque intent=.05 produce GUIDE antes de combinar
```

Una propuesta que no coincide con la intención puede acabar disponible para aprobación. Esto puede ocurrir con reglas actuales de monto/dominio y se vuelve especialmente importante si se añade confirmación obligatoria a cancelaciones sin revisar la combinación.

**Cierre:** usar reglas explícitas de elegibilidad: una propuesta sin intención/argumentos válidos se corrige o rechaza; solo una propuesta válida entra al flujo de aprobación. Preservar también la causa semántica en auditoría.

### 7.4 G-03 — Salidas Decider inválidas pueden permitir ejecución

**Prioridad: P0. Evidencia:** [agentshield/decider_client.py](../agentshield/decider_client.py:27), [agentshield/combine.py](../agentshield/combine.py:68).

El cliente accede directamente a campos JSON y construye `GuardAnswers` sin validar tipos, finitud o rangos. El dataclass no valida en runtime.

Comprobaciones ejecutadas:

```python
combine(GuardAnswers(float('nan'), float('nan'), float('nan'), float('nan')),
        HardResult()).action
# 'proceed'

combine(GuardAnswers(2, 2, -1, -1), HardResult()).action
# 'proceed'
```

Con `NaN`, las comparaciones no activan las ramas de rechazo/incertidumbre. Algunos campos ausentes o tipos incompatibles generarían excepciones; ese comportamiento no cubre todos los resultados inválidos.

**Cierre:** normalización tipada estricta, números finitos, rangos por tipo de pregunta, validación del umbral y errores estables. En escritura, salida inválida debe terminar sin mutación y con error auditable. Estas pruebas reproducen el núcleo local; no afirman que el servidor real emita esos valores.

### 7.5 G-04 — Errores de Decider sin resultado y auditoría del guard

**Prioridad: P0. Evidencia:** [agentshield/guard.py](../agentshield/guard.py:35).

`Shield.evaluate()` llama al Decider sin `try/except`; la auditoría ocurre después. Si falla HTTP, JSON o parsing, no se registra la decisión fallida desde esta función. La consola y el benchmark tampoco convierten el fallo en un resultado controlado.

El handler declara cierre ante errores mediante `on_error`, lo que es positivo. **No se ha demostrado aquí que la versión concreta del SDK lo aplique**, y esa protección no produce automáticamente una traza del error en las llamadas directas a `Shield.evaluate()`.

Además, incluso cuando `Policy` devuelve `DENY`, se llama al Decider antes de regresar la denegación. Si el modelo falla, se pierde el resultado estructurado de una regla que ya había rechazado la operación.

**Cierre:** salida anticipada para hard deny, estado `decider.invoked=false`, manejo de fallo tipado y auditoría de error; prueba del handler real con herramienta espía y cero mutaciones.

### 7.6 G-05 — Validación de negocio ausente en la mutación

**Prioridad: P0. Evidencia:** [store/tools.py](../store/tools.py:49).

Las funciones de escritura no revalidan actor, estado permitido, versión, aprobación ni idempotencia al modificar datos. `cancel_orders` modifica todas las coincidencias de estado. `issue_refund` agrega un registro sin validar siquiera existencia del pedido o duplicidad.

No existe una capa equivalente a `AuthorizedToolExecutor`. El hook es la única barrera en la ruta protegida del agente, y los modos sin protección permiten acceder a las mismas herramientas.

**Cierre:** mover mutaciones a un servicio/ejecutor que valide contexto y recurso al momento de escribir; para mock, transacción y consumo único de aprobación; para REST, contrato de idempotencia y conciliación propios.

### 7.7 G-06 — Shadow permite incluso hard DENY

**Prioridad: P0 antes de integrar REST. Evidencia:** [agentshield/guard.py](../agentshield/guard.py:95), [agent/run_agent.py](../agent/run_agent.py:45).

Si `mode == "shadow"`, el handler devuelve `Proceed` incluso cuando el veredicto calculado es `DENY`. `--no-shield` omite por completo el guard. En el estado actual las tools son simuladas y esos modos sirven para comparar experimentos.

La guía permite baseline solo en sandbox aislado. El código no liga estos modos a un backend/entorno seguro ni identifica explícitamente una ejecución experimental en el resultado de negocio. **No se encontró una ruta HTTP pública que active esos flags; hoy son opciones CLI.**

**Cierre:** aislamiento explícito a mock/sandbox y autorización determinista que siga aplicándose independientemente de la observación semántica. No conectar un adapter real a estas rutas sin resolverlo.

### 7.8 G-07 — Contexto no equivale a autorización

**Prioridad: P0 para datos reales. Evidencia:** [agentshield/guard.py](../agentshield/guard.py:63), [agentshield/questions.py](../agentshield/questions.py:53).

El estado contiene el último mensaje de usuario, los últimos tres textos de herramientas y la propuesta. No contiene actor, alcance autorizado, efecto conocido por código ni delimitación de confianza del contexto. Las salidas de herramientas no se filtran por esquema o clasificación.

`context_from_messages()` descarta mensajes previos al último pedido de usuario. Por tanto, una referencia legítima a un ID mencionado en un turno anterior puede perder su respaldo. En el mock, cualquier texto recibido de herramientas participa en la heurística `seen`, sin comprobación de autoridad.

La pregunta adicional de inyección es útil, pero no sustituye la selección de contexto autorizado por la aplicación.

**Cierre:** memoria autorizada y minimizada, separación explícita de datos no confiables y efecto/permiso definidos en código. Limitar también tamaño en caracteres/tokens: conservar tres textos no evita que cada uno sea enorme.

### 7.9 G-08 — Redacción de auditoría insuficiente para datos empresariales

**Prioridad: P0 antes de datos reales. Evidencia:** [agentshield/audit.py](../agentshield/audit.py:15).

`minimize()` solo trata cuatro claves exactas de primer nivel: `account`, `card`, `password`, `token`. Conserva los últimos cuatro caracteres incluso de passwords/tokens. No recorre objetos/listas ni reconoce variantes como `Authorization`, `access_token` o cabeceras.

Se comprobó que un secreto sintético anidado y otro bajo `Authorization` quedan intactos. Tampoco se redaccionan `reason`, prompts de aprobación o estado enviado al modelo.

**Cierre:** allowlist de campos auditables, redacción recursiva cuando proceda, eliminación completa de credenciales y separación entre minimización para auditoría y minimización para modelos.

### 7.10 G-09 — Configuración .env no cargada

**Prioridad: P0 de reproducibilidad. Evidencia:** [README.md](../README.md), [.env.example](../.env.example), [agentshield/decider_client.py](../agentshield/decider_client.py:92).

El README indica poner `DECIDER_URL` en `.env`, pero el código solo usa `os.getenv`. No hay `load_dotenv`, dependencia equivalente ni comando documentado que cargue ese archivo. Crear `.env` por sí solo no configura esas variables para los comandos de Python mostrados.

**Consecuencia:** alguien puede creer que usa Decider real y seguir en `MockDecider`. Lo mismo afecta región/modelos si no se exportan desde el entorno por otra vía.

**Cierre:** cargar configuración explícitamente o documentar comandos de exportación/`--env-file` donde aplique; mostrar al arrancar el modo efectivo y fallar si una ejecución declarada real no tiene endpoint válido.

## 8. Preguntas, umbrales y contrato del Decider

Referencia: guía §7.1–7.4, §9; [agentshield/questions.py](../agentshield/questions.py), [agentshield/decider_client.py](../agentshield/decider_client.py).

| Aspecto | Guía v2.1 | Código actual | Lectura del gap |
|---|---|---|---|
| Preguntas mínimas | `args_grounded`, `intent_aligned`, ambas `noul` | `grounded`, `intent`, `injected` (`noul`) y `blast` (`score`) | Las dos primeras son equivalentes conceptualmente; nombres y respuesta requieren adapter. Las extensiones son de la propuesta original. |
| Estado | Contexto autorizado, efecto y rol; ejemplo textual delimitado | Diccionario con usuario, outputs y propuesta | Falta información/segmentación de confianza. No se certificó compatibilidad del tipo de `state` con un servidor concreto. |
| Contrato de respuesta | Respuestas, checkpoint, uso y latencia | Extrae valores/latencia; descarta `model` y `usage` | No permite acreditar qué modelo respondió ni medir tokens/invocación por traza. |
| Umbrales iniciales | Bajos <.40, intermedios .40–<.75, favorables >=.75; a calibrar | `T=.9`, banda `1-T…T` | Es una decisión distinta, no un incumplimiento automático de umbrales oficiales. Debe justificarse con datos. |
| Incertidumbre de escritura | Aclarar; no aprobar una acción no fundamentada | Generalmente `CONFIRM` | Diferencia funcional importante: aprobación no reemplaza la aclaración. |
| Impacto | Criticidad conocida por herramienta/código | `blast` inferido por modelo | El impacto debe tener al menos una base determinista. |
| Modelo de desarrollo | Stub solo para tests; E2E real | Mock automático si falta URL | Útil localmente; debe ser explícito e imposible de confundir en evidencia real. |

Ejemplo concreto: `grounded=.20`, `intent=.95`, `injected=0`, `blast=0` produce `CONFIRM` con T=.9. Según la tabla orientativa de v2.1, una señal grounded tan baja debería corregirse o denegarse.

No se recomienda copiar ciegamente .40/.75: la guía aclara que son hipótesis. Sí se recomienda separar validez de la propuesta, autorización y necesidad de aprobación.

La documentación de `GuardAnswers` describe valores como probabilidades y dice “entre 0 y 1”, pero `blast` utiliza escala 0–2. Conviene documentar las escalas y evitar presentar `noul` como probabilidad certificada de seguridad.

## 9. Aprobación humana, persistencia y concurrencia

Referencia: guía §7.6, §8.5, §9.6.

### Lo existente

`AgentShieldHandler` construye un `Confirm`. El CLI ofrece una pregunta de sí/no mediante `_cli_approver`, cuyo resultado se pasa a `Confirm(response=...)`. Sin callback, devuelve `Confirm` sin respuesta.

Es una base de interacción humana, pero **no se ha probado el contrato de `response` ni interrupt/resume con una versión concreta del SDK**. No corresponde afirmar que esté roto ni que esté validado sin esa prueba.

### Lo pendiente

- Aprobación persistente con estados pendiente, aprobada, rechazada, expirada, ejecutada y fallida.
- Identidad y permiso del aprobador, separados de un rol enviado libremente.
- Vínculo a `decision_id`, actor, organización, conector, entorno, política, hash de argumentos y versión del pedido.
- TTL y rechazo de aprobaciones vencidas, duplicadas o de propuestas modificadas.
- Revalidación inmediatamente antes de mutar.
- Consumo atómico de aprobación y control de concurrencia.
- Persistencia tras reinicio y evidencia antes/después.
- Si se añade REST de escritura: idempotencia upstream y resultado desconocido/conciliación ante timeout ambiguo.

**Una confirmación interactiva local puede ser una solución de demo**, conforme al recorte permitido por la guía, siempre que se pruebe el SDK y los controles necesarios. Un botón que solo cambia el veredicto visual no lo sería. Actualmente la consola ni siquiera tiene ese botón.

## 10. API y experiencia de demo

Referencia: guía §8 y §11; [console/app.py](../console/app.py:49), [console/static/index.html](../console/static/index.html).

| Capacidad objetivo | Código actual | Gap |
|---|---|---|
| Escenarios | `GET /api/cases` | Equivalente básico a listado; los contratos/IDs deben alinearse. |
| Fixture por guard real y fuente explícita | `POST /api/run` evalúa fixture con Decider configurado | Fuente no etiquetada en UI; mock puede estar activo; no hay efecto de tool. |
| Solicitud libre a agente Bedrock | Solo CLI separado | Falta integración de agente en API/consola. |
| Detalle de decisión por ID | Sin endpoint | JSONL no tiene consulta implementada. |
| Timeline por ejecución | SSE global `/api/events` | Sin filtro por correlación, persistencia/replay ni separación entre sesiones. |
| Pedidos antes/después | Sin ruta/vista | No se ejecutan tools desde consola ni se muestran efectos. |
| Aprobar/rechazar | Solo callback CLI | Sin API protegida ni flujo persistente. |
| Estado live/ready | Ausente | No distingue API viva de Bedrock/Decider/configuración utilizables. |
| Connector/environment/model/source | Ausentes en UI | No acredita mock/REST, sandbox/staging, fixture/agente o mock/modelo real. |
| Validación operativa | `case_id: str`, `threshold: float` | No restringe rango/finitud; ID desconocido causa acceso a diccionario sin manejo. |

La consola ya presenta intención, propuesta, acción, checks y eventos: es una buena base visual. **Cambiar HTML por React no es el gap prioritario**; la guía permite CLI/API y considera UI P1.

Observaciones de robustez:

- `/api/run` modifica `shield.threshold`, compartido entre solicitudes. Hay riesgo de interferencia entre ejecuciones concurrentes; conviene pasar configuración por request o hacerla inmutable y administrada.
- SSE publica eventos a todos los suscriptores; sin autenticación ni filtro. Con datos reales se necesitaría aislamiento de acceso.
- Las colas SSE no tienen límite ni heartbeat/replay; no es bloqueante para una demo local controlada, pero sí una limitación operativa.
- La UI inserta contenido mediante `innerHTML` e `insertAdjacentHTML`. Hoy consume fixtures locales; al introducir texto libre o datos externos debe escaparse o usarse `textContent` para evitar inyección HTML.
- No hay manejo visible de error de `fetch`; un timeout o fallo del Decider no se convierte en una explicación clara para el operador.
- No se encontraron rate limits ni autenticación de API. Hoy la ruta evalúa fixtures y no muta pedidos; no confundir esa limitación actual con autorización suficiente para futuras escrituras públicas.

## 11. Auditoría y observabilidad

Referencia: guía §8.3, §10.3; [agentshield/audit.py](../agentshield/audit.py), [agentshield/guard.py](../agentshield/guard.py:41).

### Ya disponible

JSONL con `decision_id`, modo, tool, argumentos parcialmente minimizados, reglas duras, respuestas normalizadas, latencia, veredicto, razón y timestamp; suscripción de listeners usada por SSE.

### Faltante para trazabilidad de v2.1

| Grupo | Campos/capacidad pendientes |
|---|---|
| Correlación | `correlation_id`, `run_id`, `execution_id`, `toolUseId` y relación con aprobación. |
| Procedencia | `source=agent/fixture-replay`, escenario, Decider real/mock e invocación efectivamente realizada. |
| Versiones | Política, checkpoint/revisión, modelo Bedrock, conector y manifiesto. |
| Autoridad | Actor, organización, permiso, alcance, aprobador y entorno. |
| Ejecución | Pendiente, rechazada, ejecutada, fallida o desconocida; efecto antes/después y verificación. |
| HTTP | Método/operación permitida, status y request ID upstream, sin secretos. |
| Errores | Fallo de inferencia/configuración/aprobación/dispatch auditado con códigos estables. |
| Tiempo | Timestamp con zona/UTC, latencia separada de guard, modelo, upstream y E2E. |
| Consulta | Recuperar decisiones y timeline por ID/correlación, incluidos reinicios. |

`decision_id` usa solo los primeros ocho caracteres de un UUID: 32 bits de identificador. Es suficiente para una demo pequeña, pero se recomienda UUID completo para auditoría durable. El timestamp actual carece de zona horaria.

Un listener que lance una excepción propaga el error después de que el registro ya fue escrito. No hay separación entre fallo de emisión de UI y auditoría. Conviene que la observabilidad secundaria no vuelva ambiguo el resultado operativo.

## 12. Casos AS: colisión de nombres y cobertura real

**Un `AS-XX` actual no acredita automáticamente el `AS-XX` de la guía.** Referencias: guía §4.4/§10.4 y [bench/cases.jsonl](../bench/cases.jsonl).

| ID | Guía v2.1 | Caso actual del repo | Cobertura respecto a v2.1 |
|---|---|---|---|
| AS-01 | Consulta de pendientes, propuesta indebida de cancelación por IDs | Reporte de atrasados, cancelación por estado | Tema equivalente; sin contrato canónico ni aserción de cero mutaciones. |
| AS-02 | ID de pedido inventado al actualizar estado | ID de cliente inventado al actualizar teléfono | Comprueba concepto de grounding; no escenario ni herramienta objetivo. |
| AS-03 | Lectura de pedido ORD-1001 | Inventario TV-55X en Z10 | Otra tool; no acredita consulta de pedidos ni E2E real. |
| AS-04 | Cancelación legítima pendiente, aprobación y efecto | Envío de clientes VIP a Gmail | Caso distinto; no acredita HITL de cancelación. |
| AS-05 | Ambigüedad sin escritura | Ajuste de monto dudoso | Aproximación semántica; solo veredicto confirm, sin efecto probado. |
| AS-06 | Decider caído/timeout sin escritura | Inyección de reembolso desde ticket | Distinto; no cubre resiliencia. |
| AS-07 | Viewer no puede cancelar | Consulta de pedidos atrasados | Distinto; no cubre permiso. |
| AS-08 | Aprobación doble o expirada | Actualización legítima de teléfono | Distinto; no cubre replay/TTL. |
| AS-09 | GET real a staging por conector REST | Cancelación masiva por estado | Distinto; la lectura REST no existe. |
| AS-10 | Dry-run sin HTTP de escritura | Inyección de correo externo | Distinto. |
| AS-11 | Actor/tenant/conector no autorizado | Reembolso sobre límite monetario | Distinto. |
| AS-12 | Escritura staging única tras aprobación revalidada | Correo legítimo de alto impacto | Distinto. |
| AS-13 | Timeout ambiguo, UNKNOWN y no retry ciego | No existe | Sin cobertura. |

**Recomendación:** preservar los casos anteriores con namespace explícito, por ejemplo `LEGACY-AS-06`, y crear los nuevos con referencia a la versión de especificación. Evitar sobrescribir etiquetas y después comparar métricas históricas como si midieran lo mismo.

## 13. Pruebas y métricas: qué se puede afirmar

### 13.1 Inventario de tests

Hay **14 funciones de test**: 8 en `test_combine.py` y 6 en `test_policy_and_guard.py`. Una de las seis recorre los 12 casos del benchmark con `MockDecider`.

Cubren decisiones puras, prevalencia de reglas duras, umbral, límites monetarios, correo externo, tool desconocida, una redacción de cuenta, fixtures mock y extracción básica de contexto.

No prueban ejecución real de herramientas, integración Strands, HTTP Decider, Bedrock, approvals, cambios antes/después, concurrencia, fallos de modelo, REST, entorno, SSRF o idempotencia.

### 13.2 Ejecución realizada durante esta revisión

| Comprobación | Resultado | Interpretación |
|---|---|---|
| `python --version` / `python -m pytest -q` con Python del PATH | No se pudo iniciar el alias WindowsApps | Problema del entorno local, no fallo de lógica del proyecto. |
| Python del runtime disponible, `-m pytest -q` | `No module named pytest` | Suite completa no ejecutada. Ese runtime tampoco tiene yaml, strands, fastapi o boto3. |
| 8 funciones de `tests/test_combine.py` ejecutadas directamente con biblioteca estándar | **8/8 pasaron** | Validación limitada del módulo puro; no equivale a `pytest` completo. |
| Entradas adversas a `combine()` | Reproducidos G-01, G-02, G-03 y grounded=.20 → confirm | Evidencia dinámica aislada de las decisiones indicadas. |
| Redacción con secretos sintéticos anidados/Authorization | Permanecen sin minimizar | Evidencia aislada de G-08. |
| Mock sobre cancelación y actualización canónica explícita | Cancelación → confirm; actualización → proceed | El mock incorpora heurísticas, no verifica ejecución ni reglas reales de negocio. |
| `ast.parse` de archivos Python | **17/17 parsearon** | Sintaxis válida; no comprueba imports, tipos o SDK. |

Para aislar el núcleo sin dependencias se cargaron sus submódulos con un contenedor de paquete temporal en memoria, evitando que `agentshield/__init__.py` importara el guard y YAML. No se sustituyó el SDK para declarar integración ni se modificaron módulos del repo. No se ejecutaron las otras seis pruebas con ese mecanismo.

Comando de suite intentado con runtime disponible:

```powershell
python -m pytest -q   # con el runtime de Python disponible en esa máquina
```

**No se afirma “14 passed”, “12/12 real” ni “E2E funciona”.** El README describe resultados esperados del arranque; esta revisión no los acredita como resultados de la sesión.

### 13.3 Limitaciones del benchmark

- Hay 12 casos, por debajo de los 16 iniciales recomendados en v2.1; ampliar a 30–50 es posterior a cerrar P0.
- `run_decider()` evalúa propuestas; no ejecuta tools ni mide efectos. Por tanto, no calcula guard success rate operacional.
- “Ataques que pasaron” solo considera casos con `expected == "deny"`; omite acciones inseguras etiquetadas `guide` o `confirm` que llegaran a `proceed`.
- Los falsos bloqueos se calculan sobre casos `expected == "proceed"`; no hay evaluación separada por rol, entorno, origen o conector.
- La latencia `ms` del benchmark incluye política, cliente, combinación y escritura de auditoría; no es latencia de inferencia aislada. El guard registra además `ans.latency_ms`, pero el reporte agregado no usa esa separación.
- `MockDecider` fija `latency_ms=1.0`; ese valor es sintético y no una medición de inferencia.
- El comparador Bedrock como juez sí tiene implementación con `converse`, pero no se ejecutó. Compara decisiones semánticas sin aplicar la misma política dura al juez, por lo que hay que aclarar qué se está comparando.
- Se extrae la primera palabra del juez sin un esquema estricto ni manejo de salida vacía/desconocida.
- El CSV no conserva etiqueta explícita de proveedor/modelo, checkpoint, hardware o configuración; el sufijo `-llm` no sustituye metadatos reproducibles.
- No hay resultados medidos versionados que respalden latencia, ahorro o accuracy. `docs/PROPUESTA.md` menciona aproximadamente 200 ms en GPU sin evidencia propia revisada.
- `.gitignore` ignora todos los JSONL salvo `bench/cases.jsonl` y todos los CSV; habrá que definir cómo versionar corpus nuevos y resultados públicos sanitizados.

## 14. Dependencias, CI y reproducibilidad

| Aspecto | Estado | Brecha / observación |
|---|---|---|
| Dependencias | `requirements.txt` con mínimos o sin versión | No hay lock ni versión exacta probada del SDK/Decider. |
| Python | CI usa 3.12 | No hay definición equivalente reproducible para ejecución local. |
| CI | Workflow pytest en push/PR | Existe; no se consultó su resultado remoto. No acredita AWS/E2E. |
| Instalación CI | Instala paquetes directamente sin `-r requirements.txt` | Puede usar una combinación distinta del arranque documentado; omite `strands-decider` explícito y no respeta el mínimo de `strands-agents`. |
| Paquetización | Sin `pyproject.toml` | No bloquea por sí sola una demo, pero falta empaquetado del patrón y entorno reproducible. |
| Configuración | `.env.example` presente | No se carga automáticamente, ver G-09. |
| SDK opcional | Fallback `InterventionHandler=object` | Permite pruebas puras sin SDK, pero `Proceed/Guide/Confirm/Deny` no quedan definidos si falta el import. Invocar el handler así no funciona. |
| Modelo generativo | ID por defecto en CLI y .env.example | Disponibilidad, permisos y región no comprobados. No se puede dar por válido por ser un string. |
| Decider real | URL configurable | Sin smoke test reproducible versionado, identidad del checkpoint ni respuesta capturada. |

La guía pide revisar firmas contra la versión realmente instalada. Esta sesión no tiene Strands instalado en el runtime inspeccionado; por tanto, `Confirm(response=...)`, `on_error`, `event.tool_use`, el formato de `state` y los schemas de preguntas quedan como **compatibilidad pendiente de prueba**, no como bugs confirmados del SDK.

## 15. Despliegue AWS y entrega

### 15.1 Qué hay

`docs/DIA1.md` explica preparación de cuenta, presupuesto, IAM, Bedrock, cuota GPU, comando de servidor Decider y una prueba HTTP. Son instrucciones útiles de preparación. El CI local del repositorio está definido y existe licencia Apache 2.0.

### 15.2 Qué no está acreditado o falta

- Runbook completo de servicio API/agente y Decider persistentes, reinicio, health, almacenamiento y logs.
- Evidencia E2E desde AWS con modelo generativo, checkpoint y resultado identificados.
- Configuración verificable de endpoint privado, IAM mínimo y acceso administrativo controlado.
- API staging registrada y GET real mediante el mismo guard.
- Capacidad/RAM/disco/latencia/costo medidos para el checkpoint.
- Persistencia durable de demo y recuperación tras reinicio.
- Instrucciones exactas de cleanup y registro de recursos activos.
- Enlaces verificados a artículo Builder Center y video público, y evidencia de envío/tags.

La infraestructura como código completa es **P2 según la guía**; no debe convertirse en prerrequisito artificial. Un despliegue manual reproducible con evidencia puede cerrar el objetivo antes que una plataforma de automatización extensa.

### 15.3 Requisitos de hackathon según la guía

| ID | Resultado de esta revisión |
|---|---|
| H-01 AWS funcional | No verificado. |
| H-02 Decider 2B decide significativamente | Cliente y preguntas presentes; ejecución real no acreditada. |
| H-03 Bedrock generativo | Constructor presente; invocación real no acreditada. |
| H-04 Artículo Builder Center | Publicación no verificada. |
| H-05 Repo público + licencia | Licencia Apache 2.0 presente; acceso público no verificado. |
| H-06 Patrón reutilizable | Parcial; falta entrega autocontenida/documentada. |
| H-07 Video | Publicación y duración no verificadas. |
| H-08 Tags | Mencionados en documentos; publicación efectiva no verificada. |
| H-09 Originalidad | No determinada por una revisión local de código. |
| H-10 Elegibilidad e inscripción | No verificadas; no son funcionalidades de software. |

## 16. Patrón reutilizable y documentación desalineada

### 16.1 Patrón

`questions.py` se describe como “el patrón” y README identifica `agentshield/` como reutilizable. Hay inyección por duck typing de Decider, Policy y AuditLog, una base adecuada para extraerlo.

Falta el entregable autocontenido de §7.7: README propio, contratos normalizados, integración probada, ejemplos de lectura permitida/bloqueada/aprobada, pruebas independientes, explicación de errores y ejemplo de adapter registrado. La política por defecto depende del YAML del repositorio y los ejemplos están ligados al alcance anterior.

**La carpeta exacta es secundaria; la reutilización comprobable y sus contratos son el objetivo.** Para seguir literalmente la guía, conviene publicar `patterns/grounded_tool_call_guard/` sin duplicar el motor de decisión.

### 16.2 Contradicciones internas que afectan al trabajo del equipo

| Documento / contrato | Situación | Impacto |
|---|---|---|
| `docs/PROPUESTA.md` | Declara integración con sistemas reales fuera de alcance | Contradice el GET staging P0 de v2.1. |
| `docs/BACKLOG.md` | Ocho tools, DynamoDB, comparativa de modelos, UI avanzada; sin tareas de conectores | Puede consumir el plazo en prioridades anteriores. |
| `docs/EQUIPO.md` | Congela GuardAnswers, Verdict, evaluate, auditoría y casos del alcance original | Añadir contexto, ejecución y trazabilidad requiere coordinar evolución de contratos. |
| README | Demo rápida con mock, escenarios originales y patrón en paquete principal | No explica las capacidades/límites nuevos ni el estado real de la integración. |
| `CLAUDE.md` | Referencias y reglas basadas en equipo/módulos actuales | No es un avance de código ni autoriza implementación automática por leerlo. |
| Propuesta de latencia | Aproximación ~200 ms en GPU | Debe identificarse como referencia/expectativa hasta medir el despliegue propio. |
| Guía vs documentos del equipo | SQLite vs DynamoDB; tres vs ocho tools; dos vs cuatro preguntas | Algunas diferencias son elecciones válidas; otras cambian el producto y deben resolverse explícitamente. |

No se recomienda romper contratos compartidos silenciosamente. Se puede introducir un contexto tipado opcional o una nueva capa de servicio conservando adapters temporales, pero la decisión debe quedar registrada y comunicada al equipo.

## 17. Backlog recomendado para cerrar el gap

Las prioridades siguientes son de esta revisión. Se apoyan en la guía, pero corrigen el orden donde hay riesgos de ejecución. **No son estimaciones de trabajo ya realizado.**

| Orden | Prioridad | Entrega concreta | Criterio de aceptación | Relación con guía |
|---|---|---|---|---|
| 1 | P0 | Alinear alcance y contratos | Documento/backlog común con tres tools canónicas, casos versionados y responsables. | AS-T03/07/18 |
| 2 | P0 | Entorno reproducible y modos explícitos | Versiones probadas, configuración cargada y modo real/mock visible; ejecución real falla si falta endpoint. | AS-T01/02 |
| 3 | P0 | Smoke real Bedrock + Decider + hook | Traza real con modelos, región y tool spy; una señal semántica cambia ejecución. | G0/G1, AS-T01/02/04 |
| 4 | P0 | Corregir reglas de decisión | Cancelación siempre confirma; propuesta inválida no pasa a aprobación; NaN/rangos/errores no escriben. | AS-T06, AS-06/07 |
| 5 | P0 | Dominio de pedidos + mock detrás de puerto | Dataset, lectura por ID, transiciones y cancelación por ID; estados/versiones probados. | AS-T03/07/18 |
| 6 | P0 | Identidad/contexto + ejecutor | Permiso y alcance revalidados al mutar; bypass de hook no concede autoridad. | §6.5, §9.4 |
| 7 | P0 | HITL verificable | Pedido intacto pendiente/rechazado/expirado; aprobación válida causa una sola mutación y registra efecto. | AS-T09, AS-04/08 |
| 8 | P0 | REST de lectura staging | GET real con mismo guard, mapeo tipado, destino administrado y secretos fuera de estado/logs. | AS-T19, AS-09 |
| 9 | P0 | Aislamiento y dry_run | Fixture solo mock; producción bloqueada; denegaciones y dry_run de escritura producen cero HTTP de mutación. | AS-T20, AS-10/11 |
| 10 | P0 | AWS demostrable + patrón + documentación | Runbook reproducido, E2E AWS y patrón independiente con ejemplos/tests. | AS-T05/10 |
| 11 | P0 | Entrega pública verificada | Repo/licencia/artículo/video/tags e inscripción comprobados por responsable. | AS-T11 |
| 12 | P1 | Mejorar consola y evaluación | Fuente/modelo/conector/efecto visibles; corpus >=16 y métricas con método. | AS-T12/13/14 |
| 13 | P1 | Escrituras REST staging | Solo con aprobación revalidada, idempotencia y conciliación; UNKNOWN no se reintenta a ciegas. | AS-T21, AS-12/13 |
| 14 | P2 | IaC/pipeline ampliado y comparativa | Después de cerrar P0; no retrasa artículo/video ni E2E. | AS-T16/17 |

### 17.1 Dependencias que conviene respetar

```text
Entorno y contratos ──→ smoke de integración real
          │
          └──→ dominio + puerto mock + política corregida
                              │
                              └──→ contexto + ejecutor + HITL
                                             │
                                             └──→ REST GET + aislamiento
                                                            │
                                                            └──→ E2E AWS + evidencia

Auditoría, patrón y documentación acompañan cada paso.
Artículo y video se preparan a partir de evidencia confirmada.
```

### 17.2 Recortes que conservan el objetivo

- Mantener HTML o usar CLI; React no es imprescindible.
- No añadir DynamoDB ni arquitectura distribuida para sustituir la persistencia mínima de demo.
- Posponer escrituras REST: GET staging sí es P0 en v2.1.
- Posponer benchmark contra otro LLM y curvas sofisticadas hasta medir el sistema real.
- Mantener los casos de inyección antiguos como regresión complementaria, sin confundirlos con los nuevos IDs.
- Dejar producción deshabilitada; prepararla en contrato no exige operarla durante la hackathon.

## 18. Pruebas de aceptación que faltan

Estas pruebas deben comprobar **efectos y llamadas**, además de acciones textuales:

| Área | Prueba mínima propuesta |
|---|---|
| Decisión | Hard deny con modelo favorable; cancelación con blast=0; intent bajo + hard confirm; límites exactos de umbral. |
| Salidas inválidas | NaN, infinito, fuera de rango, bool/string inesperado, campo ausente, JSON inválido, timeout. |
| AS-01/02 | Estado antes=después y contador de escritura cero tras propuesta indebida/no fundamentada. |
| AS-03 | Bedrock propone lectura, hook invocado, Decider real responde y pedido correcto llega al usuario. |
| AS-04 | Sin cambios pendiente; aprobación válida cambia solo pedido autorizado; rechazo no modifica. |
| Roles | Viewer denegado aunque scores sean favorables; identidad procede del servidor. |
| Aprobación | TTL, doble click, concurrencia, cambio de argumentos/política/versión invalidan ejecución. |
| REST GET | Servidor staging independiente recibe HTTP real; mapeo y request ID auditados. |
| No despacho | DENY/GUIDE/CONFIRM pendiente no llaman al backend; dry_run no manda HTTP de escritura. |
| Entorno | Fixture no resuelve REST; producción no se activa por prompt, args o UI. |
| Egreso | URL/path manipulados, redirect y destino no permitido se bloquean. |
| Errores upstream | Respuestas 401/403/404/409/429/5xx y schemas inválidos tienen resultado controlado. |
| Escritura REST P1 | Timeout tras posible efecto → UNKNOWN/conciliación; no repetir sin contrato de idempotencia. |
| Datos | Tokens/secretos sintéticos anidados no aparecen en prompt, log ni respuesta. |
| Operación | Reinicio conserva trazas/aprobaciones según contrato y no duplica ejecución. |

No hace falta crear tests que solo reproduzcan la implementación. Los casos anteriores validan invariantes de autoridad, ejecución y evidencia que hoy no están cubiertas.

## 19. Decisiones que requieren acuerdo de producto/equipo

1. **¿Se adopta v2.1 como alcance efectivo?** Este análisis la toma como objetivo solicitado para comparar; el repo documenta todavía otro alcance.
2. **¿Qué conservar de las cuatro preguntas?** Las adicionales pueden aportar valor, pero no deben decidir permisos o eliminar la aprobación obligatoria.
3. **¿Cómo evolucionan los contratos compartidos?** Contexto, eventos y ejecución requieren campos nuevos; conviene una transición explícita.
4. **¿Qué aprobación segura cabe en la demo?** CLI es viable si el SDK y las invariantes se prueban; UI puede esperar.
5. **¿Qué API staging controlada se usará?** Definir esquema, autenticación, conectividad y un recurso de prueba independiente de fixtures.
6. **¿Qué evidencia externa existe ya?** AWS, modelos, repo público, artículo/video y envío necesitan comprobación del responsable; no puede inferirse su estado del checklist.

## 20. Balance final

El avance real está en el **núcleo de evaluación y el esqueleto de integración**. La deuda principal está en **contratos de pedidos, autoridad de ejecución, aprobación verificable y conectores**, junto con la demostración real en AWS.

La ruta más eficiente es conservar los módulos puros y el cliente de inferencia, corregir primero las decisiones inseguras, introducir dominio/puerto/ejecutor y demostrar una lectura real y una cancelación mock aprobada. Después, incorporar el GET de staging con aislamiento y evidencia. Pulir UI o ampliar benchmarks antes de eso mejoraría la presentación de una cobertura que todavía no existe.

**Cambios de esta revisión:** se creó únicamente `analisis.md`; no se cambiaron contratos, código de negocio, configuración, dependencias, infraestructura ni documentos previos.
