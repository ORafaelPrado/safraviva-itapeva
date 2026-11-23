# Publicação do SafraViva

Como o projeto vai para a internet, e o que fica onde.

| Onde | O quê | Público? |
|---|---|---|
| GitHub (repositório) | código, SQL, documentação, análises, notebook | sim (portfólio) |
| MotherDuck (`md:safraviva`) | o banco inteiro: dados públicos + fazenda + alertas + conversas da IA | não (só com o token) |
| Streamlit Community Cloud | o painel | link aberto, mas **pede senha** |
| Segredos (Streamlit e GitHub) | `MOTHERDUCK_TOKEN`, `OPENAI_API_KEY`, `APP_SENHA` | não |

## Passo a passo (uma vez)

### 1. GitHub pessoal
1. No terminal, entre na **conta pessoal** (a máquina está logada na conta da empresa):
   ```bash
   gh auth login
   ```
   Escolha *GitHub.com* → *HTTPS* → *Login with a web browser* e entre com a conta pessoal.
2. Crie o repositório e envie (o commit inicial já foi feito localmente):
   ```bash
   gh repo create safraviva-itapeva --public --source . --push
   ```

### 2. MotherDuck (banco na nuvem)
1. Crie a conta em <https://app.motherduck.com> (plano gratuito) e gere um token em *Settings → Access tokens*.
2. Cole no `.env`: `MOTHERDUCK_TOKEN=...`
3. Envie o banco local:
   ```bash
   python -m scripts.publicar_motherduck
   ```
   Depois disso, o banco **oficial é o da nuvem**. Para backup: `python -m scripts.publicar_motherduck --baixar`.

### 3. Rotina diária no GitHub Actions
No repositório: *Settings → Secrets and variables → Actions → New repository secret*:
- `MOTHERDUCK_TOKEN` (obrigatório)
- `OPENAI_API_KEY` (opcional, para o resumo semanal)

Teste em *Actions → rotina-diaria → Run workflow*. A partir daí, ela roda todo dia às 6h (Brasília).

### 4. Painel no Streamlit Community Cloud
1. Entre em <https://share.streamlit.io> com a conta pessoal do GitHub → *Create app*.
2. Repositório `safraviva-itapeva`, branch `main`, arquivo principal `app/main.py`, Python 3.13.
3. Em *Advanced settings → Secrets*, cole (TOML):
   ```toml
   MOTHERDUCK_TOKEN = "..."
   OPENAI_API_KEY = "..."
   OPENAI_MODEL = "gpt-5-mini"
   APP_SENHA = "uma senha forte"
   ```
4. *Deploy*. O endereço fica como `https://<nome>.streamlit.app`. Abra no celular e entre com a senha.

## No dia a dia
- O painel online e a rotina das 6h leem e gravam no MotherDuck: lançamentos feitos no celular ficam salvos.
- Para usar em casa **com os mesmos dados** da nuvem, deixe o `MOTHERDUCK_TOKEN` no `.env`. Sem ele, o painel usa o arquivo local `data/safraviva.duckdb`.
- Custo: GitHub, Streamlit Community Cloud e o plano gratuito do MotherDuck não cobram. A OpenAI cobra por uso (~8 mil tokens por pergunta).
