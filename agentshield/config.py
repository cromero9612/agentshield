"""Carga de configuracion desde .env (sin dependencias extra).

Las variables que ya existen en el entorno tienen prioridad sobre el archivo.
"""

from __future__ import annotations

import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent


def load_env(*paths: str | Path) -> list[str]:
    """Lee archivos KEY=VALUE y los vuelca en os.environ sin pisar lo ya definido.

    Sin argumentos busca `.env` en el directorio actual y en la raiz del repo.
    Devuelve los nombres de las variables que cargo.
    """
    candidates = [Path(p) for p in paths] or [Path.cwd() / ".env", _ROOT / ".env"]
    loaded: list[str] = []
    for path in dict.fromkeys(candidates):
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip("\"'")
            if key and key not in os.environ:
                os.environ[key] = value
                loaded.append(key)
    return loaded
