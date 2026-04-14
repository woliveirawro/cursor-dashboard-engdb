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
# MAPEAMENTO DE VERTICAIS ENGDB (e-mail → vertical)
# ══════════════════════════════════════════════════════════════
ENGDB_VERTICAL_MAP = {
    "daniela.costa@engdb.com.br": "I&S",
    "andre.santos@engdb.com.br": "I&S",
    "ulisses.oliveira@engdb.com.br": "I&S",
    "alaecio.junior@engdb.com.br": "I&S",
    "ana.rosa@engdb.com.br": "I&S",
    "marcio.silva@engdb.com.br": "I&S",
    "phelipe.medeiros@engdb.com.br": "I&S",
    "ricardo.tassini@engdb.com.br": "I&S",
    "sabrina.silva@engdb.com.br": "I&S",
    "jhon.carvalho@engdb.com.br": "I&S",
    "edi.goetz@engdb.com.br": "I&S",
    "victor.brendo@engdb.com.br": "I&S",
    "davi.carmo@engdb.com.br": "I&S",
    "guilherme.nascimento@engdb.com.br": "I&S",
    "marcio.mattos@engdb.com.br": "I&S",
    "romero.barreto@engdb.com.br": "I&S",
    "luciano.mengarelli@engdb.com.br": "E&U",
    "andre.zaniboni@engdb.com.br": "E&U",
    "danilo.netti@engdb.com.br": "E&U",
    "amauri.serra@engdb.com.br": "E&U",
    "stefano.damacena@engdb.com.br": "E&U",
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
}

# Nomes são extraídos automaticamente do e-mail (ex: victor.brendo@ → Victor Brendo)
# Use este dict apenas para sobrescrever nomes que o e-mail não representa bem
ENGDB_NAME_MAP = {}

# ══════════════════════════════════════════════════════════════
# CONFIGURAÇÃO DOS GRUPOS
# filter_vertical: filtra membros pela vertical (para sub-grupos ENGDB)
# Grupos com mesmo api_key_env reutilizam dados da API (cache)
# ══════════════════════════════════════════════════════════════
GROUPS = [
    {
        "id": "arq",
        "name": "Arquitetura",
        "api_key_env": "CURSOR_API_KEY",
        "filter_vertical": "Arq",
        "default_vertical": "N/D",
        "vertical_map": ENGDB_VERTICAL_MAP,
        "name_map": ENGDB_NAME_MAP,
        "vert_names": {"Arq": "Arquitetura"},
    },
    {
        "id": "eu",
        "name": "Energia e Utilities",
        "api_key_env": "CURSOR_API_KEY",
        "filter_vertical": "E&U",
        "default_vertical": "N/D",
        "vertical_map": ENGDB_VERTICAL_MAP,
        "name_map": ENGDB_NAME_MAP,
        "vert_names": {"E&U": "Energia e Utilities"},
    },
    {
        "id": "is",
        "name": "Indústria e Serviços",
        "api_key_env": "CURSOR_API_KEY",
        "filter_vertical": "I&S",
        "default_vertical": "N/D",
        "vertical_map": ENGDB_VERTICAL_MAP,
        "name_map": ENGDB_NAME_MAP,
        "vert_names": {"I&S": "Indústria e Serviços"},
    },
    {
        "id": "nd",
        "name": "N/D",
        "api_key_env": "CURSOR_API_KEY",
        "filter_vertical": "N/D",
        "default_vertical": "N/D",
        "vertical_map": ENGDB_VERTICAL_MAP,
        "name_map": ENGDB_NAME_MAP,
        "vert_names": {"N/D": "Não Definido"},
    },
    {
        "id": "produtos",
        "name": "Produtos",
        "api_key_env": "CURSOR_API_KEY_2",
        "filter_vertical": None,
        "default_vertical": "Produtos",
        "vertical_map": {},
        "name_map": {},
        "vert_names": {"Produtos": "Produtos"},
    },
    {
        "id": "telco",
        "name": "Telco & Media",
        "api_key_env": "CURSOR_API_KEY_3",
        "filter_vertical": None,
        "default_vertical": "Telco&Media",
        "vertical_map": {},
        "name_map": {},
        "vert_names": {"Telco&Media": "Telco & Media"},
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


def name_from_email(email):
    """Deriva nome do e-mail: david.oliveira@engdb.com.br → David Oliveira"""
    local = email.split("@")[0]
    parts = local.replace("_", ".").replace("-", ".").split(".")
    return " ".join(p.capitalize() for p in parts if p)


def process_group(members_raw, events_raw, vertical_map, name_map, default_vertical, filter_vertical=None):
    members = {}
    for m in members_raw:
        email = (m.get("email") or "").strip().lower()
        if not email:
            continue
        vert = vertical_map.get(email, default_vertical)
        if filter_vertical and vert != filter_vertical:
            continue
        name = m.get("name") or ""
        if not name or name in ("Unnamed", "N/A", "(Sem nome)"):
            name = name_map.get(email, name_from_email(email))
        members[email] = {
            "name": name, "email": email,
            "role": m.get("role", "Member"),
            "vertical": vert,
        }

    usage_by_user = {}
    usage_by_user_date = {}
    daily_totals = {}
    daily_od_costs = {}
    model_usage = {}
    od_by_model = {}
    all_dates = set()
    member_emails = set(members.keys())

    for ev in events_raw:
        email = (ev.get("userEmail") or "").strip().lower()
        if not email:
            continue

        # Determinar vertical do email
        vert = vertical_map.get(email, default_vertical)

        # Se filtrando, só processar eventos de membros da vertical
        if filter_vertical and vert != filter_vertical:
            continue

        # Adicionar membro se não veio no spend
        if email not in member_emails:
            name = name_map.get(email, name_from_email(email))
            members[email] = {
                "name": name, "email": email,
                "role": "Member", "vertical": vert,
            }
            member_emails.add(email)

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
            usage_by_user[email] = {"requests": 0, "tokens": 0, "dates": set(),
                                    "od_requests": 0, "od_cents": 0.0, "included_requests": 0}
        usage_by_user[email]["requests"] += requests_count
        usage_by_user[email]["tokens"] += total_tokens
        usage_by_user[email]["dates"].add(date_str)

        # Classificar: On-Demand vs Included
        # Campo real da API: 'kind' (não 'kindLabel'), 'chargedCents' (não tokenUsage.totalCents)
        kind = ev.get("kind", "") or ev.get("kindLabel", "") or ""
        charged_cents = ev.get("chargedCents", 0) or 0
        is_ondemand = "usage-based" in kind.lower() or "on-demand" in kind.lower()

        if is_ondemand:
            usage_by_user[email]["od_requests"] += requests_count
            usage_by_user[email]["od_cents"] += charged_cents
        else:
            usage_by_user[email]["included_requests"] += requests_count

        key = (email, date_str)
        usage_by_user_date[key] = usage_by_user_date.get(key, 0) + requests_count
        daily_totals[date_str] = daily_totals.get(date_str, 0) + requests_count
        model_usage[model] = model_usage.get(model, 0) + requests_count

        # Custo on-demand por dia e por modelo
        if is_ondemand:
            daily_od_costs[date_str] = daily_od_costs.get(date_str, 0) + charged_cents
            od_by_model[model] = od_by_model.get(model, {"requests": 0, "cents": 0.0})
            od_by_model[model]["requests"] += requests_count
            od_by_model[model]["cents"] += charged_cents

    all_dates = sorted(all_dates)

    member_list = []
    for email, m in members.items():
        u = usage_by_user.get(email, {"requests": 0, "tokens": 0, "dates": set(),
                                      "od_requests": 0, "od_cents": 0.0, "included_requests": 0})
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

        od_dollars = round(u["od_cents"] / 100, 2)

        member_list.append({
            "name": m["name"], "email": email, "role": m["role"],
            "vertical": m["vertical"], "total_requests": round(tr),
            "included_requests": round(u["included_requests"]),
            "od_requests": round(u["od_requests"]),
            "od_cost": od_dollars,
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
            "total_od_requests": round(sum(m["od_requests"] for m in member_list)),
            "total_od_cost": round(sum(m["od_cost"] for m in member_list), 2),
            "total_tokens": round(sum(m["total_tokens"] for m in member_list)),
            "total_days": len(all_dates),
            "od_members": sum(1 for m in member_list if m["od_requests"] > 0),
        },
        "daily_od_costs": [{"date": d, "cents": round(daily_od_costs.get(d, 0), 2)} for d in all_dates],
        "od_by_model": sorted(
            [{"model": k, "requests": v["requests"], "cost": round(v["cents"]/100, 2)} for k, v in od_by_model.items()],
            key=lambda x: -x["cost"]
        ),
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

    # Cache: mesma API Key → reutiliza dados (evita chamadas duplicadas)
    api_cache = {}

    for group in GROUPS:
        api_key = os.environ.get(group["api_key_env"], "")
        if not api_key:
            print(f"⚠ Grupo '{group['name']}': API Key ({group['api_key_env']}) não encontrada, pulando...")
            continue

        print(f"━━━ Grupo: {group['name']} ━━━")

        cache_key = group["api_key_env"]
        if cache_key in api_cache:
            print(f"  Reutilizando dados do cache ({cache_key})...")
            members, events = api_cache[cache_key]
        else:
            print(f"  Buscando membros...")
            members = fetch_members(api_key)
            print(f"  → {len(members)} membros")
            print(f"  Buscando eventos...")
            events = fetch_events(api_key)
            print(f"  → {len(events)} eventos")
            api_cache[cache_key] = (members, events)

        fv = group.get("filter_vertical")
        print(f"  Processando{f' (filtro: {fv})' if fv else ''}...")
        data = process_group(
            members, events,
            group["vertical_map"], group["name_map"],
            group["default_vertical"], fv
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
