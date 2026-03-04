import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="App Zelador", page_icon="🏢")

if 'modo_edicao' not in st.session_state:
    st.session_state.modo_edicao = False

# --- FUNÇÕES DE PERSISTÊNCIA ---
def salvar_no_historico(dados):
    arquivo = 'historico_zelador.csv'
    df_novo = pd.DataFrame([dados])
    if os.path.exists(arquivo):
        df_novo.to_csv(arquivo, mode='a', index=False, header=False)
    else:
        df_novo.to_csv(arquivo, index=False)

def carregar_historico():
    arquivo = 'historico_zelador.csv'
    if os.path.exists(arquivo):
        return pd.read_csv(arquivo)
    return None

# --- INTERFACE EM ABAS ---
aba_inspecao, aba_historico = st.tabs(["📋 Nova Inspeção", "📊 Histórico de Inspeções"])

with aba_inspecao:
    st.title("🏢 Sistema de Inspeção: Zelador")
    inspetor = st.text_input("Nome do Responsável:")
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    if not inspetor:
        st.info("Por favor, identifique-se.")
    else:
        areas = ["Recepção", "Elevadores", "Escadarias", "Corredores", "Corrimões", "Janelas", "Garagens"]
        blocos = ["Bloco A", "Bloco B"]
        nao_conformidades = []

        for bloco in blocos:
            with st.expander(f"📋 {bloco}", expanded=True):
                for area in areas:
                    col1, col2 = st.columns([2, 3])
                    with col1:
                        status = st.radio(f"{area}", ["Conforme", "Não Conforme"], key=f"{bloco}_{area}")
                    if status == "Não Conforme":
                        with col2:
                            correcao = st.selectbox("Ação:", ["Limpeza", "Reparo", "Troca", "Sinalizar"], key=f"c_{bloco}_{area}")
                            obs = st.text_input("Obs:", key=f"o_{bloco}_{area}")
                            nao_conformidades.append(f"[{bloco}-{area}] {obs} (Ação: {correcao})")

        if st.button("Finalizar"):
            detalhes = " | ".join(nao_conformidades) if nao_conformidades else "Tudo em ordem"
            resumo = "OK" if not nao_conformidades else f"{len(nao_conformidades)} Pendências"
            
            salvar_no_historico({
                "Data": data_atual,
                "Inspetor": inspetor,
                "Status": resumo,
                "Detalhes": detalhes  # Nova coluna para salvar o texto dos erros
            })
            st.success("Inspeção Salva!")
            st.rerun()

with aba_historico:
    st.title("📊 Histórico")
    df_hist = carregar_historico()
    
    if df_hist is not None:
        # Exibimos apenas as colunas principais na tabela principal
        st.dataframe(df_hist[["Data", "Inspetor", "Status"]], use_container_width=True)
        
        st.subheader("🔍 Ver Detalhes das Pendências")
        # Filtramos apenas as linhas que possuem pendências para mostrar no seletor
        pendentes = df_hist[df_hist['Status'] != "OK"]
        
        if not pendentes.empty:
            escolha = st.selectbox("Selecione uma inspeção para ver os detalhes:", 
                                    pendentes.index, 
                                    format_func=lambda x: f"{df_hist.loc[x, 'Data']} - {df_hist.loc[x, 'Inspetor']}")
            
            if st.button("👁️ Visualizar Pendências"):
                conteudo = df_hist.loc[escolha, 'Detalhes'].replace(" | ", "\n")
                st.info(f"**Relatório de Problemas:**\n\n{conteudo}")
        else:
            st.write("Nenhuma pendência registrada nos últimos relatórios.")

        # --- BOTÃO EDITAR (Oculto em expander para limpar a tela) ---
        with st.expander("🛠️ Gerenciar Dados"):
            if st.button("Ativar Modo Edição"):
                st.session_state.modo_edicao = not st.session_state.modo_edicao
            
            if st.session_state.modo_edicao:
                senha = st.text_input("Senha:", type="password")
                if senha == "flats":
                    if st.button("🚨 APAGAR TUDO"):
                        if os.path.exists('historico_zelador.csv'): os.remove('historico_zelador.csv')
                        st.rerun()
