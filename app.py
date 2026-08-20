import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import requests

# 1. CONFIGURAÇÃO DA PÁGINA (Deve ser o primeiro comando Streamlit)
st.set_page_config(
    page_title="Observatório de Parcerias UFMS",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. FUNÇÃO PARA CARREGAR DADOS REAIS DA API FEDERAL
@st.cache_data(ttl=3600)
def carregar_dados_reais():
    api_key = st.secrets.get("TRANSPARENCIA_API_KEY", None)
    if not api_key:
        return pd.DataFrame()

    url = "https://api.portaldatransparencia.gov.br/api-de-dados/convenios"
    headers = {"chave-api-dados": api_key}
    
    # Exemplo requisitando a primeira página de convênios da UFMS
    params = {
        "cnpjConvenente": "15424215000108",  # CNPJ da UFMS
        "pagina": 1
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            dados = response.json()
            if not dados:
                return pd.DataFrame()

            registros = []
            for item in dados:
                data_ini = item.get("dataInicioVigencia", "")
                
                # Extrai o ano da data (formato padrão DD/MM/YYYY na API)
                try:
                    ano = int(data_ini.split("/")[-1]) if data_ini else datetime.now().year
                except ValueError:
                    ano = datetime.now().year

                registros.append({
                    "id_termo": str(item.get("numero", "N/A")),
                    "modalidade": item.get("tipoInstrumento", "Convênio"),
                    "parceiro": item.get("concedente", {}).get("nome", "Não informado"),
                    "valor_global": float(item.get("valor", 0.0)),
                    "status": str(item.get("situacao", "N/A")).upper(),
                    "data_inicio": data_ini,
                    "data_fim": item.get("dataFimVigencia", ""),
                    "objeto": item.get("objeto", "Sem descrição disponível"),
                    "ano": ano,
                    "auditoria": "Verificado (API Federal)"
                })
            return pd.DataFrame(registros)
        else:
            return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# 3. FUNÇÃO PARA GERAR DADOS SIMULADOS (MOCK)
@st.cache_data
def gerar_dados_simulados(n=120):
    np.random.seed(42)
    
    modalidades = ["Convênio", "TED", "Acordo de Cooperação", "Contrato de Gestão"]
    status_list = ["VIGENTE", "CONCLUÍDO", "RESCINDIDO"]
    parceiros = ["FAAPEC", "MEC", "MCTI", "FINEP", "CNPq", "Itaipu Binacional", "Prefeitura de Campo Grande"]
    auditoria_status = ["Consistente (API + DOU)", "Divergência de Valor", "Apenas no SEI (Sem API)"]
    
    hoje = datetime.now()
    dados = []
    
    for i in range(1, n + 1):
        ano = np.random.choice([2021, 2022, 2023, 2024, 2025, 2026], p=[0.1, 0.15, 0.2, 0.25, 0.2, 0.1])
        data_ini = datetime(ano, np.random.randint(1, 13), np.random.randint(1, 28))
        data_fim = data_ini + timedelta(days=np.random.randint(180, 1460))
        
        status = "VIGENTE" if data_fim > hoje else np.random.choice(["CONCLUÍDO", "RESCINDIDO"], p=[0.9, 0.1])
        modalidade = np.random.choice(modalidades, p=[0.4, 0.3, 0.2, 0.1])
        valor = 0.0 if modalidade == "Acordo de Cooperação" else float(np.random.lognormal(mean=11.5, sigma=1.2))
        
        dados.append({
            "id_termo": f"{i:03d}/{ano}",
            "modalidade": modalidade,
            "objeto": f"Projeto de P&D/Extensão de Teste nº {i} focado em inovação regional.",
            "parceiro": np.random.choice(parceiros),
            "valor_global": round(valor, 2),
            "data_inicio": data_ini.strftime("%d/%m/%Y"),
            "data_fim": data_fim.strftime("%d/%m/%Y"),
            "status": status,
            "ano": int(ano),
            "auditoria": np.random.choice(auditoria_status, p=[0.75, 0.15, 0.10])
        })
        
    return pd.DataFrame(dados)

# 4. ORQUESTRAÇÃO DA CARGA DE DADOS
df_raw = carregar_dados_reais()

if df_raw.empty:
    st.info("ℹ️ **Modo de Demonstração (Dados Fictícios)**: Para carregar dados reais, cadastre a chave `TRANSPARENCIA_API_KEY` em **Settings > Secrets** no Streamlit Cloud.")
    df_raw = gerar_dados_simulados()
else:
    st.success("✅ **Conexão Estabelecida**: Dados reais carregados diretamente da API do Portal da Transparência!")

# 5. BARRA LATERAL (FILTROS)
st.sidebar.image("https://www.ufms.br/wp-content/uploads/2022/09/UFMS_POS-1.png", width=180)
st.sidebar.title("Filtros do Painel")

min_ano = int(df_raw['ano'].min())
max_ano = int(df_raw['ano'].max())

ano_selecionado = st.sidebar.slider(
    "Intervalo de Anos", 
    min_value=min_ano, 
    max_value=max_ano, 
    value=(min_ano, max_ano)
)

modalidade_filtro = st.sidebar.multiselect(
    "Modalidade", 
    options=df_raw['modalidade'].unique(), 
    default=df_raw['modalidade'].unique()
)

status_filtro = st.sidebar.multiselect(
    "Status do Instrumento", 
    options=df_raw['status'].unique(), 
    default=df_raw['status'].unique()
)

auditoria_filtro = st.sidebar.multiselect(
    "Status da Auditoria", 
    options=df_raw['auditoria'].unique(), 
    default=df_raw['auditoria'].unique()
)

# Aplicação dos Filtros
df_filtrado = df_raw[
    (df_raw['ano'] >= ano_selecionado[0]) & 
    (df_raw['ano'] <= ano_selecionado[1]) &
    (df_raw['modalidade'].isin(modalidade_filtro)) &
    (df_raw['status'].isin(status_filtro)) &
    (df_raw['auditoria'].isin(auditoria_filtro))
]

# 6. CABEÇALHO PRINCIPAL
st.title("📊 Observatório Independente de Parcerias — UFMS")
st.caption("Painel acadêmico de transparência passiva via cruzamento de Dados Abertos e DOU.")
st.markdown("---")

# 7. CARTÕES DE MÉTRICAS (KPIs)
col1, col2, col3, col4 = st.columns(4)

total_recursos = df_filtrado['valor_global'].sum()
total_acordos = len(df_filtrado)
acordos_vigentes = len(df_filtrado[df_filtrado['status'] == 'VIGENTE'])
qtd_auditados = len(df_filtrado[df_filtrado['auditoria'].str.contains("Verificado|Consistente", case=False, na=False)])
taxa_consistencia = (qtd_auditados / total_acordos * 100) if total_acordos > 0 else 0

col1.metric("Montante Captado", f"R$ {total_recursos:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col2.metric("Total de Instrumentos", total_acordos)
col3.metric("Acordos Vigentes", acordos_vigentes)
col4.metric("Consistência dos Dados", f"{taxa_consistencia:.1f}%")

st.markdown("---")

# 8. VISUALIZAÇÕES GRÁFICAS E TABELA
tab_graficos, tab_tabela = st.tabs(["📈 Análises Gráficas", "📋 Tabela Detalhada & Auditoria"])

with tab_graficos:
    if not df_filtrado.empty:
        g_col1, g_col2 = st.columns(2)
        
        with g_col1:
            df_ano_mod = df_filtrado.groupby(['ano', 'modalidade'])['valor_global'].sum().reset_index()
            fig_evolucao = px.bar(
                df_ano_mod, 
                x='ano', 
                y='valor_global', 
                color='modalidade', 
                title="Evolução Anual de Recursos por Modalidade (R$)",
                labels={'valor_global': 'Valor (R$)', 'ano': 'Ano'},
                barmode='stack'
            )
            st.plotly_chart(fig_evolucao, use_container_width=True)

        with g_col2:
            fig_auditoria = px.pie(
                df_filtrado, 
                names='auditoria', 
                title="Distribuição do Status de Validação Cruzada",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig_auditoria, use_container_width=True)

        df_parceiros = df_filtrado.groupby('parceiro')['valor_global'].sum().reset_index().sort_values(by='valor_global', ascending=True)
        fig_parceiros = px.bar(
            df_parceiros, 
            x='valor_global', 
            y='parceiro', 
            orientation='h', 
            title="Volume Financeiro por Ente Parceiro / Financiador",
            labels={'valor_global': 'Total Acumulado (R$)', 'parceiro': 'Parceiro'}
        )
        st.plotly_chart(fig_parceiros, use_container_width=True)
    else:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")

with tab_tabela:
    st.subheader("Base Cruzada de Instrumentos Celebrações")
    
    termo_busca = st.text_input("🔍 Buscar por objeto, parceiro ou número do termo:")
    
    df_exibicao = df_filtrado.copy()
    if termo_busca and not df_exibicao.empty:
        df_exibicao = df_exibicao[
            df_exibicao['objeto'].str.contains(termo_busca, case=False, na=False) |
            df_exibicao['parceiro'].str.contains(termo_busca, case=False, na=False) |
            df_exibicao['id_termo'].str.contains(termo_busca, case=False, na=False)
        ]
    
    st.dataframe(
        df_exibicao[[
            "id_termo", "modalidade", "parceiro", "valor_global", 
            "status", "auditoria", "data_inicio", "data_fim", "objeto"
        ]],
        column_config={
            "id_termo": "Nº Termo",
            "modalidade": "Modalidade",
            "parceiro": "Parceiro / Financiador",
            "valor_global": st.column_config.NumberColumn("Valor Global (R$)", format="R$ %.2f"),
            "status": "Status",
            "auditoria": "Auditoria",
            "data_inicio": "Início",
            "data_fim": "Término",
            "objeto": "Objeto do Acordo"
        },
        hide_index=True,
        use_container_width=True
    )

    csv_data = df_exibicao.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar Dados Filtrados em CSV",
        data=csv_data,
        file_name=f"parcerias_ufms_auditadas_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
