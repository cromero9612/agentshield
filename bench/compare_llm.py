"""Decider 2B frente a un LLM como juez, sobre los MISMOS casos de prueba (los que no se usaron para calibrar).

    DECIDER_URL=http://localhost:8000 python -m bench.compare_llm                 # juez: Ollama local (OLLAMA_MODEL, por defecto qwen3:8b)

El juez recibe el mismo contexto y debe responder una palabra (proceed, guide, confirm o deny), igual que `bench.run_bench
--llm-judge` pero contra Ollama. NO es Bedrock. El juez no aplica las reglas duras ni la comprobacion exacta de IDs; se
compara la decision semantica contra la del guard completo y tambien contra el Decider sin esas reglas (misma entrada).
Resultado en bench/results/llm_judge.json. Una sola corrida: no son tasas ni intervalos.
"""

from __future__ import annotations

import json
import os
import statistics
import time

from bench.calibrate import CACHE, evaluate, fit, load
from bench.run_bench import JUDGE_PROMPT

VERDICTS = ("proceed", "guide", "confirm", "deny")


def judge(client, model: str, case: dict) -> tuple[str, float]:
    prompt = JUDGE_PROMPT.format(user=case["user_request"], outputs=case["tool_outputs"], tool=case["tool"],
                                 args=json.dumps(case["args"], ensure_ascii=False))
    t0 = time.perf_counter()
    r = client.chat(model=model, messages=[{"role": "user", "content": prompt}], think=False,
                    options={"temperature": 0, "num_predict": 8})
    ms = (time.perf_counter() - t0) * 1000
    words = (r["message"]["content"] or "").strip().lower().replace(".", " ").split()
    return (words[0] if words and words[0] in VERDICTS else "invalid"), ms


def main() -> None:
    import ollama

    model = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    client = ollama.Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    cases = load()
    cached = json.loads(CACHE.read_text(encoding="utf-8"))["answers"]
    th, _ = fit(cases, cached)
    test = [c for c in cases if c["split"] == "test"]
    judge(client, model, test[0])  # calentar el modelo (carga en memoria)
    rows = [{"id": c["id"], "expected": c["expected"], "kind": c["kind"], **dict(zip(("got", "ms"), judge(client, model, c)))} for c in test]
    attacks = [r for r in rows if r["expected"] == "deny"]
    benign = [r for r in rows if r["expected"] == "proceed"]
    block = {"guide", "confirm", "deny"}
    llm = {"model": model, "exact": sum(r["got"] == r["expected"] for r in rows), "n": len(rows),
           "attacks_denied": sum(r["got"] == "deny" for r in attacks), "attacks_total": len(attacks),
           "attacks_leaked": [r["id"] for r in attacks if r["got"] not in block],
           "false_blocks": [r["id"] for r in benign if r["got"] != "proceed"], "benign_total": len(benign),
           "invalid": sum(r["got"] == "invalid" for r in rows),
           "ms_median": round(statistics.median(r["ms"] for r in rows)), "ms_max": round(max(r["ms"] for r in rows))}
    dec = evaluate(test, cached, thresholds=th)
    d_ms = [cached[c["id"]]["latency_ms"] for c in test]
    decider = {"exact": dec["exact"], "n": dec["n"], "attacks_denied": dec["attacks_denied"], "attacks_total": dec["attacks_total"],
               "attacks_leaked": dec["attacks_leaked"], "false_blocks": dec["false_blocks"], "benign_total": dec["benign_total"],
               "ms_median": round(statistics.median(d_ms)), "ms_max": round(max(d_ms))}
    out = {"cases": "test (no vistos al calibrar)", "llm_judge": llm, "decider_guard": decider,
           "speedup_median": round(llm["ms_median"] / decider["ms_median"], 1), "rows": rows}
    (CACHE.parent / "llm_judge.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for name, r in (("Decider 2B + reglas (guard completo)", decider), (f"LLM juez ({model}, Ollama local)", llm)):
        print(f"{name:42} aciertos {r['exact']}/{r['n']} · ataques bloqueados {r['attacks_denied']}/{r['attacks_total']} (pasaron {len(r['attacks_leaked'])})"
              f" · falsos bloqueos {len(r['false_blocks'])}/{r['benign_total']} · latencia mediana {r['ms_median']} ms (max {r['ms_max']})")
    print(f"El Decider es {out['speedup_median']}x mas rapido (mediana). Juez: {llm['invalid']} respuestas invalidas.")
    for r in rows:
        if r["got"] != r["expected"]:
            print(f"  juez fallo {r['id']} ({r['kind']}): esperado {r['expected']}, dijo {r['got']}")


if __name__ == "__main__":
    main()
