# Equipo y contratos

**Actualizado:** 19 de octubre de 2026, según main 96aade8 y la rama de consolidación. Describe contratos actuales; no cambia firmas ni concede como implementadas las capacidades del plan.

## Responsabilidades propuestas

| Persona | Módulo principal | Próxima entrega |
|---|---|---|
| A / Carlos | Guard, política, patrón y artículo | Semántica de incertidumbre, coordinación de contexto/decisiones y patrón publicable. |
| B | Agente, dominio y conectores | Ejecutor/aprobaciones con A, lectura real y adapter REST. |
| C | Consola y auditoría | Fuente, correlación, efectos y resolución de aprobación por el servicio común. |
| D | AWS, evaluación y CI | Acceso/modelos reales, despliegue y evaluación separada de calibración. |

Estas responsabilidades no equivalen a asignaciones comprobadas en GitHub. La sincronización y las revisiones siguen siendo del equipo. El código y los issues se consultan en GitHub; no se requiere crear un tablero adicional.

## Contratos realmente implementados

```python
GuardAnswers(grounded, intent, injected, blast, latency_ms=None)
HardResult(verdict="proceed", reasons=())
Verdict(action, reason, hint="", checks={})
Shield.evaluate(user_request, tool_name, tool_input,
                tool_outputs=None, role="agente_soporte") -> Verdict
```

- grounded/intent/injected: números finitos 0…1. blast: número finito 0…2; no es un permiso.
- Acciones internas: proceed, guide, confirm, deny.
- Hard deny omite contexto/inferencia. En denegación previa o error sin respuesta, los cuatro scores y latency_ms quedan en null; threshold se conserva.
- La banda intermedia aún devuelve confirm; el plan pide aclaración para propuestas ambiguas. No presentar ese cambio como terminado.
- El rol es un parámetro de evaluación. El handler actual utiliza su valor por defecto; no está unido a identidad autenticada.

### Herramientas y dominio

```text
get_orders(order_id=None, status=None, limit=10)
update_order_status(order_id, new_status)
cancel_orders(order_ids, reason)          # exactamente un ID
```

OrderService valida argumentos; el conector valida estados y versiones al mutar. El puerto acepta expected_version opcional, pero el servicio actual no vincula esa versión a una aprobación ni revalida identidad.

MockOrderConnector usa memoria por defecto y admite archivo SQLite. El constructor conserva datos existentes y reset es explícito. No se expone una ruta pública de reset.

### Evento de auditoría actual

```text
decision_id, mode, tool, args, hard, answers,
latency_ms, verdict, reason, ts
```

AuditLog redacta campos sensibles recursivamente antes de escribir y publicar el evento. La estructura se conserva; las credenciales se sustituyen por [REDACTED]. No se infieren resultados de ejecución a partir del veredicto.

### Casos activos

```text
id=EVAL-*, spec_version=unified-1, use_case_id=AS-*, kind,
user_request, tool, args, tool_outputs, expected
```

EVAL-005 incluye policy_variants para viewer, con deny y expected_decider_calls=0. Las ejecuta el test de regresión de precheck; el runner de benchmark normal recorre siete registros con el rol por defecto. AS-* identifica el uso; EVAL-* identifica la entrada que acepta /api/run.

## Contratos futuros, todavía pendientes

- Contexto confiable: actor, organización, permisos, entorno, conector, correlación y dry_run; siempre construido por el servidor.
- Decisión vinculada a argumentos y ejecución; aprobación con identidad, TTL, versión y consumo único.
- Evento versionado con source, correlation_id, checkpoint/modelo, execution.status y efecto verificado.
- Registry y RestOrderConnector de lectura; producción bloqueada.

Estos cambios deben coordinarse con sus consumidores antes de modificar firmas. No existe un contrato v2 de contexto opcional implementado solo porque esté descrito en una rama documental.

## Flujo Git y validación

1. Crear rama desde main actualizado para cada entrega; conservar los cambios locales de otros integrantes.
2. Abrir PR con destino main explícito. Si se apila sobre otra rama, documentar destino y abrir/reapuntar la promoción posterior; Merged no implica presencia en main.
3. Pedir revisión humana. El check requerido se llama test; el workflow se llama tests. La configuración de protección se consulta en GitHub.
4. CI ejecuta Linux/Windows en pushes a main y PR dirigidos a main.
5. Cambios del guard llevan tests y actualización de un caso del corpus cuando corresponda. Tests con mock no acreditan inferencia real.
6. Actualizar [ESTADO.md](ESTADO.md) con comandos realmente ejecutados y límites.

Mantener datos ficticios y secretos fuera del repositorio. No reejecutar el generador inicial de issues sobre el repositorio ya poblado.
