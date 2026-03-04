import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="App Zelador", page_icon="🏢")

if 'modo_edicao' not in st.session_state:
    st.session_state.modo_edicao = False

ARQUIVO = 'historico_zelador.csv'

# --- FUNÇÕES DE PERSISTÊNCIA ---
def salvar_no_historico(dados):
    df_novo = pd.DataFrame([dados])
    # Usamos o separador ";" que é mais seguro para textos com vírgulas
    if os.path.exists(ARQUIVO):
        df_novo.to_csv(ARQUIVO, mode='a', index=False, header=False, sep=';')
    else:
        df_novo.to_csv(ARQUIVO, index=False, sep=';')

def carregar_historico():
    if os.path.exists(ARQUIVO):
        try:
            df = pd.read_csv(ARQUIVO, sep=';', on_bad_lines='skip')
            # Garante que todas as colunas necessárias existam para não dar KeyError
            colunas_necessarias = ["Data", "Inspetor", "Status", "Detalhes"]
            for col in colunas_necessarias:
                if col not in df.columns:
                    df[col] = "N/A"
            return df
        except:
            return None
    return None

# --- INTERFACE EM ABAS ---
aba_inspecao, aba_historico = st.tabs(["📋 Nova Inspeção", "📊 Histórico de Inspeções"])

with aba_inspecao:
    st.title("🏢 Sistema de Inspeção")
    inspetor = st.text_input("Nome do Responsável:")
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    if not inspetor:
        st.info("Identifique-se para começar.")
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
                            # Limpeza de texto para não quebrar o CSV
                            obs_limpa = (obs if obs else "Pendente").replace(";", "-")
                            nao_conformidades.append(f"[{bloco}-{area}] {obs_limpa} (Ação: {correcao})")

        if st.button("Finalizar e Salvar"):
            resumo_status = "OK" if not nao_conformidades else f"{len(nao_conformidades)} Pendências"
            texto_detalhes = " / ".join(nao_conformidades) if nao_conformidades else "Tudo em conformidade"
            
            salvar_no_historico({
                "Data": data_atual, "Inspetor": inspetor, "Status": resumo_status, "Detalhes": texto_detalhes
            })
            st.success("Inspeção Salva!")
            st.rerun()

with aba_historico:
    st.title("📊 Histórico")
    df_hist = carregar_historico()
    
    if df_hist is not None and not df_hist.empty:
        # Tenta exibir apenas as colunas principais
        try:
            st.dataframe(df_hist[["Data", "Inspetor", "Status"]], use_container_width=True)
            
            st.markdown("---")
            st.subheader("🔍 Visualizar Detalhes")
            
            # Filtra apenas linhas com pendências para o seletor
            pendentes = df_hist[df_hist['Status'].str.contains("Pendências", na=False)]
            
            if not pendentes.empty:
                escolha = st.selectbox("Selecione a inspeção:", pendentes.index, 
                                        format_func=lambda x: f"{df_hist.loc[x, 'Data']} - {df_hist.loc[x, 'Inspetor']}")
                
                if st.button("👁️ Ver O que foi pontuado"):
                    conteudo = df_hist.loc[escolha, 'Detalhes'].replace(" / ", "\n")
                    st.warning(f"**Relatório de Pendências:**\n\n{conteudo}")
        except KeyError:
            st.error("O arquivo de histórico está com formato incompatível.")
            if st.button("Tentar Corrigir Formato"):
                os.remove(ARQUIVO)
                st.rerun()

        # --- GERENCIAMENTO ---
        with st.expander("🛠️ Gerenciar"):
            senha = st.text_input("Senha:", type="password")
            if senha == "flats":
                if st.button("🚨 APAGAR TUDO E RESETAR"):
                    if os.path.exists(ARQUIVO):
                        os.remove(ARQUIVO)
                        st.success("Histórico resetado!")
                        st.rerun()
    else:
        st.info("Nenhum dado disponível. Realize uma nova inspeção.")
