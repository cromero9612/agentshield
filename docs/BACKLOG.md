# Backlog unificado

**Actualizado:** 19 de octubre de 2026. Referencia de código: main 96aade8; la consolidación de código visual y tests Strands se entrega en un PR propio. Los estados describen evidencia, no tareas automáticamente cerradas en GitHub.

Entrega interna objetivo del equipo: 22 de octubre. El cierre e inscripción se verifican con las reglas del evento. Los issues existentes #1…28 fueron creados con el alcance anterior: hay que revisar sus criterios, sin duplicarlos ni inferir que un issue abierto significa ausencia de código.

**No reejecutar scripts/crear_issues.sh sobre este repositorio.** Es una utilidad de carga inicial sin deduplicación. El formato diario de las tablas sigue siendo compatible con su lectura, pero cambiar este documento no sincroniza ni cierra issues externos.

## Estado de las etapas

| Etapa | Estado comprobado | Gate pendiente |
|---|---|---|
| U-01: alcance/contratos | Tres tools y casos unified-1 en código; documentación alineada en esta consolidación. | Coordinar los contratos futuros de contexto y ejecución. |
| U-02: inferencia real | Constructor de agente/cliente HTTP; tests de hook con modelos simulados recuperados. | Bedrock + Decider real + hook + tool en ejecución documentada. |
| U-03: dominio | Diez pedidos, tres tools, puerto/mock, estados/versiones/historial; persistencia de archivo corregida. | Conectar contexto autorizado y almacenamiento del servicio según despliegue. |
| U-04: política | Hard deny previo, errores auditados, números válidos y cancelación siempre confirmada. | Alinear permisos/catálogo y aclaración ante incertidumbre. |
| U-05: ejecución/aprobación | Confirmación CLI, validación de negocio. | Ejecutor, identidad, aprobación durable, TTL, versión y consumo único. |
| U-06: REST/aislamiento | Puerto disponible. | GET staging, registry, secretos, dry_run y producción bloqueada. |
| U-07: consola/evaluación | Evaluación de fixtures, siete casos mock, auditoría y diseño; no ejecución web. | Fuente, efectos, correlación, corpus >=16 y evaluación real. |
| U-08: publicación | Licencia y documentos iniciales. | Patrón autónomo, runbook AWS, artículo, video y enlaces verificados. |

## Lun 19 · Consolidación y evidencia mínima

| Persona | Tarea |
|---|---|
| A | Revisar la promoción del código del PR #35 y los tests #36; alinear documentos al código sin traer estados históricos como hechos actuales. |
| B | Ejecutar lectura con Bedrock y Decider real por CLI; registrar modelo, región, propuesta, intervención y pedido devuelto. |
| D | Resolver acceso/modelo/cuotas y conectividad del endpoint Decider; documentar resultados reales sin esperar una GPU para todo el trabajo. |
| C | Revisar la consola recuperada; especificar fuente/efecto y separar evaluación visual de ejecución. |

## Mar 20 · Ejecutor y aprobación

| Persona | Tarea |
|---|---|
| A | Definir contexto confiable y decisión vinculada; no convertir incertidumbre en operación aprobable sin aclaración. |
| B | Implementar ejecutor y aprobación durable: pedido intacto pendiente/rechazado, TTL, hash de argumentos, versión y consumo único. |
| C | Conectar aprobación al servicio común; evitar una ruta de escritura directa desde el botón. |
| D | Probar AS-06/07/08 con contadores y efectos; comprobar reinicio, permisos y concurrencia. |

## Mié 21 · Integración staging y evaluación

| Persona | Tarea |
|---|---|
| B | Implementar RestOrderConnector GET contra API de staging independiente de fixtures, con mapeo tipado. |
| A | Registry/entorno administrados, estado autorizado y límites; producción apagada. |
| D | AS-09/10/11: HTTP real, cero escrituras en dry_run y cero llamadas de negocio ante destino/alcance inválido. |
| C | Mostrar fuente, conector, inferencia, correlación y efecto; adaptar formulario de ataque a notas de pedido. |
| Todos | Preparar >=16 entradas etiquetadas; separar calibración y evaluación. No comparar las métricas del catálogo antiguo como si fuera el mismo corpus. |

## Jue 22 · Entrega verificable

| Persona | Tarea |
|---|---|
| A | Documentar el patrón reutilizable, finalizar artículo y revisar tags/inscripción. |
| D | Runbook de instalación/despliegue/cleanup y evidencia E2E desde AWS; revisar acceso y costos reales. |
| C | Grabar video breve con fuente explícita, lectura real, GET staging y aprobación mock. |
| B | Ensayo reproducible y revisión de enlaces públicos con otro integrante. |

## Recortes y condiciones

Posponer escrituras REST, comparativa avanzada de LLM, gráficos sofisticados e IaC completa hasta cerrar P0. Mantener lectura REST de staging como requisito del alcance v2.1; si se recorta, declarar el desvío.

No hay tareas obligatorias de DynamoDB, inventario, reembolsos o correo. La presentación usa el catálogo real de tres tools. Las capturas históricas y los tests con modelos simulados no sustituyen evidencia de inferencia real.
