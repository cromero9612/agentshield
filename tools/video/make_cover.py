"""Genera la portada del articulo (1200x675, sin texto: Builder Center lo desaconseja).

    python -m tools.video.make_cover            # escribe ~/Downloads/agentshield-video/portada.jpg

Ilustracion de la idea: un agente lanza tres acciones; el guard (escudo de cristal) deja pasar dos y rompe la inyectada.
"""
import io
import os
import pathlib

from PIL import Image
from playwright.sync_api import sync_playwright

OUT = pathlib.Path(os.getenv("VIDEO_DIR", pathlib.Path.home() / "Downloads" / "agentshield-video"))

TILE = lambda y, on: (  # noqa: E731
    f'<rect x="968" y="{y}" width="112" height="112" rx="30" fill="#34e39a" opacity=".30" filter="url(#b14)"/>' if on else "")

HTML = """<!doctype html><meta charset=utf-8><style>*{margin:0}body{width:1200px;height:675px;overflow:hidden;background:#04060c}</style>
<svg width="1200" height="675" viewBox="0 0 1200 675" xmlns="http://www.w3.org/2000/svg">
<defs>
 <radialGradient id="bgv" cx="50%" cy="50%" r="75%"><stop offset="55%" stop-color="#000" stop-opacity="0"/><stop offset="100%" stop-color="#000" stop-opacity=".65"/></radialGradient>
 <linearGradient id="gShield" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".30"/><stop offset=".5" stop-color="#9fd0ff" stop-opacity=".10"/><stop offset="1" stop-color="#fff" stop-opacity=".05"/></linearGradient>
 <linearGradient id="gRim" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".95"/><stop offset=".4" stop-color="#fff" stop-opacity=".12"/><stop offset=".7" stop-color="#fff" stop-opacity=".05"/><stop offset="1" stop-color="#7fe9c0" stop-opacity=".85"/></linearGradient>
 <linearGradient id="gCheck" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5dffb8"/><stop offset="1" stop-color="#3aa0ff"/></linearGradient>
 <linearGradient id="gOk" x1="0" x2="1"><stop offset="0" stop-color="#34e39a" stop-opacity=".05"/><stop offset=".75" stop-color="#34e39a" stop-opacity=".95"/><stop offset="1" stop-color="#9dffd5"/></linearGradient>
 <linearGradient id="gBad" x1="0" x2="1"><stop offset="0" stop-color="#ff5470" stop-opacity=".05"/><stop offset=".8" stop-color="#ff5470" stop-opacity=".95"/><stop offset="1" stop-color="#ffb0bd"/></linearGradient>
 <linearGradient id="gTile" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".20"/><stop offset="1" stop-color="#fff" stop-opacity=".04"/></linearGradient>
 <filter id="b30" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="30"/></filter>
 <filter id="b14" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="14"/></filter>
 <filter id="b6" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>
 <filter id="b3" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3"/></filter>
 <filter id="noise"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .5 0"/></filter>
 <pattern id="dots" width="26" height="26" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.1" fill="#9fb8ff" fill-opacity=".14"/></pattern>
</defs>
<rect width="1200" height="675" fill="#04060c"/>
<circle cx="120" cy="80" r="330" fill="#2a6bff" opacity=".55" filter="url(#b30)"/>
<circle cx="1120" cy="170" r="300" fill="#18d996" opacity=".42" filter="url(#b30)"/>
<circle cx="700" cy="760" r="340" fill="#8b5cf6" opacity=".50" filter="url(#b30)"/>
<circle cx="1000" cy="650" r="180" fill="#ff5ea8" opacity=".22" filter="url(#b30)"/>
<rect width="1200" height="675" fill="url(#dots)"/>

<!-- haces: dos entran al escudo y salen hacia las herramientas; uno se estrella -->
<g fill="none" stroke-linecap="round">
 <path d="M258 322 C 420 322, 520 252, 668 252" stroke="#34e39a" stroke-width="11" opacity=".5" filter="url(#b6)"/><path d="M258 322 C 420 322, 520 252, 668 252" stroke="url(#gOk)" stroke-width="4"/>
 <path d="M258 358 C 420 358, 520 428, 668 428" stroke="#34e39a" stroke-width="11" opacity=".5" filter="url(#b6)"/><path d="M258 358 C 420 358, 520 428, 668 428" stroke="url(#gOk)" stroke-width="4"/>
 <path d="M912 252 C 940 252, 944 226, 968 226" stroke="#34e39a" stroke-width="11" opacity=".5" filter="url(#b6)"/><path d="M912 252 C 940 252, 944 226, 968 226" stroke="#7bffc4" stroke-width="4"/>
 <path d="M912 428 C 940 428, 944 454, 968 454" stroke="#34e39a" stroke-width="11" opacity=".5" filter="url(#b6)"/><path d="M912 428 C 940 428, 944 454, 968 454" stroke="#7bffc4" stroke-width="4"/>
 <path d="M258 340 L 662 340" stroke="#ff5470" stroke-width="13" opacity=".6" filter="url(#b6)"/><path d="M258 340 L 662 340" stroke="url(#gBad)" stroke-width="4.5"/>
</g>
<g>
 <rect x="372" y="306" width="46" height="22" rx="11" fill="#34e39a" filter="url(#b6)" opacity=".8"/><rect x="372" y="306" width="46" height="22" rx="11" fill="#c9ffe6"/>
 <rect x="520" y="264" width="34" height="18" rx="9" fill="#34e39a" filter="url(#b6)" opacity=".8"/><rect x="520" y="264" width="34" height="18" rx="9" fill="#c9ffe6"/>
 <rect x="368" y="348" width="46" height="22" rx="11" fill="#34e39a" filter="url(#b6)" opacity=".8"/><rect x="368" y="348" width="46" height="22" rx="11" fill="#c9ffe6"/>
 <rect x="522" y="416" width="34" height="18" rx="9" fill="#34e39a" filter="url(#b6)" opacity=".8"/><rect x="522" y="416" width="34" height="18" rx="9" fill="#c9ffe6"/>
 <rect x="468" y="328" width="58" height="24" rx="12" fill="#ff5470" filter="url(#b6)" opacity=".9"/><rect x="468" y="328" width="58" height="24" rx="12" fill="#ffd0d8"/>
 <rect x="584" y="333" width="30" height="14" rx="7" fill="#ff5470" filter="url(#b6)" opacity=".8"/><rect x="584" y="333" width="30" height="14" rx="7" fill="#ffd0d8"/>
 <rect x="928" y="246" width="26" height="12" rx="6" fill="#c9ffe6"/><rect x="928" y="422" width="26" height="12" rx="6" fill="#c9ffe6"/>
</g>

<!-- agente -->
<g>
 <circle cx="190" cy="340" r="128" fill="none" stroke="#fff" stroke-opacity=".10" stroke-width="1.5" stroke-dasharray="3 9"/>
 <circle cx="190" cy="340" r="96" fill="none" stroke="#fff" stroke-opacity=".18" stroke-width="1.5"/>
 <circle cx="190" cy="340" r="72" fill="#2a8cff" opacity=".55" filter="url(#b14)"/>
 <circle cx="190" cy="340" r="62" fill="url(#gTile)" stroke="url(#gRim)" stroke-width="2"/>
 <circle cx="190" cy="340" r="26" fill="#fff" opacity=".92"/><circle cx="190" cy="340" r="14" fill="#2a8cff"/>
 <circle cx="190" cy="212" r="6" fill="#9fd0ff"/><circle cx="302" cy="404" r="5" fill="#34e39a"/><circle cx="96" cy="430" r="4" fill="#c9a8ff"/>
</g>

<!-- escudo de cristal -->
<g>
 <path d="M790 150 L 668 198 V 318 C 668 418 724 500 790 530 C 856 500 912 418 912 318 V 198 Z" fill="#34e39a" opacity=".38" filter="url(#b30)"/>
 <path d="M790 150 L 668 198 V 318 C 668 418 724 500 790 530 C 856 500 912 418 912 318 V 198 Z" fill="url(#gShield)" stroke="url(#gRim)" stroke-width="3.5"/>
 <path d="M790 172 L 688 212 V 318 C 688 405 735 476 790 503 C 845 476 892 405 892 318 V 212 Z" fill="none" stroke="#fff" stroke-opacity=".16" stroke-width="2"/>
 <path d="M700 224 C 740 205 790 192 840 198" fill="none" stroke="#fff" stroke-opacity=".55" stroke-width="5" stroke-linecap="round" filter="url(#b3)"/>
 <path d="M738 344 L 778 386 L 850 292" fill="none" stroke="#34e39a" stroke-width="30" stroke-linecap="round" stroke-linejoin="round" opacity=".6" filter="url(#b14)"/>
 <path d="M738 344 L 778 386 L 850 292" fill="none" stroke="url(#gCheck)" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/>
 <path d="M742 340 L 778 378" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="5" stroke-linecap="round"/>
</g>

<!-- impacto del ataque bloqueado: onda de choque y esquirlas -->
<g>
 <circle cx="662" cy="340" r="46" fill="#ff5470" opacity=".55" filter="url(#b14)"/>
 <circle cx="662" cy="340" r="64" fill="none" stroke="#ff7a90" stroke-opacity=".55" stroke-width="2"/>
 <circle cx="662" cy="340" r="92" fill="none" stroke="#ff7a90" stroke-opacity=".25" stroke-width="1.5"/>
 <circle cx="662" cy="340" r="15" fill="#fff" opacity=".96"/>
 <g fill="#ffc2cd">
  <rect x="598" y="288" width="22" height="9" rx="3" transform="rotate(-40 609 292)"/><rect x="574" y="333" width="26" height="9" rx="3" transform="rotate(8 587 337)"/>
  <rect x="596" y="384" width="22" height="9" rx="3" transform="rotate(38 607 388)"/><rect x="636" y="262" width="18" height="8" rx="3" transform="rotate(-72 645 266)"/>
  <rect x="634" y="408" width="18" height="8" rx="3" transform="rotate(70 643 412)"/><rect x="548" y="300" width="12" height="6" rx="3" transform="rotate(-20 554 303)"/>
  <rect x="552" y="372" width="12" height="6" rx="3" transform="rotate(24 558 375)"/>
 </g>
</g>

<!-- herramientas: dos activas, una apagada -->
<g>
 <rect x="968" y="170" width="112" height="112" rx="30" fill="#34e39a" opacity=".30" filter="url(#b14)"/>
 <rect x="968" y="170" width="112" height="112" rx="30" fill="url(#gTile)" stroke="url(#gRim)" stroke-width="2"/>
 <g stroke="#7bffc4" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"><rect x="1000" y="192" width="48" height="68" rx="9"/><path d="M1011 216 H1037 M1011 232 H1037 M1011 248 H1028"/></g>
 <rect x="968" y="404" width="112" height="112" rx="30" fill="#34e39a" opacity=".30" filter="url(#b14)"/>
 <rect x="968" y="404" width="112" height="112" rx="30" fill="url(#gTile)" stroke="url(#gRim)" stroke-width="2"/>
 <g stroke="#7bffc4" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M1024 428 L1054 445 V479 L1024 496 L994 479 V445 Z"/><path d="M994 445 L1024 462 L1054 445 M1024 462 V496"/></g>
 <rect x="968" y="287" width="112" height="106" rx="30" fill="#0a0e1a" fill-opacity=".55" stroke="#ff5470" stroke-opacity=".5" stroke-width="2.5" stroke-dasharray="6 8"/>
 <g stroke="#ff7a90" stroke-opacity=".85" stroke-width="6" stroke-linecap="round"><path d="M1006 322 L1042 358 M1042 322 L1006 358"/></g>
</g>

<!-- cuatro respuestas tipadas -->
<g transform="translate(520 70)">
 <rect x="0" y="0" width="300" height="58" rx="29" fill="url(#gTile)" stroke="url(#gRim)" stroke-width="1.6"/>
 <rect x="38" y="16" width="14" height="26" rx="7" fill="#fff" fill-opacity=".10"/><rect x="38" y="20" width="14" height="22" rx="7" fill="#34e39a"/>
 <rect x="104" y="16" width="14" height="26" rx="7" fill="#fff" fill-opacity=".10"/><rect x="104" y="18" width="14" height="24" rx="7" fill="#34e39a"/>
 <rect x="170" y="16" width="14" height="26" rx="7" fill="#fff" fill-opacity=".10"/><rect x="170" y="14" width="14" height="28" rx="7" fill="#ff5470"/>
 <rect x="236" y="16" width="14" height="26" rx="7" fill="#fff" fill-opacity=".10"/><rect x="236" y="26" width="14" height="16" rx="7" fill="#ffc94d"/>
</g>
<rect width="1200" height="675" fill="url(#bgv)"/>
<rect width="1200" height="675" filter="url(#noise)" opacity=".07" style="mix-blend-mode:overlay"/>
</svg>"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        pg = b.new_page(viewport={"width": 1200, "height": 675}, device_scale_factor=2)  # 2x y se reduce: bordes limpios
        pg.set_content(HTML)
        pg.wait_for_timeout(500)
        png = pg.screenshot(type="png")
        b.close()
    im = Image.open(io.BytesIO(png)).convert("RGB").resize((1200, 675), Image.LANCZOS)
    im.save(OUT / "portada.jpg", quality=93, optimize=True, subsampling=0)
    print(im.size, round((OUT / "portada.jpg").stat().st_size / 1024), "KB ->", OUT / "portada.jpg")


if __name__ == "__main__":
    main()
