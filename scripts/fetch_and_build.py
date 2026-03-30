#!/usr/bin/env python3
"""
Cursor AI Dashboard Builder - Multi-Group
Consome a Admin API do Cursor para múltiplos grupos e gera o dashboard HTML.
Grupos: ENGDB | Produtos | Telco & Media
"""

import json
import os
import sys
from base64 import b64encode
from datetime import datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_BASE = "https://api.cursor.com"

# ─────────────────────────────────────────────
# Configuração dos grupos
# ─────────────────────────────────────────────
GROUPS = [
    {
        "id": "engdb",
        "name": "ENGDB",
        "api_key_env": "CURSOR_API_KEY",
        "default_vertical": "N/D",
        "vertical_map": {
            "thiago.mascarenhas@engdb.com.br": "Arq",
            "luciano.mengarelli@engdb.com.br": "Arq",
            "ulisses.oliveira@engdb.com.br": "Arq",
            "andre.zaniboni@engdb.com.br": "Arq",
            "daniela.costa@engdb.com.br": "Arq",
            "danilo.netti@engdb.com.br": "E&U",
            "alaecio.junior@engdb.com.br": "E&U",
            "ulisses.rodrigues@engdb.com.br": "E&U",
            "amauri.serra@engdb.com.br": "E&U",
            "romero.barreto@engdb.com.br": "I&S",
            "jhon.carvalho@engdb.com.br": "I&S",
        },
        "name_map": {
            "thiago.mascarenhas@engdb.com.br": "Thiago Mascarenhas",
            "luciano.mengarelli@engdb.com.br": "Luciano Mengarelli",
            "ulisses.oliveira@engdb.com.br": "Ulisses Oliveira",
            "andre.zaniboni@engdb.com.br": "Andre Zaniboni",
            "daniela.costa@engdb.com.br": "Daniela Costa",
            "danilo.netti@engdb.com.br": "Danilo Netti",
            "alaecio.junior@engdb.com.br": "Alaecio Quirino",
            "ulisses.rodrigues@engdb.com.br": "Ulisses Rodrigues",
            "amauri.serra@engdb.com.br": "Amauri Serra",
            "romero.barreto@engdb.com.br": "Romero Barreto",
        },
        "vert_names": {
            "Arq": "Arquitetura",
            "E&U": "Energia e Utilities",
            "I&S": "Indústria e Serviços",
            "N/D": "Não Definido",
        },
    },
    {
        "id": "produtos",
        "name": "Produtos",
        "api_key_env": "CURSOR_API_KEY_2",
        "default_vertical": "Produtos",
        "vertical_map": {},
        "name_map": {},
        "vert_names": {
            "Produtos": "Produtos",
            "N/D": "Não Definido",
        },
    },
    {
        "id": "telco_media",
        "name": "Telco & Media",
        "api_key_env": "CURSOR_API_KEY_3",
        "default_vertical": "Telco & Media",
        "vertical_map": {},
        "name_map": {},
        "vert_names": {
            "Telco & Media": "Telco & Media",
            "N/D": "Não Definido",
        },
    },
]


# ─────────────────────────────────────────────
# Funções de API
# ─────────────────────────────────────────────
def api_call(endpoint, api_key, payload=None):
    url = f"{API_BASE}{endpoint}"
    data = json.dumps(payload or {}).encode()
    creds = b64encode(f"{api_key}:".encode()).decode()
    req = Request(url, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Basic {creds}"
    })
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        print(f"  API Error {e.code}: {e.read().decode()}", file=sys.stderr)
        return None
    except URLError as e:
        print(f"  Connection Error: {e.reason}", file=sys.stderr)
        return None


def fetch_members(api_key):
    """Tenta /teams/team-members primeiro; faz fallback para /teams/spend."""
    all_members = []

    # Tentativa 1: endpoint team-members
    data = api_call("/teams/team-members", api_key, {})
    if data:
        raw = data.get("teamMembers", data.get("members", []))
        if raw:
            # Normaliza para o formato {email, name}
            for m in raw:
                email = m.get("email", "") or m.get("userId", "")
                name  = m.get("name", "") or m.get("displayName", "") or email.split("@")[0]
                all_members.append({"email": email, "name": name})
            print(f"  → {len(all_members)} membros via /team-members")
            return all_members

    # Fallback: endpoint spend
    page = 1
    while True:
        data = api_call("/teams/spend", api_key, {"page": page, "pageSize": 50})
        if not data:
            break
        members = data.get("members", [])
        if not members:
            break
        for m in members:
            email = m.get("email", "") or m.get("userId", "")
            name  = m.get("name", "") or email.split("@")[0]
            all_members.append({"email": email, "name": name})
        if len(members) < 50:
            break
        page += 1

    print(f"  → {len(all_members)} membros via /spend")
    return all_members


def fetch_events(api_key):
    all_events = []
    page = 1
    while True:
        data = api_call("/teams/filtered-usage-events", api_key, {
            "page": page,
            "pageSize": 100,
        })
        if not data:
            break
        events = data.get("usageEvents", [])
        if not events:
            break
        all_events.extend(events)
        print(f"  → Página {page}: {len(events)} eventos (total: {len(all_events)})")
        if len(events) < 100:
            break
        page += 1
    return all_events


# ─────────────────────────────────────────────
# Processamento de dados
# ─────────────────────────────────────────────
def parse_timestamp(raw_ts):
    """Aceita timestamp como int (ms epoch) ou string ISO 8601."""
    try:
        if isinstance(raw_ts, str):
            return datetime.fromisoformat(raw_ts.replace("Z", "+00:00")).replace(tzinfo=None)
        return datetime.utcfromtimestamp(int(raw_ts) / 1000)
    except Exception:
        return None


def process_group(members, events, vertical_map, name_map, default_vertical):
    from datetime import timezone
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now - timedelta(days=31)

    # Indexar eventos por e-mail
    events_by_email = {}
    all_dates = set()
    for ev in events:
        dt = parse_timestamp(ev.get("timestamp", 0))
        if dt is None or dt < cutoff:
            continue
        email = ev.get("userId", "")
        day = dt.strftime("%Y-%m-%d")
        all_dates.add(day)
        if email not in events_by_email:
            events_by_email[email] = {"requests": 0, "tokens": 0, "models": {}, "days": {}}
        events_by_email[email]["requests"] += 1
        tokens = ev.get("totalTokens", 0) or 0
        events_by_email[email]["tokens"] += tokens
        model = ev.get("model", "unknown") or "unknown"
        events_by_email[email]["models"][model] = events_by_email[email]["models"].get(model, 0) + 1
        events_by_email[email]["days"][day] = events_by_email[email]["days"].get(day, 0) + 1

    # Montar lista de membros
    member_list = []
    for m in members:
        email = m.get("email", "")
        name = name_map.get(email) or m.get("name") or email.split("@")[0]
        vertical = vertical_map.get(email, default_vertical)
        ev_data = events_by_email.get(email, {})
        last_active = ""
        if ev_data.get("days"):
            last_active = max(ev_data["days"].keys())

        member_list.append({
            "email": email,
            "name": name,
            "vertical": vertical,
            "requests": ev_data.get("requests", 0),
            "total_tokens": ev_data.get("tokens", 0),
            "models": ev_data.get("models", {}),
            "daily": ev_data.get("days", {}),
            "last_active": last_active,
            "active": ev_data.get("requests", 0) > 0,
        })

    member_list.sort(key=lambda x: x["requests"], reverse=True)

    # Período do relatório
    sorted_dates = sorted(all_dates)
    if sorted_dates:
        d0 = datetime.strptime(sorted_dates[0], "%Y-%m-%d").strftime("%d/%m/%Y")
        d1 = datetime.strptime(sorted_dates[-1], "%Y-%m-%d").strftime("%d/%m/%Y")
        report_period = f"{d0} – {d1}"
    else:
        report_period = "Sem dados"

    return {
        "members": member_list,
        "all_dates": sorted_dates,
        "stats": {
            "total_members": len(member_list),
            "active_members": sum(1 for m in member_list if m["active"]),
            "total_requests": sum(m["requests"] for m in member_list),
            "total_tokens": round(sum(m["total_tokens"] for m in member_list)),
            "total_days": len(all_dates),
        },
        "report_period": report_period,
    }


# ─────────────────────────────────────────────
# Build HTML
# ─────────────────────────────────────────────
def build_html(all_groups_data):
    template_path = os.path.join(os.path.dirname(__file__), "..", "template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("__DATA_PLACEHOLDER__", json.dumps(all_groups_data, ensure_ascii=False))
    html = html.replace("__UPDATED_AT__", all_groups_data["updated_at"])
    return html


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    from datetime import timezone
    now_brt = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=3)
    print(f"═══ Cursor Dashboard Builder (Multi-Group) ═══")
    print(f"Início: {now_brt.strftime('%Y-%m-%d %H:%M')} (BRT)\n")

    all_groups_data = {
        "groups": {},
        "group_list": [],
        "updated_at": now_brt.strftime("%d/%m/%Y %H:%M") + " (BRT)",
    }

    for group in GROUPS:
        api_key = os.environ.get(group["api_key_env"], "")
        if not api_key:
            print(f"⚠ Grupo '{group['name']}': variável {group['api_key_env']} não encontrada, pulando...")
            continue

        print(f"━━━ Grupo: {group['name']} ━━━")
        print(f"  Buscando membros...")
        members = fetch_members(api_key)
        print(f"  → {len(members)} membros")

        print(f"  Buscando eventos...")
        events = fetch_events(api_key)

        print(f"  Processando dados...")
        data = process_group(
            members, events,
            group["vertical_map"], group["name_map"],
            group["default_vertical"]
        )
        data["vert_names"] = group["vert_names"]

        all_groups_data["groups"][group["id"]] = data
        all_groups_data["group_list"].append({
            "id": group["id"],
            "name": group["name"],
        })

        print(f"  → {data['stats']['total_members']} membros | "
              f"{data['stats']['active_members']} ativos | "
              f"{data['stats']['total_requests']:,} requests\n")

    if not all_groups_data["groups"]:
        print("ERRO: Nenhum grupo processado.", file=sys.stderr)
        sys.exit(1)

    print("Gerando HTML...")
    html = build_html(all_groups_data)

    output_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = len(html) // 1024
    print(f"  → Salvo: {output_path} ({size_kb}KB)")
    print(f"\n✅ Dashboard atualizado com sucesso!")


if __name__ == "__main__":
    main()
