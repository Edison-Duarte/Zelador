import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="App Zelador", page_icon="🏢")

if 'modo_edicao' not in st.session_state:
    st.session_state.modo_edicao = False

ARQUIVO = 'historico_zelador.csv'

# --- FUNÇÕES DE PERSISTÊNCIA ---
def salvar_no_historico(dados):
    df_novo = pd.DataFrame([dados])
    # Forçamos o separador ";" para evitar conflitos com textos
    if os.path.exists(ARQUIVO):
        df_novo.to_csv(ARQUIVO, mode='a', index=False, header=False, sep=';')
    else:
        df_novo.to_csv(ARQUIVO, index=False, sep=';')

def carregar_historico():
    if not os.path.exists(ARQUIVO):
        return None
    try:
        # Tenta ler com ponto-e-vírgula primeiro
        df = pd.read_csv(ARQUIVO, sep=';', on_bad_lines='skip')
        # Se as colunas principais não aparecerem, tenta com vírgula (formato antigo)
        if "Data" not in df.columns:
            df = pd.read_csv(ARQUIVO, sep=',', on_bad_lines='skip')
        
        # Garante que a coluna Detalhes exista
        if 'Detalhes' not in df.columns:
            df['Detalhes'] = "Sem detalhes (registro antigo)"
        return df
    except:
        return None

# --- LÓGICA DE ALERTA ---
df_hist_verificacao = carregar_historico()
if df_hist_verificacao is not None and not df_hist_verificacao.empty:
    try:
        # Verifica se a coluna Data existe antes de acessar
        if "Data" in df_hist_verificacao.columns:
            ultima_data_str = df_hist_verificacao['Data'].iloc[-1].split(" ")[0]
            ultima_data = datetime.strptime(ultima_data_str, "%d/%m/%Y")
            if (datetime.now() - ultima_data).days >= 7:
                st.error("⚠️ Atenção: Mais de 7 dias sem vistoria!")
    except: pass

# --- ABAS ---
aba_inspecao, aba_historico = st.tabs(["📋 Nova Inspeção", "📊 Histórico"])

with aba_inspecao:
    st.title("🏢 Sistema de Inspeção")
    inspetor = st.text_input("Nome do Responsável:")
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    if inspetor:
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
                            obs = st.text_input("Problema:", key=f"obs_{bloco}_{area}")
                            acao = st.selectbox("Ação:", ["Limpeza", "Reparo", "Troca"], key=f"ac_{bloco}_{area}")
                            # Tratamento de texto para não quebrar o CSV
                            detalhe = f"[{bloco}-{area}] {obs if obs else 'Pendente'} ({acao})".replace(";", "-")
                            nao_conformidades.append(detalhe)

        if st.button("Finalizar e Salvar"):
            resumo = "OK" if not nao_conformidades else f"{len(nao_conformidades)} Pendências"
            detalhes_str = " // ".join(nao_conformidades) if nao_conformidades else "Tudo em ordem"
            salvar_no_historico({"Data": data_atual, "Inspetor": inspetor, "Status": resumo, "Detalhes": detalhes_str})
            st.success("Salvo!")
            st.rerun()

with aba_historico:
    st.title("📊 Histórico")
    df_hist = carregar_historico()
    
    if df_hist is not None:
        # Verificação de segurança para as colunas antes de exibir
        colunas_vistas = [c for c in ["Data", "Inspetor", "Status"] if c in df_hist.columns]
        st.dataframe(df_hist[colunas_vistas], use_container_width=True)

        # --- VISUALIZAR PENDÊNCIAS ---
        st.markdown("---")
        if "Status" in df_hist.columns and "Detalhes" in df_hist.columns:
            pendentes = df_hist[df_hist['Status'].str.contains("Pendências", na=False)]
            if not pendentes.empty:
                escolha = st.selectbox("Ver detalhes de qual inspeção?", pendentes.index, 
                                        format_func=lambda x: f"{df_hist.loc[x, 'Data']} - {df_hist.loc[x, 'Inspetor']}")
                if st.button("👁️ Mostrar O que foi pontuado"):
                    conteudo = df_hist.loc[escolha, 'Detalhes'].replace(" // ", "\n")
                    st.warning(f"**Detalhes:**\n\n{conteudo}")
        
        # --- GERENCIAMENTO ---
        with st.expander("🛠️ Gerenciar / Resetar"):
            senha = st.text_input("Senha:", type="password")
            if senha == "flats":
                if st.button("🚨 APAGAR TUDO E CORRIGIR ERROS"):
                    if os.path.exists(ARQUIVO): os.remove(ARQUIVO)
                    st.rerun()
    else:
        st.info("Nenhum dado encontrado.")
