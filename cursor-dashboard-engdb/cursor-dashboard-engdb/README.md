# Cursor AI - Dashboard de Utilização - ENGDB

Dashboard automatizado que consome a **Admin API do Cursor** e publica relatórios de uso do time via **GitHub Pages**.

## Arquitetura

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Cursor API  │────▶│  GitHub Actions   │────▶│  GitHub Pages    │
│  (dados)     │     │  (cron diário)    │     │  (dashboard)     │
└──────────────┘     └──────────────────┘     └──────────────────┘
                      fetch_and_build.py        index.html
                      template.html ──▶ dados
```

**Fluxo:**
1. GitHub Actions roda diariamente às 07:00 UTC (04:00 BRT)
2. O script Python consome 3 endpoints da API do Cursor
3. Processa os dados e injeta no template HTML
4. Faz commit do `index.html` atualizado
5. Deploy automático no GitHub Pages

## Setup Rápido (5 minutos)

### 1. Criar repositório no GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/SEU_USER/cursor-dashboard-engdb.git
git push -u origin main
```

### 2. Configurar o Secret da API Key

1. No repositório GitHub, vá em **Settings → Secrets and variables → Actions**
2. Clique em **New repository secret**
3. Nome: `CURSOR_API_KEY`
4. Valor: `crsr_f652e5b6f1f642065e19fb17464c10e4bdf83eb7206f2ec3cfb3e4d26bada2fb`
5. Clique em **Add secret**

### 3. Ativar GitHub Pages

1. No repositório, vá em **Settings → Pages**
2. Em **Source**, selecione **GitHub Actions**
3. Salvar

### 4. Executar a primeira vez

1. Vá em **Actions** no repositório
2. Selecione o workflow **Atualizar Dashboard Cursor**
3. Clique em **Run workflow → Run workflow**
4. Aguarde ~2 minutos
5. Acesse: `https://SEU_USER.github.io/cursor-dashboard-engdb/`

## Estrutura do Repositório

```
cursor-dashboard-engdb/
├── .github/workflows/
│   └── update-dashboard.yml    # Automação GitHub Actions
├── scripts/
│   └── fetch_and_build.py      # Coleta dados da API + gera HTML
├── template.html               # Template do dashboard
├── index.html                  # Dashboard gerado (auto-commit)
└── README.md
```

## Personalização

### Alterar frequência de atualização

Edite `.github/workflows/update-dashboard.yml`:

```yaml
schedule:
  - cron: '0 */6 * * *'   # A cada 6 horas
  - cron: '0 7 * * 1-5'   # Apenas dias úteis às 07:00 UTC
  - cron: '*/30 * * * *'  # A cada 30 minutos
```

### Adicionar novo membro ou vertical

Edite `scripts/fetch_and_build.py`:

```python
VERTICAL_MAP = {
    ...
    "novo.membro@engdb.com.br": "Arq",  # adicionar aqui
}

NAME_MAP = {
    ...
    "novo.membro@engdb.com.br": "Nome Completo",  # se necessário
}
```

### Alterar layout/cores do dashboard

Edite `template.html` — todo o CSS e JS está no próprio arquivo.

## Execução Local (teste)

```bash
export CURSOR_API_KEY="crsr_..."
python3 scripts/fetch_and_build.py
# Abre index.html no browser
```

## Endpoints da API utilizados

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/teams/team-members` | POST | Lista membros do time |
| `/teams/filtered-usage-events` | POST | Eventos de uso (paginado) |
| `/teams/spend` | POST | Gastos por membro |

## Segurança

- A API Key fica armazenada como **GitHub Secret** (encriptada)
- Nunca é exposta no HTML ou no código
- O dashboard gerado é 100% estático (sem chamadas client-side)
- Acesso ao Pages pode ser restrito via repositório privado

## Troubleshooting

**Workflow falha com "API Error 401"**
→ Verifique se o secret `CURSOR_API_KEY` está correto

**Workflow falha com "API Error 403"**
→ A API Key pode ter expirado, gere uma nova em cursor.com/dashboard

**Dados estão desatualizados**
→ Execute o workflow manualmente via Actions → Run workflow

**Membro aparece como "(Sem nome)"**
→ Adicione o e-mail no `NAME_MAP` em `fetch_and_build.py`
