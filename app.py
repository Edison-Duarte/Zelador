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
ARQUIVO = 'historico_zelador.csv'

def salvar_no_historico(dados):
    df_novo = pd.DataFrame([dados])
    if os.path.exists(ARQUIVO):
        # Usamos sep=';' e quoting para evitar erro de leitura posterior
        df_novo.to_csv(ARQUIVO, mode='a', index=False, header=False, sep=';')
    else:
        df_novo.to_csv(ARQUIVO, index=False, sep=';')

def carregar_historico():
    if os.path.exists(ARQUIVO):
        try:
            # on_bad_lines='skip' evita que o app trave se houver uma linha corrompida
            df = pd.read_csv(ARQUIVO, sep=';', on_bad_lines='skip')
            if 'Detalhes' not in df.columns:
                df['Detalhes'] = "Sem detalhes"
            return df
        except Exception:
            # Se o arquivo estiver muito corrompido, ele retorna um erro amigável
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
                            # Removemos pontos e vírgulas das observações para não quebrar o CSV
                            obs_limpa = (obs if obs else "Pendente").replace(";", ",")
                            nao_conformidades.append(f"[{bloco}-{area}] {obs_limpa} (Ação: {correcao})")

        if st.button("Finalizar e Salvar"):
            resumo_status = "OK" if not nao_conformidades else f"{len(nao_conformidades)} Pendências"
            texto_detalhes = " / ".join(nao_conformidades) if nao_conformidades else "Tudo em conformidade"
            
            salvar_no_historico({
                "Data": data_atual,
                "Inspetor": inspetor,
                "Status": resumo_status,
                "Detalhes": texto_detalhes
            })
            st.success("Inspeção Concluída!")
            st.rerun()

with aba_historico:
    st.title("📊 Histórico")
    df_hist = carregar_historico()
    
    if df_hist is not None:
        st.dataframe(df_hist[["Data", "Inspetor", "Status"]], use_container_width=True)
        
        st.markdown("---")
        st.subheader("🔍 Detalhes das Pendências")
        
        pendentes = df_hist[df_hist['Status'].str.contains("Pendências", na=False)]
        
        if not pendentes.empty:
            escolha = st.selectbox("Selecione a inspeção:", pendentes.index, 
                                    format_func=lambda x: f"{df_hist.loc[x, 'Data']} - {df_hist.loc[x, 'Inspetor']}")
            
            if st.button("👁️ Ver Pendências"):
                conteudo = df_hist.loc[escolha, 'Detalhes'].replace(" / ", "\n")
                st.warning(f"**Relatório:**\n\n{conteudo}")
        
        with st.expander("🛠️ Gerenciar"):
            senha = st.text_input("Senha:", type="password")
            if senha == "flats":
                if st.button("🚨 APAGAR TUDO E RESETAR"):
                    if os.path.exists(ARQUIVO):
                        os.remove(ARQUIVO)
                        st.success("Arquivo resetado! O erro deve sumir.")
                        st.rerun()
    else:
        st.info("Nenhum dado encontrado ou arquivo corrompido. Tente salvar uma nova inspeção.")
