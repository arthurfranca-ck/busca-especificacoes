"""
App de Busca de Especificacoes de Equipamentos (com IA)
========================================================
Interface web (Streamlit) com busca automatica + assistente IA (Google Gemini).

Uso:
    py -m streamlit run app_busca.py
"""

import streamlit as st
import pandas as pd
import time
import io
import os
import json
from datetime import datetime

import base64
import requests as req

from freezer_specs_scraper import search_product

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_secret(key: str) -> str:
    val = os.environ.get(key, "")
    if not val:
        try:
            val = st.secrets.get(key, "")
        except Exception:
            pass
    return val or ""


# ─── Historico persistente (GitHub) ───────────────────────────────────────────

GITHUB_TOKEN = _get_secret("GITHUB_TOKEN")
GITHUB_REPO = _get_secret("GITHUB_REPO") or "arthurfranca-ck/busca-especificacoes"
HISTORY_FILE = "historico.csv"
HISTORY_COLUMNS = [
    "produto", "potencia_w", "voltagem_v", "fase", "consumo_kwh", "btu",
    "fonte_potencia", "fonte_voltagem", "data_hora", "usuario",
]


@st.cache_data(ttl=30, show_spinner=False)
def _load_history_from_github() -> pd.DataFrame:
    """Le o historico.csv do repositório GitHub."""
    if not GITHUB_TOKEN:
        return pd.DataFrame(columns=HISTORY_COLUMNS)
    try:
        resp = req.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{HISTORY_FILE}",
            headers={"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"},
            timeout=10,
        )
        if resp.status_code == 200:
            content = base64.b64decode(resp.json()["content"]).decode("utf-8-sig")
            df = pd.read_csv(io.StringIO(content))
            return df
        return pd.DataFrame(columns=HISTORY_COLUMNS)
    except Exception:
        return pd.DataFrame(columns=HISTORY_COLUMNS)


def _save_history_to_github(df: pd.DataFrame):
    """Salva o historico.csv no repositório GitHub."""
    if not GITHUB_TOKEN:
        return
    try:
        csv_content = df.to_csv(index=False, encoding="utf-8-sig")
        encoded = base64.b64encode(csv_content.encode("utf-8-sig")).decode()

        resp = req.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{HISTORY_FILE}",
            headers={"Authorization": f"token {GITHUB_TOKEN}"},
            timeout=10,
        )
        sha = resp.json().get("sha") if resp.status_code == 200 else None

        payload = {
            "message": f"Historico atualizado - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            "content": encoded,
            "branch": "main",
        }
        if sha:
            payload["sha"] = sha

        req.put(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{HISTORY_FILE}",
            headers={"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"},
            json=payload,
            timeout=15,
        )
        _load_history_from_github.clear()
    except Exception:
        pass


def append_to_persistent_history(result: dict):
    """Adiciona um resultado ao historico persistente no GitHub."""
    if not GITHUB_TOKEN:
        return
    row = {col: result.get(col, "") for col in HISTORY_COLUMNS}
    row["data_hora"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    df = _load_history_from_github()
    new_row = pd.DataFrame([row])
    df = pd.concat([new_row, df], ignore_index=True)
    _save_history_to_github(df)


# ─── Tavily (busca com fontes reais) ──────────────────────────────────────────

TAVILY_API_KEY = _get_secret("TAVILY_API_KEY")
tavily_client = None

if TAVILY_API_KEY:
    try:
        from tavily import TavilyClient
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
    except Exception:
        pass

# ─── AI Setup (Groq / Llama) ─────────────────────────────────────────────────

GROQ_API_KEY = _get_secret("GROQ_API_KEY")
HAS_GEMINI = False
groq_client = None

if GROQ_API_KEY and GROQ_API_KEY != "SUA-CHAVE-AQUI":
    try:
        from groq import Groq
        groq_client = Groq(api_key=GROQ_API_KEY)
        HAS_GEMINI = True
    except Exception:
        pass

AI_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = (
    "Voce e um assistente tecnico de equipamentos comerciais/industriais. "
    "REGRAS: "
    "1) Seja MUITO breve e direto. Responda APENAS com as especificacoes tecnicas. "
    "2) Formato: liste Potencia (W), Voltagem (V), Consumo (kWh), BTU quando aplicavel. "
    "3) NAO faca introducoes, resumos longos ou explicacoes desnecessarias. "
    "4) IGNORE completamente dados sobre carros, imoveis ou assuntos nao relacionados a equipamentos. "
    "5) Se nao tiver dados confirmados, de sua melhor estimativa e marque com (estimativa). "
    "6) Responda em portugues do Brasil."
)


def ask_gemini(prompt: str, context: str = "") -> str:
    if not HAS_GEMINI:
        return "IA nao configurada. Adicione GROQ_API_KEY no arquivo .env"
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        user_content = ""
        if context:
            user_content += f"Dados do scraper:\n{context}\n\n"
        user_content += prompt
        messages.append({"role": "user", "content": user_content})

        response = groq_client.chat.completions.create(
            model=AI_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=800,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erro ao consultar IA: {e}"


def _tavily_search(produto: str, missing: list[str]) -> tuple[str, dict[str, str]]:
    """Busca specs faltantes via Tavily. Retorna (conteudo, {campo: url_fonte})."""
    if not tavily_client:
        return "", {}
    try:
        query = f"{produto} especificações técnicas {' '.join(missing)}"
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True,
        )
        content_parts = []
        sources = {}
        for r in response.get("results", []):
            url = r.get("url", "")
            text = r.get("content", "")
            if text:
                content_parts.append(f"[Fonte: {url}]\n{text}")
                if url:
                    for field in missing:
                        if field.lower() not in sources:
                            sources[field.lower()] = url

        answer = response.get("answer", "")
        if answer:
            content_parts.insert(0, f"Resumo: {answer}")

        top_url = ""
        if response.get("results"):
            top_url = response["results"][0].get("url", "")
        for field in missing:
            if field.lower() not in sources:
                sources[field.lower()] = top_url

        return "\n\n".join(content_parts), sources
    except Exception:
        return "", {}


def _map_field_source(field_label: str, sources: dict) -> str:
    """Mapeia um label de campo para a URL fonte do Tavily."""
    mappings = {
        "potencia_w": ["potencia (w)", "potencia"],
        "voltagem_v": ["voltagem (v)", "voltagem"],
        "fase": ["fase (monofasico/bifasico/trifasico)", "fase"],
        "consumo_kwh": ["consumo (kwh)", "consumo"],
        "btu": ["btu"],
    }
    for key in mappings.get(field_label, []):
        if key in sources:
            return sources[key]
    return ""


def enrich_with_ai(result: dict) -> dict:
    """Quando o scraper nao encontra specs, busca via Tavily + Groq."""
    missing = []
    if not result.get("potencia_w"):
        missing.append("Potencia (W)")
    if not result.get("voltagem_v"):
        missing.append("Voltagem (V)")
    if not result.get("fase"):
        missing.append("Fase (monofasico/bifasico/trifasico)")
    if not result.get("consumo_kwh"):
        missing.append("Consumo (kWh)")
    if not result.get("btu"):
        missing.append("BTU")

    if not missing:
        return result

    produto = result.get("produto", "")

    tavily_content, tavily_sources = _tavily_search(produto, missing)

    if tavily_content and HAS_GEMINI:
        prompt = (
            f"Analise os dados abaixo sobre o equipamento '{produto}' e extraia: {', '.join(missing)}.\n"
            f"Dados encontrados na internet:\n{tavily_content[:3000]}\n\n"
            f"Responda APENAS em formato JSON com as chaves: "
            f"potencia_w, voltagem_v, fase, consumo_kwh, btu. "
            f"Se nao encontrar nos dados, coloque null. Exemplo: "
            f'{{"potencia_w": "150 W", "voltagem_v": "220 V", "fase": "Monofasico", "consumo_kwh": "45 kWh/mes", "btu": null}}'
        )
        source_label = "IA + Fonte web"
    elif HAS_GEMINI:
        prompt = (
            f"Para o equipamento '{produto}', nao consegui encontrar: {', '.join(missing)}. "
            f"Com base no modelo e marca, estime os valores mais provaveis. "
            f"Responda APENAS em formato JSON com as chaves: "
            f"potencia_w, voltagem_v, fase, consumo_kwh, btu. "
            f"Se nao souber, coloque null. Exemplo: "
            f'{{"potencia_w": "150 W", "voltagem_v": "220 V", "fase": "Monofasico", "consumo_kwh": "45 kWh/mes", "btu": null}}'
        )
        source_label = "Estimativa IA"
    else:
        return result

    response = ask_gemini(prompt)
    try:
        start = response.find("{")
        end_idx = response.rfind("}") + 1
        if start >= 0 and end_idx > start:
            ai_data = json.loads(response[start:end_idx])
            enriched = result.copy()
            fields = [
                ("potencia_w", "fonte_potencia"),
                ("voltagem_v", "fonte_voltagem"),
                ("fase", "fonte_fase"),
                ("consumo_kwh", "fonte_consumo"),
                ("btu", "fonte_btu"),
            ]
            for field, fonte_field in fields:
                if not enriched.get(field) and ai_data.get(field):
                    tavily_url = _map_field_source(field, tavily_sources)
                    if tavily_url:
                        enriched[field] = str(ai_data[field])
                        enriched[fonte_field] = tavily_url
                    else:
                        enriched[field] = f"{ai_data[field]} (estimativa IA)"
                        enriched[fonte_field] = "Estimativa IA"
            return enriched
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    return result


def analyze_single(result: dict) -> str:
    """Gera analise de IA para um equipamento."""
    context = json.dumps({
        "produto": result.get("produto"),
        "potencia_w": result.get("potencia_w"),
        "voltagem_v": result.get("voltagem_v"),
        "fase": result.get("fase"),
        "consumo_kwh": result.get("consumo_kwh"),
        "btu": result.get("btu"),
    }, ensure_ascii=False)

    return ask_gemini(
        "Liste as especificacoes tecnicas deste equipamento de forma curta e direta:\n"
        "- Potencia, Voltagem, Consumo, BTU\n"
        "- Custo mensal estimado (tarifa R$0,75/kWh)\n"
        "- Se faltar algum dado, de sua estimativa marcando com (estimativa)\n"
        "5. Observacoes importantes",
        context=context,
    )


def compare_multiple(results: list[dict]) -> str:
    """Gera comparacao de IA entre multiplos equipamentos."""
    items = []
    for r in results:
        items.append({
            "produto": r.get("produto"),
            "potencia_w": r.get("potencia_w"),
            "voltagem_v": r.get("voltagem_v"),
            "fase": r.get("fase"),
            "consumo_kwh": r.get("consumo_kwh"),
            "btu": r.get("btu"),
        })
    context = json.dumps(items, ensure_ascii=False)

    return ask_gemini(
        "Faca uma tabela comparativa curta com Potencia, Voltagem, Consumo, BTU e custo mensal estimado (R$0,75/kWh). "
        "Indique o mais economico.",
        context=context,
    )


# ─── Cache ────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def _raw_search(product_name: str) -> dict:
    return search_product(product_name)


def cached_search(product_name: str) -> dict:
    """Busca com cache — descarta automaticamente resultados vazios."""
    result = _raw_search(product_name)
    has_any = any([
        result.get("potencia_w"), result.get("voltagem_v"),
        result.get("consumo_kwh"), result.get("btu"), result.get("fase"),
    ])
    if not has_any:
        _raw_search.clear()
    return result


# ─── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Busca de Especificacoes",
    page_icon="🔍",
    layout="wide",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .main-title { font-size: 2rem; font-weight: 700; margin-bottom: 0.2rem; }
    .sub-title { font-size: 1rem; color: #888; margin-bottom: 2rem; }
    div[data-testid="stMetric"] {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 1rem;
    }
    .ai-estimate {
        background: linear-gradient(90deg, #fff3e0, #ffe0b2);
        border-left: 4px solid #ff9800;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        margin: 0.3rem 0;
        font-size: 0.85rem;
    }
    .ai-badge {
        background: #e3f2fd;
        color: #1565c0;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ─── Session State ────────────────────────────────────────────────────────────

if "history" not in st.session_state:
    st.session_state.history = []
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "last_single_result" not in st.session_state:
    st.session_state.last_single_result = None
if "last_batch_results" not in st.session_state:
    st.session_state.last_batch_results = None

# ─── Header ───────────────────────────────────────────────────────────────────

st.markdown('<p class="main-title">Busca de Especificacoes de Equipamentos</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Potencia (W) | Voltagem (V) | Consumo (kWh) | BTU</p>', unsafe_allow_html=True)

# ─── Tabs ─────────────────────────────────────────────────────────────────────

tabs = ["Busca Individual", "Busca em Lote", "Historico"]
if HAS_GEMINI:
    tabs.append("Assistente IA")

tab_objects = st.tabs(tabs)
tab_single = tab_objects[0]
tab_batch = tab_objects[1]
tab_history = tab_objects[2]
tab_ai = tab_objects[3] if HAS_GEMINI else None

# ─── Helper: render spec with AI tag ─────────────────────────────────────────

def _google_verify_url(product: str, spec_label: str, spec_value: str) -> str:
    from urllib.parse import quote_plus as qp
    query = f"{product} {spec_label} {spec_value} especificações técnicas"
    return f"https://www.google.com/search?q={qp(query)}"


def render_metric(label, value, fonte=None, product_name=None):
    """Renderiza metrica com badge se for estimativa IA."""
    if value and "(estimativa IA)" in str(value):
        clean_val = str(value).replace(" (estimativa IA)", "")
        st.metric(label, clean_val)
        st.markdown('<span class="ai-badge">Estimativa IA</span>', unsafe_allow_html=True)
        if product_name:
            url = _google_verify_url(product_name, label, clean_val)
            st.caption(f"[Verificar no Google]({url})")
    else:
        st.metric(label, value or "Nao encontrada")
    if fonte and fonte != "Estimativa Google Gemini":
        st.caption(f"[Fonte]({fonte})")


# ─── Tab 1: Busca Individual ─────────────────────────────────────────────────

with tab_single:
    col_input, col_btn = st.columns([4, 1])

    with col_input:
        product_name = st.text_input(
            "Nome do equipamento",
            placeholder="Ex: Imbera EVZ21, Forno Venancio, Ar Condicionado Elgin 12000 BTU...",
            label_visibility="collapsed",
        )

    with col_btn:
        search_clicked = st.button("Buscar", type="primary", use_container_width=True)

    if search_clicked and product_name.strip():
        start = time.time()
        pname = product_name.strip()

        ai_result = None
        if tavily_client and HAS_GEMINI:
            with st.spinner(f"Buscando **{pname}** com IA (rapido)..."):
                ai_result = enrich_with_ai({"produto": pname})
                ai_elapsed = time.time() - start

            if ai_result and any([
                ai_result.get("potencia_w"), ai_result.get("voltagem_v"),
                ai_result.get("consumo_kwh"), ai_result.get("btu"),
                ai_result.get("fase"), ai_result.get("consumo_gas"),
            ]):
                st.success(f"IA encontrou dados em {ai_elapsed:.0f}s — confirmando com scraper...")

        with st.spinner(f"Confirmando em sites de varejo/fabricantes... (pode levar 1-2 min)"):
            result = cached_search(pname)
            elapsed = time.time() - start

        if ai_result:
            for key in ["potencia_w", "voltagem_v", "fase", "consumo_kwh", "btu", "consumo_gas"]:
                fonte_key = f"fonte_{key.replace('_w','').replace('_v','').replace('_kwh','')}"
                if key == "potencia_w":
                    fonte_key = "fonte_potencia"
                elif key == "voltagem_v":
                    fonte_key = "fonte_voltagem"
                elif key == "consumo_kwh":
                    fonte_key = "fonte_consumo"
                elif key == "consumo_gas":
                    fonte_key = "fonte_consumo_gas"
                elif key == "btu":
                    fonte_key = "fonte_btu"
                elif key == "fase":
                    fonte_key = "fonte_fase"

                if result.get(key):
                    pass
                elif ai_result.get(key):
                    result[key] = ai_result[key]
                    result[fonte_key] = ai_result.get(fonte_key, "")

        st.session_state.last_single_result = result
        history_entry = {
            **result,
            "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "tempo_busca": f"{elapsed:.0f}s",
        }
        st.session_state.history.insert(0, history_entry)
        append_to_persistent_history(history_entry)

        st.success(f"Busca concluida em {elapsed:.0f} segundos")

        _pname = result.get("produto", "")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            render_metric("Potencia", result.get("potencia_w"), result.get("fonte_potencia"), _pname)
        with col2:
            render_metric("Voltagem", result.get("voltagem_v"), result.get("fonte_voltagem"), _pname)
        with col3:
            render_metric("Fase", result.get("fase"), result.get("fonte_fase"), _pname)
        with col4:
            render_metric("Consumo", result.get("consumo_kwh") or result.get("consumo_gas"), result.get("fonte_consumo") or result.get("fonte_consumo_gas"), _pname)
        with col5:
            render_metric("BTU/kcal", result.get("btu"), result.get("fonte_btu"), _pname)
        with col6:
            if result.get("consumo_gas"):
                render_metric("Gas", result.get("consumo_gas"), result.get("fonte_consumo_gas"), _pname)

        if HAS_GEMINI:
            if st.button("Analisar com IA", key="analyze_single", type="secondary"):
                with st.spinner("Gerando analise com IA..."):
                    analysis = analyze_single(result)
                st.markdown("---")
                st.markdown("### Analise do Equipamento")
                st.markdown(analysis)

    elif search_clicked:
        st.warning("Digite o nome de um equipamento para buscar.")

    if not search_clicked and st.session_state.last_single_result and HAS_GEMINI:
        result = st.session_state.last_single_result
        _pname = result.get("produto", "")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            render_metric("Potencia", result.get("potencia_w"), result.get("fonte_potencia"), _pname)
        with col2:
            render_metric("Voltagem", result.get("voltagem_v"), result.get("fonte_voltagem"), _pname)
        with col3:
            render_metric("Fase", result.get("fase"), result.get("fonte_fase"), _pname)
        with col4:
            render_metric("Consumo", result.get("consumo_kwh") or result.get("consumo_gas"), result.get("fonte_consumo") or result.get("fonte_consumo_gas"), _pname)
        with col5:
            render_metric("BTU/kcal", result.get("btu"), result.get("fonte_btu"), _pname)
        with col6:
            if result.get("consumo_gas"):
                render_metric("Gas", result.get("consumo_gas"), result.get("fonte_consumo_gas"), _pname)

        if st.button("Analisar com IA", key="analyze_single_persist", type="secondary"):
            with st.spinner("Gerando analise com IA..."):
                analysis = analyze_single(result)
            st.markdown("---")
            st.markdown("### Analise do Equipamento")
            st.markdown(analysis)


# ─── Tab 2: Busca em Lote ────────────────────────────────────────────────────

with tab_batch:
    st.markdown("Adicione um equipamento por linha ou faca upload de um arquivo `.txt` / `.csv`.")

    upload_col, text_col = st.columns(2)

    with upload_col:
        uploaded = st.file_uploader("Upload de arquivo", type=["txt", "csv"])

    with text_col:
        batch_text = st.text_area(
            "Ou cole a lista aqui (um por linha)",
            height=150,
            placeholder="Imbera EVZ21 Full Black\nForno Venancio FIRI100\nAr Condicionado Elgin 12000 BTU",
        )

    batch_products = []

    if uploaded:
        content = uploaded.read().decode("utf-8", errors="replace")
        batch_products = [line.strip() for line in content.splitlines() if line.strip()]
    elif batch_text.strip():
        batch_products = [line.strip() for line in batch_text.strip().splitlines() if line.strip()]

    if batch_products:
        st.info(f"**{len(batch_products)}** equipamento(s) na lista")

        if st.button("Buscar Todos", type="primary", key="batch_btn"):
            results = []
            progress = st.progress(0, text="Iniciando buscas...")
            status_container = st.empty()

            for i, prod in enumerate(batch_products):
                progress.progress(
                    (i) / len(batch_products),
                    text=f"Buscando [{i+1}/{len(batch_products)}]: {prod}",
                )
                status_container.info(f"Buscando: **{prod}**... (pode levar 1-2 min)")

                start = time.time()

                ai_res = None
                if tavily_client and HAS_GEMINI:
                    ai_res = enrich_with_ai({"produto": prod})

                result = cached_search(prod)
                elapsed = time.time() - start

                if ai_res:
                    for key in ["potencia_w", "voltagem_v", "fase", "consumo_kwh", "btu", "consumo_gas"]:
                        fk = {"potencia_w": "fonte_potencia", "voltagem_v": "fonte_voltagem",
                              "consumo_kwh": "fonte_consumo", "consumo_gas": "fonte_consumo_gas",
                              "btu": "fonte_btu", "fase": "fonte_fase"}.get(key, "")
                        if not result.get(key) and ai_res.get(key):
                            result[key] = ai_res[key]
                            result[fk] = ai_res.get(fk, "")

                result["tempo_busca"] = f"{elapsed:.0f}s"
                result["data_hora"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                results.append(result)
                st.session_state.history.insert(0, result)
                append_to_persistent_history(result)

            progress.progress(1.0, text="Concluido!")
            status_container.success(f"Busca concluida! {len(results)} equipamento(s) processado(s).")

            st.session_state.last_batch_results = results

            df = pd.DataFrame(results)
            display_cols = {
                "produto": "Equipamento",
                "potencia_w": "Potencia",
                "voltagem_v": "Voltagem",
                "fase": "Fase",
                "consumo_kwh": "Consumo (kWh)",
                "consumo_gas": "Consumo Gas",
                "btu": "BTU/kcal",
                "fonte_potencia": "Fonte Potencia",
                "fonte_voltagem": "Fonte Voltagem",
                "tempo_busca": "Tempo",
            }
            df_display = df[[c for c in display_cols if c in df.columns]].rename(columns=display_cols)
            st.dataframe(df_display, use_container_width=True)

            csv_buf = io.StringIO()
            df_display.to_csv(csv_buf, index=False, encoding="utf-8-sig")
            st.download_button(
                "Baixar CSV",
                csv_buf.getvalue(),
                file_name=f"especificacoes_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )

            if HAS_GEMINI and len(results) >= 2:
                if st.button("Comparar com IA", key="compare_batch", type="secondary"):
                    with st.spinner("Gerando comparacao com IA..."):
                        comparison = compare_multiple(results)
                    st.markdown("---")
                    st.markdown("### Comparacao de Equipamentos")
                    st.markdown(comparison)

    if st.session_state.last_batch_results and HAS_GEMINI and not batch_products:
        results = st.session_state.last_batch_results
        if len(results) >= 2:
            st.markdown(f"**Ultima busca em lote:** {len(results)} equipamento(s)")
            if st.button("Comparar com IA", key="compare_persist", type="secondary"):
                with st.spinner("Gerando comparacao com IA..."):
                    comparison = compare_multiple(results)
                st.markdown("---")
                st.markdown("### Comparacao de Equipamentos")
                st.markdown(comparison)


# ─── Tab 3: Historico ────────────────────────────────────────────────────────

with tab_history:
    display_cols = {
        "produto": "Equipamento",
        "potencia_w": "Potencia",
        "voltagem_v": "Voltagem",
        "fase": "Fase",
        "consumo_kwh": "Consumo (kWh)",
        "consumo_gas": "Consumo Gas",
        "btu": "BTU/kcal",
        "fonte_potencia": "Fonte Potencia",
        "fonte_voltagem": "Fonte Voltagem",
        "data_hora": "Data/Hora",
    }

    hist_tab_session, hist_tab_global = st.tabs(["Sessao atual", "Historico completo"])

    with hist_tab_session:
        if st.session_state.history:
            st.markdown(f"**{len(st.session_state.history)}** busca(s) nesta sessao")
            df_hist = pd.DataFrame(st.session_state.history)
            available = [c for c in display_cols if c in df_hist.columns]
            df_display = df_hist[available].rename(columns=display_cols)
            st.dataframe(df_display, use_container_width=True)
        else:
            st.info("Nenhuma busca nesta sessao.")

    with hist_tab_global:
        if GITHUB_TOKEN:
            if st.button("Atualizar historico", type="secondary"):
                _load_history_from_github.clear()

            df_global = _load_history_from_github()
            if not df_global.empty:
                st.markdown(f"**{len(df_global)}** busca(s) registrada(s) no total")
                available = [c for c in display_cols if c in df_global.columns]
                df_gdisp = df_global[available].rename(columns=display_cols)
                st.dataframe(df_gdisp, use_container_width=True)

                csv_buf = io.StringIO()
                df_gdisp.to_csv(csv_buf, index=False, encoding="utf-8-sig")
                st.download_button(
                    "Baixar historico completo (CSV)",
                    csv_buf.getvalue(),
                    file_name=f"historico_completo_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                )
            else:
                st.info("Nenhuma busca registrada ainda.")
        else:
            st.warning("Historico persistente nao configurado. Adicione GITHUB_TOKEN nos Secrets.")
            st.caption("Veja o GUIA_MANUTENCAO.md para instruções.")


# ─── Tab 4: Assistente IA ────────────────────────────────────────────────────

if tab_ai:
    with tab_ai:
        st.markdown(
            "Pergunte qualquer coisa sobre equipamentos. "
            "A IA pode buscar dados reais automaticamente e complementar com seu conhecimento."
        )

        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        st.markdown(
            '> **Dica:** A IA responde na hora com seu conhecimento. '
            'Para buscar dados reais em sites, use as abas "Busca Individual" ou "Busca em Lote".'
        )

        if prompt := st.chat_input("Pergunte sobre equipamentos... (ex: Qual a potencia do forno Venancio FIRI100?)"):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                history_context = ""
                recent = st.session_state.chat_messages[-10:]
                for msg in recent:
                    history_context += f"{msg['role']}: {msg['content']}\n"

                scraper_context = ""
                if st.session_state.history:
                    clean_history = []
                    for item in st.session_state.history[:5]:
                        has_spec = any([
                            item.get("potencia_w"), item.get("voltagem_v"),
                            item.get("consumo_kwh"), item.get("btu"), item.get("fase"),
                        ])
                        if has_spec:
                            clean_history.append({
                                "produto": item.get("produto"),
                                "potencia_w": item.get("potencia_w"),
                                "voltagem_v": item.get("voltagem_v"),
                                "fase": item.get("fase"),
                                "consumo_kwh": item.get("consumo_kwh"),
                                "btu": item.get("btu"),
                            })
                    if clean_history:
                        scraper_context = (
                            "Dados de buscas recentes do scraper (dados reais de sites):\n"
                            + json.dumps(clean_history, ensure_ascii=False, indent=2)
                        )

                full_context = ""
                if scraper_context:
                    full_context += scraper_context + "\n\n"
                if history_context:
                    full_context += f"Historico da conversa:\n{history_context}\n"

                with st.spinner("Pensando..."):
                    answer = ask_gemini(prompt, context=full_context)
                st.markdown(answer)

            st.session_state.chat_messages.append({"role": "assistant", "content": answer})

        if st.session_state.chat_messages:
            if st.button("Limpar conversa", key="clear_chat"):
                st.session_state.chat_messages = []
                st.rerun()


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Como usar")
    st.markdown(
        "1. Digite o nome do equipamento\n"
        "2. Clique em **Buscar**\n"
        "3. Aguarde 1-2 minutos\n"
        "4. Veja os resultados\n"
    )
    if HAS_GEMINI:
        st.markdown("### Assistente IA")
        st.markdown(
            "- Pergunte em linguagem natural\n"
            "- A IA busca dados reais + complementa\n"
            "- Compare equipamentos\n"
            "- Peca analises e recomendacoes\n"
        )
    st.markdown("### Exemplos")
    st.code(
        "Imbera EVZ21 Full Black\n"
        "Metalfrio VN50AH\n"
        "Forno Venancio FIRI100\n"
        "Ar Condicionado Elgin Eco 12000 BTU\n"
        "Coifa Nardelli 90cm\n"
        "Fritadeira Croydon FC2A",
        language=None,
    )

    st.markdown("---")
    if st.button("Limpar cache de buscas"):
        cached_search.clear()
        st.session_state.history = []
        st.success("Cache limpo!")
        st.rerun()
    if HAS_GEMINI:
        st.success("IA ativa (Llama 3.3)")
    else:
        st.warning("IA desativada")
        st.caption("Adicione GROQ_API_KEY no .env")
    if tavily_client:
        st.success("Tavily ativo (fontes reais)")
    else:
        st.info("Tavily desativado")
        st.caption("Adicione TAVILY_API_KEY nos Secrets")
    st.caption("Busca de Especificacoes v2.1")
