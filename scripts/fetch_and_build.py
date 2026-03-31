#!/usr/bin/env python3
"""
Cursor AI Dashboard Builder - Multi-Group
Consome a Admin API do Cursor para múltiplos grupos e gera o dashboard HTML.
"""
import os, json, sys, time
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from base64 import b64encode

API_BASE = "https://api.cursor.com"

# ══════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DOS GRUPOS
# Para adicionar um novo grupo, basta criar uma entrada aqui
# ══════════════════════════════════════════════════════════════
GROUPS = [
    {
        "id": "engdb",
        "name": "ENGDB",
        "api_key_env": "CURSOR_API_KEY",
        "default_vertical": "N/D",
        "vertical_map": {
            "daniela.costa@engdb.com.br": "I&S",
            "andre.santos@engdb.com.br": "I&S",
            "ulisses.oliveira@engdb.com.br": "I&S",
            "alaecio.junior@engdb.com.br": "I&S",
            "ana.rosa@engdb.com.br": "I&S",
            "marcio.silva@engdb.com.br": "I&S",
            "phelipe.medeiros@engdb.com.br": "I&S",
            "ricardo.tassini@engdb.com.br": "I&S",
            "sabrina.silva@engdb.com.br": "I&S",
            "luciano.mengarelli@engdb.com.br": "E&U",
            "andre.zaniboni@engdb.com.br": "E&U",
            "danilo.netti@engdb.com.br": "E&U",
            "amauri.serra@engdb.com.br": "E&U",
            "stefano.damacena@engdb.com.br": "E&U",
            "romero.barreto@engdb.com.br": "E&U",
            "edson.junior@engdb.com.br": "E&U",
            "jose.marcelo@engdb.com.br": "E&U",
            "leonardo.sousa@engdb.com.br": "E&U",
            "oswaldo.pelegrina@engdb.com.br": "E&U",
            "ulisses.rodrigues@engdb.com.br": "E&U",
            "ricardo.chagas@engdb.com.br": "Arq",
            "sergio.marmilicz@engdb.com.br": "Arq",
            "tiago.cardoso@engdb.com.br": "Arq",
            "wander.oliveira@engdb.com.br": "Arq",
            "thiago.mascarenhas@engdb.com.br": "Arq",
            "alessandro.schneider@engdb.com.br": "Arq",
            "brenno.neves@engdb.com.br": "Arq",
            "luiz.souza@engdb.com.br": "Arq",
            "mariane.quirino@engdb.com.br": "Arq",
            "walter.moura@engdb.com.br": "Arq",
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
        "id": "telco",
        "name": "Telco & Media",
        "api_key_env": "CURSOR_API_KEY_3",
        "default_vertical": "Telco & Media",
        "vertical_map": {},
        "name_map": {},
        "vert_names": {
            "Telco&Media": "Telco & Media",
            "N/D": "Não Definido",
        },
    },
]


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
    all_members = []
    page = 1
    while True:
        data = api_call("/teams/spend", api_key, {"page": page, "pageSize": 50})
        if not data:
            break
        spend_list = data.get("teamMemberSpend", [])
        for s in spend_list:
            all_members.append({
                "name": s.get("name", ""),
                "email": s.get("email", ""),
                "role": s.get("role", "member"),
            })
        total_pages = data.get("totalPages", 1)
        print(f"    Página {page}/{total_pages}: {len(spend_list)} membros")
        if page >= total_pages:
            break
        page += 1
        time.sleep(0.3)
    return all_members


def fetch_events(api_key):
    all_events = []
    page = 1
    while True:
        data = api_call("/teams/filtered-usage-events", api_key, {
            "page": page, "pageSize": 100
        })
        if not data:
            break
        events = data.get("usageEvents", [])
        all_events.extend(events)
        pagination = data.get("pagination", {})
        print(f"    Página {page}: {len(events)} eventos (total: {len(all_events)})")
        if not pagination.get("hasNextPage", False):
            break
        page += 1
        time.sleep(0.3)
    return all_events


def process_group(members_raw, events_raw, vertical_map, name_map, default_vertical):
    members = {}
    for m in members_raw:
        email = (m.get("email") or "").strip().lower()
        if not email:
            continue
        name = m.get("name") or name_map.get(email, "(Sem nome)")
        if name in ("Unnamed", "", "N/A"):
            name = name_map.get(email, "(Sem nome)")
        members[email] = {
            "name": name, "email": email,
            "role": m.get("role", "Member"),
            "vertical": vertical_map.get(email, default_vertical),
        }

    usage_by_user = {}
    usage_by_user_date = {}
    daily_totals = {}
    model_usage = {}
    all_dates = set()

    for ev in events_raw:
        email = (ev.get("userEmail") or "").strip().lower()
        if not email:
            continue
        ts = ev.get("timestamp", "")
        try:
            if isinstance(ts, (int, float)) or (isinstance(ts, str) and ts.isdigit()):
                dt = datetime.fromtimestamp(int(ts) / 1000)
            else:
                dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except:
            continue

        date_str = dt.strftime("%Y-%m-%d")
        all_dates.add(date_str)
        raw_cost = ev.get("requestsCosts", 1)
        requests_count = round(float(raw_cost)) if raw_cost else 1
        model = ev.get("model", "unknown")
        tokens = ev.get("tokenUsage", {})
        total_tokens = (
            tokens.get("inputTokens", 0) + tokens.get("outputTokens", 0) +
            tokens.get("cacheWriteTokens", 0) + tokens.get("cacheReadTokens", 0)
        )

        if email not in usage_by_user:
            usage_by_user[email] = {"requests": 0, "tokens": 0, "dates": set()}
        usage_by_user[email]["requests"] += requests_count
        usage_by_user[email]["tokens"] += total_tokens
        usage_by_user[email]["dates"].add(date_str)

        key = (email, date_str)
        usage_by_user_date[key] = usage_by_user_date.get(key, 0) + requests_count
        daily_totals[date_str] = daily_totals.get(date_str, 0) + requests_count
        model_usage[model] = model_usage.get(model, 0) + requests_count

        if email not in members:
            members[email] = {
                "name": name_map.get(email, email.split("@")[0].title()),
                "email": email, "role": "Member",
                "vertical": vertical_map.get(email, default_vertical),
            }

    all_dates = sorted(all_dates)

    member_list = []
    for email, m in members.items():
        u = usage_by_user.get(email, {"requests": 0, "tokens": 0, "dates": set()})
        tr = u["requests"]
        dates = sorted(u["dates"]) if u["dates"] else []
        if dates:
            d1 = datetime.strptime(dates[0], "%Y-%m-%d")
            d2 = datetime.strptime(dates[-1], "%Y-%m-%d")
            periodo = f"{d1.strftime('%d/%m/%Y')} até {d2.strftime('%d/%m/%Y')}"
            months = set()
            cur = d1
            while cur <= d2:
                months.add(cur.strftime("%m/%Y"))
                if cur.month == 12:
                    cur = cur.replace(year=cur.year + 1, month=1, day=1)
                else:
                    cur = cur.replace(month=cur.month + 1, day=1)
            meses_ativos = ", ".join(sorted(months))
        else:
            periodo = "—"
            meses_ativos = "—"

        member_list.append({
            "name": m["name"], "email": email, "role": m["role"],
            "vertical": m["vertical"], "total_requests": round(tr),
            "total_tokens": u["tokens"], "days_used": len(dates),
            "periodo": periodo, "meses_ativos": meses_ativos, "used": tr > 0,
        })

    member_list.sort(key=lambda x: -x["total_requests"])

    daily_usage = {}
    for (email, date_str), req in usage_by_user_date.items():
        if email not in daily_usage:
            daily_usage[email] = {}
        daily_usage[email][date_str] = round(req)

    vert_summary = {}
    for m in member_list:
        v = m["vertical"]
        if v not in vert_summary:
            vert_summary[v] = {"total": 0, "used": 0, "requests": 0}
        vert_summary[v]["total"] += 1
        if m["used"]:
            vert_summary[v]["used"] += 1
        vert_summary[v]["requests"] += m["total_requests"]

    if all_dates:
        d_start = datetime.strptime(all_dates[0], "%Y-%m-%d")
        d_end = datetime.strptime(all_dates[-1], "%Y-%m-%d")
        report_period = f"{d_start.strftime('%d %b')} — {d_end.strftime('%d %b %Y')}"
    else:
        report_period = "Sem dados"

    return {
        "members": member_list,
        "daily_usage": daily_usage,
        "all_dates": all_dates,
        "daily_totals": [{"date": d, "requests": round(daily_totals.get(d, 0))} for d in all_dates],
        "models": sorted(
            [{"model": k, "requests": v} for k, v in model_usage.items()],
            key=lambda x: -x["requests"]
        ),
        "vertical_summary": vert_summary,
        "stats": {
            "total_members": len(member_list),
            "active_members": sum(1 for m in member_list if m["used"]),
            "inactive_members": sum(1 for m in member_list if not m["used"]),
            "total_requests": round(sum(m["total_requests"] for m in member_list)),
            "total_tokens": round(sum(m["total_tokens"] for m in member_list)),
            "total_days": len(all_dates),
        },
        "report_period": report_period,
    }


def build_html(all_groups_data):
    template_path = os.path.join(os.path.dirname(__file__), "..", "template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("__DATA_PLACEHOLDER__", json.dumps(all_groups_data, ensure_ascii=False))
    html = html.replace("__UPDATED_AT__", all_groups_data["updated_at"])

    return html


def main():
    now_brt = datetime.now(tz=None) - timedelta(hours=3)
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
            print(f"⚠ Grupo '{group['name']}': API Key ({group['api_key_env']}) não encontrada, pulando...")
            continue

        print(f"━━━ Grupo: {group['name']} ━━━")
        print(f"  Buscando membros...")
        members = fetch_members(api_key)
        print(f"  → {len(members)} membros")

        print(f"  Buscando eventos...")
        events = fetch_events(api_key)
        print(f"  → {len(events)} eventos")

        print(f"  Processando...")
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

        print(f"  → {data['stats']['total_members']} membros, {data['stats']['active_members']} ativos, {data['stats']['total_requests']:,} requests\n")

    if not all_groups_data["groups"]:
        print("ERRO: Nenhum grupo processado.", file=sys.stderr)
        sys.exit(1)

    print("Gerando HTML...")
    html = build_html(all_groups_data)

    output_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  → Salvo: {output_path} ({len(html) // 1024}KB)")
    print(f"\n✅ Dashboard atualizado com sucesso!")


if __name__ == "__main__":
    main()
