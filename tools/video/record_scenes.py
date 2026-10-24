"""Graba las escenas REALES de la demo: la consola con el agente de Strands corriendo (sin simulaciones ni retoques).

    python -m tools.video.record_scenes sin_guard con_guard aprobacion      # o solo las que quieras repetir

Requisitos: consola en http://localhost:8080 con AGENT_MODEL_PROVIDER=ollama, Ollama y el Decider real corriendo.
Salida: <VIDEO_DIR>/raw/<escena>/*.webm y <VIDEO_DIR>/marks_<escena>.json (tiempos y estado real de la corrida, que se usan
para escribir la narracion con los numeros EXACTOS y para acelerar solo las esperas).
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.getenv("CONSOLE_URL", "http://localhost:8080")
OUT = Path(os.getenv("VIDEO_DIR", Path.home() / "Downloads" / "agentshield-video"))
VP = {"width": 1600, "height": 900}

CURSOR_JS = """
document.addEventListener('DOMContentLoaded', () => {
  const c = document.createElement('div'); c.id = 'fc';
  c.style.cssText = 'position:fixed;z-index:99999;width:24px;height:24px;border-radius:50%;background:rgba(255,255,255,.95);' +
    'box-shadow:0 0 0 3px rgba(0,0,0,.35),0 8px 22px rgba(0,0,0,.55);pointer-events:none;left:60px;top:60px;' +
    'transition:left .8s cubic-bezier(.4,0,.2,1),top .8s cubic-bezier(.4,0,.2,1),transform .15s';
  document.body.appendChild(c);
  window.__moveTo = (x, y) => { c.style.opacity = 1; c.style.left = (x - 12) + 'px'; c.style.top = (y - 12) + 'px'; };
  window.__hide = () => { c.style.opacity = 0; };
  c.style.opacity = 0; c.style.transition += ',opacity .4s';
  window.__click = () => { c.style.transform = 'scale(.65)'; setTimeout(() => c.style.transform = 'scale(1)', 170); };
  window.__pulse = (sel) => { const e = document.querySelector(sel); if (e) { e.style.transition = 'box-shadow .4s';
    e.style.boxShadow = '0 0 0 3px #34e39a, 0 0 40px 6px rgba(52,227,154,.45)'; setTimeout(() => e.style.boxShadow = '', 2600); } };
});
"""


def api_get(path):
    return json.load(urllib.request.urlopen(BASE + path, timeout=10))


class Scene:
    def __init__(self, p, name):
        self.name, self.marks = name, {}
        self.browser = p.chromium.launch(channel="chrome", headless=True, args=["--force-device-scale-factor=1"])
        self.ctx = self.browser.new_context(viewport=VP, record_video_dir=str(OUT / "raw" / name), record_video_size=VP,
                                            color_scheme="dark")
        self.ctx.add_init_script(CURSOR_JS)
        self.t0 = time.time()
        self.page = self.ctx.new_page()

    def mark(self, key):
        self.marks[key] = round(time.time() - self.t0, 2)

    def pause(self, s):
        self.page.wait_for_timeout(int(s * 1000))

    def click(self, selector):
        loc = self.page.locator(selector).first
        loc.scroll_into_view_if_needed()
        b = loc.bounding_box()
        self.page.evaluate("([x, y]) => window.__moveTo(x, y)", [b["x"] + b["width"] / 2, b["y"] + b["height"] / 2])
        self.pause(1.0)
        self.page.evaluate("window.__click()")
        loc.click()
        self.pause(0.35)
        self.page.evaluate("window.__hide()")  # el cursor se oculta tras el clic (no queda un punto suelto)
        self.pause(0.3)

    def center(self, selector):
        """Desplaza para dejar el elemento a media pantalla, lejos de los subtitulos del borde inferior."""
        self.page.evaluate("(sel) => { const e = document.querySelector(sel); if (e) e.scrollIntoView({block: 'center', behavior: 'smooth'}); }", selector)
        self.pause(1.0)

    def wait_done(self, timeout=240):
        self.page.wait_for_function("() => { const b = document.querySelector('.banner'); return b && !b.querySelector('.spinner'); }",
                                    timeout=timeout * 1000)

    def finish(self):
        self.mark("end")
        run_id = self.page.evaluate("typeof agent !== 'undefined' ? agent.runId : null")
        if run_id:
            self.marks["run"] = api_get(f"/api/agent/run/{run_id}")
        self.ctx.close()
        self.marks["video"] = str(next((OUT / "raw" / self.name).glob("*.webm")))
        (OUT / f"marks_{self.name}.json").write_text(json.dumps(self.marks, indent=1, ensure_ascii=False), encoding="utf-8")
        self.browser.close()
        print(f"{self.name}: listo · {self.marks.get('end')} s · run {run_id}")


def open_agent_tab(s):
    s.page.goto(BASE + "/#agent")
    s.page.wait_for_selector("#agentPane:not([hidden])")
    s.pause(2.0)


def sin_guard(p):
    s = Scene(p, "sin_guard")
    open_agent_tab(s)
    s.click(".preset.attack")
    s.pause(1.2)
    s.click('#gMode button[data-m="off"]')
    s.pause(1.0)
    s.click("#gGo")
    s.mark("run_click")
    s.wait_done()
    s.mark("done")
    s.pause(3.0)
    s.center(".ord.changed")
    s.page.evaluate("window.__pulse('.ord.changed')")
    s.pause(4.0)
    s.finish()


def con_guard(p):
    s = Scene(p, "con_guard")
    open_agent_tab(s)
    s.click(".preset.attack")
    s.pause(1.0)
    s.click('#gMode button[data-m="enforce"]')
    s.pause(0.8)
    s.click("#gGo")
    s.mark("run_click")
    s.wait_done()
    s.mark("done")
    s.pause(8.0)  # tiempo para que la narracion explique el bloqueo sobre lo que se ve
    # detalle de la decision: la misma nota evaluada con el Decider real, con cada pregunta contra su limite calibrado
    s.mark("detail_start")
    s.click("#tabAttack")
    s.pause(1.2)
    s.click("#aGo")
    s.page.wait_for_selector(".verdict", timeout=60000)
    s.pause(1.5)
    s.center(".gauges")
    s.page.evaluate("window.__pulse('.gauges')")
    s.pause(9.5)
    s.finish()


def aprobacion(p):
    s = Scene(p, "aprobacion")
    open_agent_tab(s)
    s.click(".preset.approve")
    s.pause(1.0)
    s.click('#gMode button[data-m="enforce"]')
    s.pause(0.8)
    s.click("#gGo")
    s.mark("run_click")
    s.page.wait_for_selector(".approval", timeout=240000)
    s.mark("approval_shown")
    s.pause(4.0)
    s.click(".approval .btn:not(.bad)")
    s.mark("approved")
    s.wait_done()
    s.mark("done")
    s.pause(3.0)
    s.center(".orders")
    s.pause(3.5)
    s.finish()


SCENES = {"sin_guard": sin_guard, "con_guard": con_guard, "aprobacion": aprobacion}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    wanted = sys.argv[1:] or list(SCENES)
    with sync_playwright() as p:
        for name in wanted:
            SCENES[name](p)
