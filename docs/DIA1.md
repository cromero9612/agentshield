# Día 1: dejar todo listo

> Avance real de este día y pendientes: ver [ESTADO.md](ESTADO.md).

Orden recomendado. Lo marcado con **(A)** lo hace Carlos, **(D)** la Persona D, **(Todos)** cada uno.

## 0. Antes de todo (A, 15 min)

- [ ] Abrir la pestaña **Rules** del hackathon y confirmar: que Guatemala es elegible, si se permiten equipos de 4 y cómo se registra un equipo.
- [ ] Cada uno crea o completa su perfil de **AWS Builder Center** (requisito para participar).

## 1. GitHub (A, 30 min)

1. Crear una organización gratuita en GitHub (por ejemplo `agentshield-team`) o usar tu cuenta personal.
2. Crear el repo `agentshield`, **público**, con licencia **Apache 2.0** marcada al crearlo.
3. Subir el contenido de este paquete:
   ```bash
   git clone https://github.com/<org>/agentshield.git && cd agentshield
   # copiar aquí los archivos del paquete (sin sobrescribir LICENSE)
   git add . && git commit -m "Base del proyecto" && git push
   ```
4. *Settings → Collaborators*: invitar a B, C y D.
5. *Settings → Branches*: proteger `main` (requiere PR y que pase el check `tests`).
6. Crear el tablero: *Projects → New project → Board*, y vincularlo al repo.
7. Crear issues, etiquetas y milestones de golpe (requiere [GitHub CLI](https://cli.github.com) con `gh auth login`):
   ```bash
   bash scripts/crear_issues.sh <org>/agentshield
   ```

## 2. Cada miembro (Todos, 20 min)

```bash
git clone https://github.com/<org>/agentshield.git && cd agentshield
python -m venv .venv && source .venv/bin/activate   # Python 3.10+ (en macOS: uv venv --python 3.12 .venv)
pip install -r requirements.txt
pytest -q && python -m bench.run_bench
```
Si ves `14 passed` y `12/12`, ya puedes trabajar aunque AWS aún no esté listo.

## 3. AWS (D, 1–2 h)

1. Crear la cuenta de AWS con tarjeta. Activar **MFA** en el usuario raíz y no usarlo más.
2. **Presupuesto**: *Billing → Budgets → Create budget*, por ejemplo USD 50 al mes, con alerta al 50 %, 80 % y 100 % a los 4 correos.
3. **IAM Identity Center** o usuarios IAM: uno por persona, con permisos mínimos (Bedrock invoke, EC2 en la región elegida).
4. **Región**: `us-east-1` (más modelos disponibles).
5. **Bedrock**: en la consola de Bedrock, revisar *Model access* y habilitar el modelo de Anthropic que usaremos. Para Anthropic puede pedir un formulario corto de caso de uso; llenarlo el día 1 porque puede tardar.
6. Probar Bedrock desde una laptop:
   ```bash
   aws configure   # con las llaves del usuario IAM
   python -c "import boto3;print(boto3.client('bedrock-runtime').converse(modelId='global.anthropic.claude-sonnet-4-6',messages=[{'role':'user','content':[{'text':'hola'}]}])['output'])"
   ```
7. **Cuota de GPU**: *Service Quotas → EC2 → Running On-Demand G and VT instances*. Las cuentas nuevas suelen tener 0; pedir al menos 4 vCPU **hoy** porque la aprobación puede tardar.

## 4. Decider (D, cuando llegue la cuota)

```bash
# EC2 g6.xlarge o g5.xlarge con una AMI de Deep Learning (Ubuntu)
pip install "strands-decider[cuda]"
strands-decider serve StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 --host 0.0.0.0 --port 8000
```
- Security group: abrir el puerto 8000 **solo** a las IP del equipo.
- Apagar la instancia cada noche.
- Mientras llega la cuota: correr el mismo comando en una laptop con GPU, en una Mac (`--device mps`) o en CPU (`--device cpu`, más lento pero sirve para probar).
- Valida el nombre exacto del modelo y las flags en el README del repo oficial `strands-labs/strands-decider`.

Probar:
```bash
curl -s http://IP:8000/v1/systemone -H 'Content-Type: application/json' \
  -d '{"state":"Help! My payouts have been failing","questions":{"u":{"type":"noul","instructions":"Is this urgent?"}}}'
```
Luego cada uno pone `DECIDER_URL=http://IP:8000` en su `.env` y corre `python -m bench.run_bench`.

## Al final del día 1

- [ ] Repo con CI en verde y los 4 con acceso
- [ ] Tablero con todos los issues asignados
- [ ] Bedrock responde desde al menos una laptop
- [ ] Cuota de GPU solicitada (o Decider ya corriendo)
