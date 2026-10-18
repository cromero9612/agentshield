#!/usr/bin/env bash
# Crea etiquetas, milestones e issues en GitHub a partir de docs/BACKLOG.md.
# Requiere GitHub CLI autenticado:  gh auth login
#
# Uso:   bash scripts/crear_issues.sh <owner>/<repo>
#        DRY_RUN=1 bash scripts/crear_issues.sh <owner>/<repo>   # solo muestra lo que haría
set -euo pipefail

REPO="${1:?Uso: bash scripts/crear_issues.sh <owner>/<repo>}"
DRY="${DRY_RUN:-0}"
HERE="$(cd "$(dirname "$0")" && pwd)"
BACKLOG="$HERE/../docs/BACKLOG.md"

run() { if [ "$DRY" = "1" ]; then echo "[dry] $*"; else "$@"; fi; }

for l in "persona-a:0E6E8C" "persona-b:1D7F46" "persona-c:9A6312" "persona-d:B8322B" "todos:5A6375"; do
  run gh label create "${l%%:*}" --color "${l##*:}" --repo "$REPO" --force
done

python3 - "$BACKLOG" > /tmp/agentshield_issues.tsv <<'PY'
import re, sys
day = None
for line in open(sys.argv[1], encoding="utf-8"):
    m = re.match(r"^## (.+?) · (.+)$", line.strip())
    if m:
        day = f"{m.group(1)} · {m.group(2)}"
        continue
    m = re.match(r"^\|\s*(A|B|C|D|Todos)\s*\|\s*(.+?)\s*\|$", line.strip())
    if m and day:
        who = "todos" if m.group(1) == "Todos" else "persona-" + m.group(1).lower()
        print(f"{day}\t{who}\t{m.group(2)}")
PY

SEEN=$'\n'
while IFS=$'\t' read -r day who title; do
  case "$SEEN" in *$'\n'"$day"$'\n'*) ;; *)
    run gh api "repos/$REPO/milestones" -f title="$day" >/dev/null || true
    SEEN="$SEEN$day"$'\n'
    ;;
  esac
  run gh issue create --repo "$REPO" --title "$title" --label "$who" --milestone "$day" \
    --body "Del backlog: **$day**. Responsable: \`$who\`. Ver docs/BACKLOG.md y docs/EQUIPO.md."
done < /tmp/agentshield_issues.tsv

echo "Listo. Asigna cada issue a su persona en GitHub (o con: gh issue edit N --add-assignee usuario)."
