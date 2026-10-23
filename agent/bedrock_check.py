"""Diagnostico de Bedrock: que modelos responden en ESTA cuenta, en que region y por que falla el resto.

    # 1) credenciales: una clave de API de Bedrock (consola de Bedrock -> Claves de API) o `aws configure`
    export AWS_BEARER_TOKEN_BEDROCK=...            # PowerShell: $env:AWS_BEARER_TOKEN_BEDROCK="..."
    # 2) correr
    python -m agent.bedrock_check                  # prueba us-east-1 y us-west-2
    python -m agent.bedrock_check --regions us-east-1,eu-west-1,ap-southeast-1

Hace una llamada minima (maximo 8 tokens de salida) a cada modelo de texto disponible y clasifica la respuesta. Para los que
responden prueba ademas el uso de herramientas, que es lo que necesita el agente. Al final imprime las lineas de `.env`.
No guarda ni imprime credenciales.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable

from botocore.exceptions import ClientError, NoCredentialsError

# Candidatos si no se puede listar (la clave de API puede no tener permiso de listado).
FALLBACK_MODELS = [
    "us.amazon.nova-micro-v1:0", "us.amazon.nova-lite-v1:0", "us.amazon.nova-pro-v1:0",
    "global.anthropic.claude-sonnet-4-6", "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "us.anthropic.claude-sonnet-4-5-20250929-v1:0", "us.meta.llama3-3-70b-instruct-v1:0",
    "us.mistral.pixtral-large-2502-v1:0", "us.deepseek.r1-v1:0", "us.writer.palmyra-x5-v1:0",
]
TOOL_SPEC = {"tools": [{"toolSpec": {"name": "ping", "description": "Responde que funciona.",
                                      "inputSchema": {"json": {"type": "object", "properties": {}}}}}]}


def classify(exc: Exception) -> tuple[str, str]:
    """(codigo corto, explicacion en español) para un error de Bedrock."""
    if isinstance(exc, NoCredentialsError):
        return "SIN_CREDENCIALES", "no hay credenciales: define AWS_BEARER_TOKEN_BEDROCK o corre `aws configure`"
    if not isinstance(exc, ClientError):
        return "ERROR", f"{type(exc).__name__}: {exc}"[:160]
    err = exc.response.get("Error", {})
    code, msg = err.get("Code", ""), err.get("Message", "")
    low = msg.lower()
    if code == "ThrottlingException" or "too many tokens" in low or "quota" in low:
        return "CUOTA", "cuota en 0 o agotada (en cuentas nuevas suele ser 0): pedir aumento, pasar a plan de pago o usar otra cuenta"
    if code == "AccessDeniedException":
        if "being verified" in low:
            return "VERIFICANDO", "la cuenta sigue en verificacion de AWS"
        if "not available for this account" in low or "not available" in low:
            return "NO_DISPONIBLE", "el modelo no esta disponible para esta cuenta"
        return "SIN_PERMISO", "la credencial no tiene permiso para invocar este modelo"
    if code in ("ValidationException", "ResourceNotFoundException"):
        return "NO_APLICA", "el modelo no admite esta forma de invocacion o no existe en esta region"
    return code or "ERROR", msg[:160]


def _discover(bedrock) -> list[str]:
    ids: list[str] = []
    try:
        for p in bedrock.list_inference_profiles(typeEquals="SYSTEM_DEFINED", maxResults=100).get("inferenceProfileSummaries", []):
            ids.append(p["inferenceProfileId"])
        for m in bedrock.list_foundation_models(byOutputModality="TEXT", byInferenceType="ON_DEMAND").get("modelSummaries", []):
            ids.append(m["modelId"])
    except Exception:  # noqa: BLE001 - sin permiso de listado se usa la lista de candidatos
        return list(FALLBACK_MODELS)
    seen, out = set(), []
    for i in ids:
        if i not in seen and "embed" not in i and "image" not in i and "rerank" not in i:
            seen.add(i)
            out.append(i)
    return out or list(FALLBACK_MODELS)


def probe(runtime, model_id: str) -> dict:
    """Prueba un modelo. Devuelve {status, detail, tools}. Nunca lanza."""
    msgs = [{"role": "user", "content": [{"text": "Responde solo: ok"}]}]
    try:
        runtime.converse(modelId=model_id, messages=msgs, inferenceConfig={"maxTokens": 8})
    except Exception as exc:  # noqa: BLE001
        status, detail = classify(exc)
        return {"model": model_id, "status": status, "detail": detail, "tools": None}
    try:
        runtime.converse(modelId=model_id, messages=[{"role": "user", "content": [{"text": "Usa la herramienta ping."}]}],
                         toolConfig=TOOL_SPEC, inferenceConfig={"maxTokens": 32})
        tools = True
    except Exception:  # noqa: BLE001
        tools = False
    return {"model": model_id, "status": "OK", "detail": "responde", "tools": tools}


def scan(make_client: Callable[[str, str], object], regions: list[str], limit: int) -> dict[str, list[dict]]:
    results: dict[str, list[dict]] = {}
    for region in regions:
        try:
            models = _discover(make_client("bedrock", region))[:limit]
            runtime = make_client("bedrock-runtime", region)
        except Exception as exc:  # noqa: BLE001
            code, detail = classify(exc)
            results[region] = [{"model": "(region)", "status": code, "detail": detail, "tools": None}]
            continue
        results[region] = [probe(runtime, m) for m in models]
    return results


def recommend(results: dict[str, list[dict]]) -> tuple[str, str] | None:
    """Mejor (region, modelo): el que responde y soporta herramientas; primero los de Anthropic, luego Nova."""
    ok = [(r, x["model"]) for r, rows in results.items() for x in rows if x["status"] == "OK" and x["tools"]]
    ok.sort(key=lambda rm: (0 if "anthropic" in rm[1] else 1 if "nova" in rm[1] else 2, rm[0], rm[1]))
    return ok[0] if ok else None


def _client_factory(service: str, region: str):
    import boto3
    return boto3.client(service, region_name=region)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--regions", default="us-east-1,us-west-2")
    p.add_argument("--limit", type=int, default=40, help="maximo de modelos a probar por region")
    a = p.parse_args()
    if not os.getenv("AWS_BEARER_TOKEN_BEDROCK"):
        import boto3
        if boto3.Session().get_credentials() is None:
            print("No hay credenciales. Opciones:\n  1) Consola de Bedrock -> Claves de API -> crear una, y definir "
                  "AWS_BEARER_TOKEN_BEDROCK\n  2) `aws configure` con las llaves de un usuario IAM con permiso de Bedrock")
            return 2
    results = scan(_client_factory, [r.strip() for r in a.regions.split(",") if r.strip()], a.limit)
    for region, rows in results.items():
        print(f"\n== {region}")
        for x in sorted(rows, key=lambda x: (x["status"] != "OK", x["model"])):
            tools = "" if x["tools"] is None else (" · herramientas: si" if x["tools"] else " · herramientas: NO")
            print(f"  {x['status']:15} {x['model']:58} {x['detail'] if x['status'] != 'OK' else 'responde' + tools}")
    best = recommend(results)
    if best:
        print(f"\nFunciona. Agrega a .env:\n  AGENT_MODEL_PROVIDER=bedrock\n  AWS_REGION={best[0]}\n  BEDROCK_MODEL_ID={best[1]}")
        return 0
    print("\nNingun modelo respondio con herramientas. Revisa los codigos de arriba (CUOTA suele significar cuenta nueva).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
