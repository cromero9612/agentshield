# Estado del proyecto

> Documento vivo. Quien avance algo lo actualiza en el mismo PR.
> **Última actualización:** domingo 18 de octubre de 2026 (Día 2) · **Responsable del documento:** Persona A (Carlos).

Este documento responde tres preguntas: **qué está hecho, qué falta y qué sigue**. Está escrito para que alguien que
llega de cero (o una sesión nueva de Claude Code) retome el trabajo sin preguntar nada.
Para el contexto del producto, lee antes [PROPUESTA.md](PROPUESTA.md), [EQUIPO.md](EQUIPO.md) y [BACKLOG.md](BACKLOG.md).

## 1. Resumen ejecutivo

| Área | Estado |
|---|---|
| Código base (guard, tienda, consola, benchmark) | Funciona sin AWS con el Decider simulado |
| Tests | 36 pasan |
| Benchmark (mock) | 12/12 aciertos, 0 ataques que pasan, 0 falsos bloqueos |
| Repo GitHub | Público, Apache 2.0, `main` protegido, CI en verde |
| Issues | 28 creados, con etiqueta por persona y milestone por día |
| Cuenta AWS | Creada (plan gratuito), MFA activo, presupuesto pendiente de confirmar |
| Bedrock | Bloqueado temporalmente por la verificación de cuenta de AWS |
| Decider real | Pendiente: cuota de GPU solicitada, sin respuesta aún |
| Invitación de compañeros al repo | Pendiente |

**Fechas.** Entrega interna: **jueves 22 de octubre**. Cierre oficial: 23 de octubre, 11:59 PM PDT
(12:59 AM del sábado 24 en Guatemala). El viernes 23 es colchón.

## 2. Lo que ya está hecho

### 2.1 Repositorio y GitHub
- Repo: https://github.com/cromero9612/agentshield (público, licencia **Apache 2.0**, el `LICENSE` lo creó GitHub).
- Commit base "Base del proyecto" subido a `main`.
- **Ruleset `protect-main`** (activo sobre la rama por defecto):
  - No se puede borrar `main` ni hacer force push.
  - Todo cambio entra por **Pull Request con 1 aprobación**.
  - Check requerido: **`test`** (es el nombre del *job* en [`.github/workflows/ci.yml`](../.github/workflows/ci.yml);
    el workflow se llama `tests`, pero el check que GitHub reporta es `test`).
  - Los administradores del repo pueden saltarse la regla (así Carlos no queda bloqueado mientras no haya revisores).
- **28 issues** generados desde `docs/BACKLOG.md` con `scripts/crear_issues.sh`. Etiquetas: `persona-a` a `persona-d` y
  `todos`. Un milestone por día (Sáb 17 a Jue 22). **No están asignados a personas** todavía.
- No se usará tablero (GitHub Projects): el seguimiento se hace con issues y milestones.

### 2.2 Entorno local verificado
- Se necesita **Python 3.10 o superior** (`strands-agents` no instala en 3.9, que es el `python3` por defecto de macOS).
- Instalado con `uv` (Python 3.12) y funciona. Ver la sección 6 para reproducirlo.
- `pytest -q` → 36 passed. `python -m bench.run_bench` → 12/12 con Decider simulado.
- La consola (`uvicorn console.app:app`) levanta y responde 200 en `/`; expone `/api/cases`, `/api/run` y `/api/events`.
- El agente (`python -m agent.run_agent`) **no se ha probado**: requiere Bedrock.

### 2.3 Verificación contra las APIs instaladas
Se comprobó en el entorno virtual, no por suposición (regla de `CLAUDE.md`):
- `strands.interventions` (Strands 1.61.1) exporta `Proceed`, `Guide`, `Confirm`, `Deny`, `Transform` e
  `InterventionHandler`, con la firma que usa `agentshield/guard.py`. `on_error` devuelve `"deny"` (fail-closed).
- El servidor del Decider (`strands-decider` 0.1.0, `POST /v1/systemone`) responde `{"answers": {...}, "latency_ms": ...}`
  con `noul` → `float` y `score` → `score` + `confidence`. Coincide con `HttpDecider` en
  `agentshield/decider_client.py`.

### 2.4 Correcciones hechas al paquete original
- `scripts/crear_issues.sh` fallaba en macOS: usaba `declare -A` (arreglos asociativos), que el bash 3.2 del sistema no
  soporta. Se reemplazó por una comprobación portable. Ahora corre en macOS y Linux.

### 2.5 Cuenta de AWS (Persona D tendrá que replicar lo que falte)
- Cuenta creada con el nombre `agent-hackathon`, **plan gratuito** de 6 meses (los créditos cubren los costos; no se cobra
  nada mientras duren).
- **MFA del usuario raíz: activo.**
- Región de trabajo: **`us-east-1` (N. Virginia)**.
- **Bedrock:** el formulario de caso de uso de Anthropic ya se envió (proyecto `AgentShield`, usuarios internos,
  datos ficticios). Al probar el *playground* con Claude Sonnet 5.5 aparece
  `AccessDeniedException: Your account is currently being verified`. Es la verificación de cuentas nuevas de AWS,
  normalmente tarda menos de 2 horas.
- **Cuota de GPU:** se solicitó aumento de *Running On-Demand G and VT instances* a **4 vCPU** en `us-east-1`
  (el valor aplicado es 0, que es lo normal en una cuenta nueva). Estado: pendiente.

### 2.6 Análisis de brechas y plan de convergencia (llegaron el 18 de octubre)
Un compañero comparó el repo con la guía interna de implementación v2.1 y dejó dos documentos, ya en `docs/`:
- [analisis.md](analisis.md): diagnóstico de brechas del código frente a la guía (hallazgos G-01 a G-09, matriz de cumplimiento, backlog P0/P1/P2).
- [integracion.md](integracion.md): **propuesta** de un solo alcance (tres herramientas de pedidos, un guard, una política, SQLite, GET real a una API de staging). Está **pendiente de aprobación del equipo** y no está implementada.

La guía v2.1 en sí **no está en el repo**; los dos documentos la citan como especificación.

**Verificación propia (18-oct, Python 3.12, `main` en `22d1311`).** El análisis no pudo ejecutar `pytest` ni instalar Strands; aquí sí se ejecutó:

| Hallazgo | Resultado al reproducirlo |
|---|---|
| G-01 `combine(GuardAnswers(.95,.95,0,0), HardResult())` | **`proceed`**: una cancelación con scores optimistas pasa sin confirmación |
| G-02 intención baja (`.05`) + regla dura `confirm` | **`confirm`**: un caso que debía corregirse (`guide`) queda aprobable |
| G-03 respuestas `NaN` o fuera de rango | **`proceed`**: una salida inválida del Decider permite la acción |
| G-08 `audit.minimize` | Solo enmascara 4 claves de primer nivel y deja 4 caracteres; no redacta anidados ni `Authorization` |
| G-09 `.env` | Confirmado: ningún módulo carga `.env` (no hay `dotenv`); `DECIDER_URL` en `.env` **no tiene efecto** |
| `pytest -q` | 14 passed (el análisis no pudo correrlo) |

Los demás hallazgos (G-04 a G-07) se leyeron en el código pero no se reprodujeron todavía.

## 3. Lo que falta (checklist)

### 3.1 Inmediato (bloquea a otros)
- [ ] **Invitar a B, C y D** al repo (*Settings → Collaborators*). *Responsable: A.*
- [ ] **Asignar los 28 issues** a sus personas: `gh issue edit N --add-assignee <usuario>`. *A.*
- [ ] **Confirmar el presupuesto mensual de AWS** (USD 50, alertas al 50/80/100 % a los correos del equipo). *D/A.*
- [ ] **Esperar la verificación de la cuenta AWS** y volver a probar Bedrock en el *playground*. Si pasan más de 2 horas,
      escribir a `aws-verification@amazon.com` con el número de cuenta.
- [ ] **Seguimiento de la cuota de GPU** en *Service Quotas → Historial de solicitudes*. Si exigen un plan de pago,
      hacer el *upgrade* desde *Billing* (conviene confirmar que se conservan los créditos).
- [ ] Cada compañero crea su perfil en **AWS Builder Center** (requisito para participar).
- [ ] Abrir la pestaña **Rules** del hackathon y confirmar: elegibilidad desde Guatemala, equipos de 4 y registro del
      equipo. *A (issue #1).*

### 3.1b Decisiones de producto que bloquean el rumbo
- [ ] **¿Se adopta el alcance de [integracion.md](integracion.md)?** Implica pasar de 8 herramientas a 3 (`get_orders`,
      `update_order_status`, `cancel_orders`), nuevos IDs de casos AS y cambios en los contratos de [EQUIPO.md](EQUIPO.md).
      Los contratos **no se cambian sin acuerdo de los 4**. *Decide: A con B, C y D.*
- [ ] Compartir la guía v2.1 con el equipo (o resumirla en `docs/`), porque es la especificación en disputa.
- [ ] Sin importar la decisión anterior, hay **correcciones de seguridad del guard** que no dependen del alcance
      (G-01, G-02, G-03, G-04, G-09). Son del módulo `agentshield/` (Persona A) y cada una lleva test y caso en el benchmark.

### 3.2 Por persona (resumen; el detalle está en los issues y en [BACKLOG.md](BACKLOG.md))
| Persona | Siguiente paso concreto |
|---|---|
| **A** · Guard | Levantar el Decider real (en Mac con `--device mps` si no hay GPU) y probar las 4 preguntas; comparar `guard.py` con `examples/strands/` del repo oficial `strands-labs/strands-decider` |
| **B** · Agente y tienda | Probar `agent/run_agent.py` en cuanto Bedrock responda; escenarios AS-01 a AS-06 por CLI |
| **C** · Consola | Revisar la consola local; boceto de la pantalla del video |
| **D** · AWS y benchmark | IAM por persona con permisos mínimos; EC2 con GPU y `strands-decider serve`; compartir `DECIDER_URL` |
| **Todos** | 10 casos nuevos cada uno en `bench/cases.jsonl` (ataques a módulos que no hicieron). Hoy hay 12 casos; el plan pide ~50 |

### 3.3 Decisiones abiertas
| Tema | Contexto | Propuesta |
|---|---|---|
| **Modelo de Bedrock** | El paquete usa `global.anthropic.claude-sonnet-4-6` (solo un valor por defecto del paquete original, no una elección medida). El catálogo de la cuenta ofrece también Sonnet 5.5, Haiku 5.5, Opus 5.5 y otros | Agente: un modelo rápido y barato. Juez del benchmark: uno más fuerte, el mismo en todas las corridas. Se cambia con `BEDROCK_MODEL_ID` y `JUDGE_MODEL_ID` sin tocar código. Decidir en equipo cuando Bedrock responda |
| **Plan de AWS** | El plan gratuito puede no permitir EC2 con GPU | Seguir en gratuito; hacer *upgrade* solo si la GPU lo exige |
| **Revisión de PR** | `protect-main` pide 1 aprobación | Rotación A→B→C→D→A, como en [EQUIPO.md](EQUIPO.md) |

## 4. Riesgos y plan B

| Riesgo | Plan B |
|---|---|
| La cuota de GPU tarda o se deniega | Correr `strands-decider serve` en una Mac (`--device mps`) o en CPU (`--device cpu`). Más lento, pero sirve para probar |
| Bedrock sigue bloqueado | Todo el desarrollo del guard, la consola y el benchmark funciona con el Decider simulado |
| El Decider simulado no sirve para el artículo | Es cierto: el benchmark imprime *"MOCK (no vale para el artículo)"*. Las métricas finales deben salir con el Decider real |
| Costos de AWS | Presupuesto con alertas; apagar la EC2 cada noche; nunca dejar recursos encendidos |
| Secretos en el repo | `.env` y `*.jsonl` (excepto `bench/cases.jsonl`) están en `.gitignore`. No subir llaves ni IDs de cuenta |

## 5. Reglas de trabajo (resumen de `CLAUDE.md` y `EQUIPO.md`)
- Una rama por tarea: `<persona>/<tema>` (`a/decider-local`, `b/agente-bedrock`). Nunca directo a `main`.
- PR pequeño con `Closes #N`, revisado por otra persona; el CI (`test`) debe pasar.
- **No cambiar los contratos** de [EQUIPO.md](EQUIPO.md) (`GuardAnswers`, `Verdict`, `Shield.evaluate`, evento de auditoría,
  formato de casos) sin avisar: los demás dependen de ellos.
- `combine()` es una función pura: el Decider solo puede **endurecer** una decisión, nunca relajar una regla dura. Todo
  cambio ahí lleva test.
- Si cambia el comportamiento del guard, se agrega o ajusta un caso en `bench/cases.jsonl`.
- Datos y empresa ficticios (ElectroNova). Nunca datos reales ni credenciales en el repo.

## 6. Cómo reproducir el entorno

```bash
git clone https://github.com/cromero9612/agentshield.git && cd agentshield

# Opción A: con uv (recomendada en macOS, donde python3 es 3.9)
uv venv --python 3.12 .venv && source .venv/bin/activate
uv pip install -r requirements.txt

# Opción B: con Python 3.10+ ya instalado
python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

pytest -q                        # 36 passed
python -m bench.run_bench        # 12/12 con el Decider simulado
uvicorn console.app:app --reload --port 8080
```

Con el Decider real: copia `.env.example` a `.env` y pon `DECIDER_URL=http://IP:8000`.
Con el agente real (requiere Bedrock): `python -m agent.run_agent "Resumeme los tickets que entraron hoy"`.

## 7. Registro de cambios de este documento
| Fecha | Cambio |
|---|---|
| 2026-10-17 | Versión inicial: estado al cierre del Día 1 |
| 2026-10-18 | Se incorporan `analisis.md` e `integracion.md`, verificación de G-01/02/03/08/09 y decisiones pendientes |
