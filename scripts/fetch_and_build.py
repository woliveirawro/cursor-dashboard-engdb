#!/usr/bin/env python3
"""
Cursor AI Dashboard Builder
Consome a Admin API do Cursor, processa os dados e gera o dashboard HTML.
"""
import os, json, sys, time
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from base64 import b64encode

API_BASE = "https://api.cursor.com"
API_KEY = os.environ.get("CURSOR_API_KEY", "")

# ── Mapeamento de verticais (ENGDB) ──
VERTICAL_MAP = {
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
}

# ── Mapeamento de nomes (para preencher "Unnamed") ──
NAME_MAP = {
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
}


def api_call(endpoint, payload=None):
    """Faz chamada autenticada à API do Cursor."""
    url = f"{API_BASE}{endpoint}"
    data = json.dumps(payload or {}).encode()
    creds = b64encode(f"{API_KEY}:".encode()).decode()
    req = Request(url, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Basic {creds}"
    })
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        print(f"API Error {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Connection Error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def fetch_team_members_from_spend():
    """Busca membros do time via endpoint /teams/spend (retorna nome, email, role)."""
    print("Buscando membros do time via /teams/spend...")
    all_members = []
    page = 1

    while True:
        data = api_call("/teams/spend", {"page": page, "pageSize": 50})
        spend_list = data.get("teamMemberSpend", [])
        for s in spend_list:
            all_members.append({
                "name": s.get("name", ""),
                "email": s.get("email", ""),
                "role": s.get("role", "member"),
            })
        total_pages = data.get("totalPages", 1)
        print(f"  → Página {page}/{total_pages}: {len(spend_list)} membros")

        if page >= total_pages:
            break
        page += 1
        time.sleep(0.3)

    print(f"  → {len(all_members)} membros encontrados")
    return all_members


def fetch_usage_events():
    """Busca todos os eventos de uso com paginação."""
    print("Buscando eventos de uso...")
    all_events = []
    page = 1
    page_size = 100

    while True:
        data = api_call("/teams/filtered-usage-events", {
            "page": page,
            "pageSize": page_size
        })
        events = data.get("usageEvents", [])
        all_events.extend(events)
        pagination = data.get("pagination", {})
        print(f"  → Página {page}: {len(events)} eventos (total: {len(all_events)})")

        if not pagination.get("hasNextPage", False):
            break
        page += 1
        time.sleep(0.3)

    return all_events


def fetch_spend():
    """Busca dados de gastos do time."""
    print("Buscando dados de gastos...")
    data = api_call("/teams/spend")
    spend = data.get("teamMemberSpend", [])
    print(f"  → {len(spend)} registros de gastos")
    return spend


def process_data(members_raw, events_raw, spend_raw):
    """Processa os dados brutos e retorna o JSON para o dashboard."""

    # Normalizar membros
    members = {}
    for m in members_raw:
        email = (m.get("email") or "").strip().lower()
        if not email:
            continue
        name = m.get("name") or NAME_MAP.get(email, "(Sem nome)")
        if name in ("Unnamed", "", "N/A"):
            name = NAME_MAP.get(email, "(Sem nome)")
        members[email] = {
            "name": name,
            "email": email,
            "role": m.get("role", "Member"),
            "vertical": VERTICAL_MAP.get(email, "N/D"),
        }

    # Processar eventos de uso
    usage_by_user = {}
    usage_by_user_date = {}
    daily_totals = {}
    model_usage = {}
    all_dates = set()

    for ev in events_raw:
        email = (ev.get("userEmail") or "").strip().lower()
        if not email:
            continue

        # Timestamp pode ser milissegundos ou ISO string
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
            tokens.get("inputTokens", 0) +
            tokens.get("outputTokens", 0) +
            tokens.get("cacheWriteTokens", 0) +
            tokens.get("cacheReadTokens", 0)
        )

        # Acumular por usuário
        if email not in usage_by_user:
            usage_by_user[email] = {"requests": 0, "tokens": 0, "dates": set()}
        usage_by_user[email]["requests"] += requests_count
        usage_by_user[email]["tokens"] += total_tokens
        usage_by_user[email]["dates"].add(date_str)

        # Acumular por usuário+data
        key = (email, date_str)
        usage_by_user_date[key] = usage_by_user_date.get(key, 0) + requests_count

        # Totais diários
        daily_totals[date_str] = daily_totals.get(date_str, 0) + requests_count

        # Modelos
        model_usage[model] = model_usage.get(model, 0) + requests_count

        # Adicionar membro se não existia
        if email not in members:
            members[email] = {
                "name": NAME_MAP.get(email, email.split("@")[0].title()),
                "email": email,
                "role": "Member",
                "vertical": VERTICAL_MAP.get(email, "N/D"),
            }

    all_dates = sorted(all_dates)

    # Construir lista de membros enriquecida
    member_list = []
    for email, m in members.items():
        u = usage_by_user.get(email, {"requests": 0, "tokens": 0, "dates": set()})
        tr = u["requests"]
        dates = sorted(u["dates"]) if u["dates"] else []

        # Calcular período e meses ativos
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
            "name": m["name"],
            "email": email,
            "role": m["role"],
            "vertical": m["vertical"],
            "total_requests": round(tr),
            "total_tokens": u["tokens"],
            "days_used": len(dates),
            "periodo": periodo,
            "meses_ativos": meses_ativos,
            "used": tr > 0,
        })

    member_list.sort(key=lambda x: -x["total_requests"])

    # Daily usage dict para heatmap
    daily_usage = {}
    for (email, date_str), req in usage_by_user_date.items():
        if email not in daily_usage:
            daily_usage[email] = {}
        daily_usage[email][date_str] = round(req)

    # Vertical summary
    vert_summary = {}
    for m in member_list:
        v = m["vertical"]
        if v not in vert_summary:
            vert_summary[v] = {"total": 0, "used": 0, "requests": 0}
        vert_summary[v]["total"] += 1
        if m["used"]:
            vert_summary[v]["used"] += 1
        vert_summary[v]["requests"] += m["total_requests"]

    # Determinar período do relatório
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
        ""updated_at": (datetime.now(tz=None) - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M") + " (BRT)",,
    }


def build_html(data):
    """Lê o template HTML e injeta os dados."""
    template_path = os.path.join(os.path.dirname(__file__), "..", "template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("__DATA_PLACEHOLDER__", json.dumps(data, ensure_ascii=False))
    html = html.replace("__REPORT_PERIOD__", data["report_period"])
    html = html.replace("__UPDATED_AT__", data["updated_at"])

    return html


def main():
    if not API_KEY:
        print("ERRO: Variável CURSOR_API_KEY não definida.", file=sys.stderr)
        sys.exit(1)

    print(f"═══ Cursor Dashboard Builder ═══")
    print(f"Início: {datetime.now(tz=None).strftime('%Y-%m-%d %H:%M UTC')}\n")

    members = fetch_team_members_from_spend()
    events = fetch_usage_events()
    spend = []  # Já extraímos membros do spend

    print("\nProcessando dados...")
    data = process_data(members, events, spend)

    print(f"  → {data['stats']['total_members']} membros")
    print(f"  → {data['stats']['active_members']} ativos ({data['stats']['total_days']} dias)")
    print(f"  → {data['stats']['total_requests']:,} requests totais")

    print("\nGerando HTML...")
    html = build_html(data)

    output_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  → Salvo: {output_path} ({len(html) // 1024}KB)")
    print(f"\n✅ Dashboard atualizado com sucesso!")


if __name__ == "__main__":
    main()
