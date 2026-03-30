import os
import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

st.set_page_config(page_title="Bruniera - Gestão Jurídica", layout="wide")

st.title("⚖️ Sistema de Gerenciamento Bruniera")

# Obter URL e Key do .env
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("As variáveis de ambiente SUPABASE_URL e SUPABASE_KEY não foram encontradas no arquivo .env")
    st.stop()

# Conectar ao Supabase usando as chaves seguras
conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url=SUPABASE_URL,
    key=SUPABASE_KEY,
)

st.markdown("---")

st.subheader("📊 Painel Geral")

# ... rest of the code (I'll keep the logic the same as app_v2_4.py)
# Note: I'll use the original logic from the file I read earlier.

col1, col2, col3, col4 = st.columns(4)

total_processos = conn.table("processos").select("id", count="exact").execute().count
ativos = conn.table("processos").select("id", count="exact").eq("status","Ativo").execute().count
encerrados = conn.table("processos").select("id", count="exact").eq("status","Encerrado").execute().count
suspensos = conn.table("processos").select("id", count="exact").eq("status","Suspenso").execute().count

col1.metric("⚖ Total de Processos", total_processos)
col2.metric("📂 Ativos", ativos)
col3.metric("📁 Encerrados", encerrados)
col4.metric("⏸ Suspensos", suspensos)

st.markdown("---")

st.subheader("👨‍⚖ Processos por Responsável")

responsaveis_df = conn.table("processos").select("responsavel").execute()
df_resp = pd.DataFrame(responsaveis_df.data)
contagem = df_resp["responsavel"].value_counts()
st.bar_chart(contagem)

responsaveis = ["Todos", "Marcia", "Debora", "Victor", "Carmem", "Miguel", "Caroline", "Carolina"]

# CONTROLE DE PÁGINA
if "processo_selecionado" not in st.session_state:
    st.session_state.processo_selecionado = None

# PÁGINA DO PROCESSO
if st.session_state.processo_selecionado:
    processo = st.session_state.processo_selecionado
    st.button("⬅ Voltar", on_click=lambda: st.session_state.update({"processo_selecionado": None}))
    st.header(f"📂 Processo {processo['numero_processo']}")
    col1, col2, col3 = st.columns(3)
    col1.write(f"**Autor:** {processo['autor']}")
    col2.write(f"**Comarca:** {processo['comarca']}")
    col3.write(f"**Responsável:** {processo['responsavel']}")
    st.write(f"**Sinistro:** {processo['sinistro_allianz']}")
    st.write(f"**Status:** {processo['status']}")
    st.markdown("---")
    st.subheader("📜 Histórico de Andamentos")
    andamento_query = conn.table("andamentos").select("*").eq("processo_id", processo["id"]).order("data_registro", desc=True, nulls_last=True).execute()
    if andamento_query.data:
        df_andamentos = pd.DataFrame(andamento_query.data)
        for _, andamento in df_andamentos.iterrows():
            st.markdown(f"**{andamento['data_registro']}**  \n{andamento['descricao']}  \n_Responsável: {andamento['responsavel_nome']}_")
            st.divider()
    else:
        st.info("Nenhum andamento registrado.")

    st.markdown("---")
    st.subheader("➕ Adicionar Andamento")
    with st.form("novo_andamento"):
        descricao = st.text_area("Descrição do Andamento")
        responsavel_nome = st.selectbox("Responsável", responsaveis[1:])
        salvar_andamento = st.form_submit_button("Salvar Andamento")
        if salvar_andamento and descricao.strip():
            novo_andamento = {"processo_id": processo["id"], "descricao": descricao, "responsavel_nome": responsavel_nome}
            conn.table("andamentos").insert(novo_andamento).execute()
            st.success("Andamento registrado!")
            st.rerun()

# LISTA DE PROCESSOS
st.sidebar.header("Filtros")
busca = st.sidebar.text_input("Buscar por Processo ou Sinistro")
responsavel_filtro = st.sidebar.selectbox("Responsável", responsaveis)
status_filtro = st.sidebar.selectbox("Status", ["Todos", "Ativo", "Encerrado", "Suspenso"])

query = conn.table("processos").select("*").range(0, 2000)
if status_filtro != "Todos":
    query = query.eq("status", status_filtro)
if busca:
    query = query.or_(f"numero_processo.ilike.%{busca}%,sinistro_allianz.ilike.%{busca}%")
if responsavel_filtro != "Todos":
    query = query.eq("responsavel", responsavel_filtro)

dados = query.execute()
if dados.data:
    df = pd.DataFrame(dados.data)
    st.subheader("📂 Processos")
    for _, row in df.iterrows():
        col1, col2 = st.columns([4, 1])
        col1.write(f"**{row['numero_processo']}** | {row['autor']} | {row['comarca']} | {row['responsavel']}")
        if col2.button("Abrir", key=row["id"]):
            st.session_state.processo_selecionado = row
            st.rerun()
else:
    st.info("Nenhum processo encontrado.")

st.markdown("---")
st.subheader("➕ Cadastrar Novo Processo")
with st.form("novo_processo_full"):
    col1, col2 = st.columns(2)
    with col1:
        n_proc = st.text_input("Número do Processo")
        n_sin = st.text_input("Número do Sinistro")
        n_aut = st.text_input("Autor")
        n_com = st.text_input("Comarca")
        n_ins = st.text_input("Instância")
    with col2:
        n_uf = st.selectbox("UF", ["RJ","SP","MG","ES","RS","SC","PR","BA","PE","CE"])
        n_resp = st.selectbox("Responsável", responsaveis[1:], key="resp_cadastro")
        n_stat = st.selectbox("Status", ["Ativo","Encerrado","Suspenso"])
        n_prazo = st.date_input("Prazo de Vencimento")
    
    salvar = st.form_submit_button("Salvar Processo")
    if salvar:
        novo = {
            "numero_processo": n_proc,
            "sinistro_allianz": n_sin,
            "autor": n_aut,
            "comarca": n_com,
            "instancia": n_ins,
            "uf": n_uf,
            "responsavel": n_resp,
            "status": n_stat,
            "prazo_vencimento": n_prazo.isoformat() if n_prazo else None
        }
        conn.table("processos").insert(novo).execute()
        st.success("Processo cadastrado!")
        st.rerun()
