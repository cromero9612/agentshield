# Guía para Windows

AgentShield corre en Windows, macOS y Linux. Los comandos del README y de [DIA1.md](DIA1.md) están escritos para
macOS/Linux; aquí van los equivalentes en **PowerShell**. La consola de fixtures y los tests funcionan **sin GPU y sin AWS** con modelos simulados. El agente generativo real requiere Bedrock.

## 1. Requisitos
| Qué | Cómo (PowerShell) |
|---|---|
| Python **3.10 o superior** (3.12 recomendado) | `winget install Python.Python.3.12` |
| Git | `winget install Git.Git` |
| GitHub CLI (`gh`) | `winget install GitHub.cli` y luego `gh auth login` |
| AWS CLI (solo quien use Bedrock) | `winget install Amazon.AWSCLI` y luego `aws configure` |
| `uv` (opcional, instala Python y paquetes más rápido) | `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"` |

Cierra y vuelve a abrir la terminal después de instalar.

## 2. Entorno y pruebas
```powershell
git clone https://github.com/cromero9612/agentshield.git
cd agentshield
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONUTF8 = "1"            # evita errores con tildes y símbolos en la consola
pytest -q
python -m bench.run_bench
uvicorn console.app:app --reload --port 8080
```
- Si PowerShell dice que la ejecución de scripts está deshabilitada:
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. En `cmd.exe` usa `.venv\Scripts\activate.bat`.
- `pip install -r requirements.txt` descarga PyTorch (varios GB). Es normal la primera vez.

## 3. Variables de entorno
Si aún no tienes `.env`, copia `.env.example` a `.env` y edítalo: el proyecto lo carga solo. No sobrescribas configuración existente. Con DECIDER_URL configurado, el benchmark consulta el endpoint real; sin esa URL usa mock. El cliente tiene actualmente un timeout de cinco segundos.
Para una sola sesión:
```powershell
$env:DECIDER_URL = "http://localhost:8000"      # PowerShell
python -m bench.run_bench
```
En `cmd.exe`: `set DECIDER_URL=http://localhost:8000`. La forma `DECIDER_URL=... python ...` **no** funciona en Windows.

## 4. Decider real en tu PC
`--device mps` es solo de Mac. En Windows:
```powershell
strands-decider serve StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 --device cpu --port 8000    # cualquier PC
strands-decider serve StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 --device cuda --port 8000   # GPU NVIDIA
```
Para usar GPU NVIDIA hace falta instalar PyTorch con CUDA (ver pytorch.org). En CPU es más lento, pero sirve para probar.
No es obligatorio levantarlo: uno del equipo puede compartir su `DECIDER_URL`, o se usa el Decider simulado.

Probar el servidor (en PowerShell, `curl` es un alias de otra cosa; usa `curl.exe` o `Invoke-RestMethod`):
```powershell
Invoke-RestMethod http://localhost:8000/v1/systemone -Method Post -ContentType "application/json" `
  -Body '{"state":"Help! My payouts have been failing","questions":{"u":{"type":"noul","instructions":"Is this urgent?"}}}'
```

## 5. Scripts `.sh`
`scripts/crear_issues.sh` necesita bash: usa **Git Bash** (viene con Git) o WSL.
Es para carga inicial y no deduplica. No volver a ejecutarlo sobre este repositorio ya poblado; para inspeccionar su salida usar únicamente DRY_RUN.
```bash
DRY_RUN=1 bash scripts/crear_issues.sh <owner>/agentshield
```
El repo fuerza saltos de línea LF en `.sh` (`.gitattributes`) para que bash no falle con CRLF.

## 6. Problemas frecuentes
| Síntoma | Causa y solución |
|---|---|
| `UnicodeEncodeError` al imprimir | `$env:PYTHONUTF8 = "1"` |
| `python` abre la Microsoft Store | Usa `py -3.12`, o desactiva los alias en *Configuración → Aplicaciones → Alias de ejecución* |
| `No matching distribution found for strands-agents` | Python menor a 3.10: `py -0p` lista las versiones instaladas |
| Rutas largas al clonar | `git config --global core.longpaths true` |
