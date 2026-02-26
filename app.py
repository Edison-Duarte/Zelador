import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Zelador Pro", page_icon="🏢")

# --- FUNÇÕES DE HISTÓRICO ---
def salvar_no_csv(dados):
    arquivo = 'historico_inspecoes.csv'
    df_novo = pd.DataFrame([dados])
    if os.path.exists(arquivo):
        df_novo.to_csv(arquivo, mode='a', index=False, header=False)
    else:
        df_novo.to_csv(arquivo, index=False)

def carregar_historico():
    arquivo = 'historico_inspecoes.csv'
    if os.path.exists(arquivo):
        return pd.read_csv(arquivo)
    return None

# --- LÓGICA DE ALERTA SEMANAL ---
hist = carregar_historico()
if hist is not None and not hist.empty:
    ultima_data_str = hist['Data'].iloc[-1].split(" ")[0]
    ultima_data = datetime.strptime(ultima_data_str, "%d/%m/%Y")
    dias_passados = (datetime.now() - ultima_data).days
    if dias_passados >= 7:
        st.error(f"⚠️ ATENÇÃO: A última vistoria foi há {dias_passados} dias!")

# --- INTERFACE EM ABAS ---
aba_nova, aba_hist = st.tabs(["📋 Nova Inspeção", "📊 Consultar Histórico"])

with aba_nova:
    st.title("Inspeção de Áreas Comuns")
    
    # 1. Identificação
    inspetor = st.text_input("Nome do Inspetor:")
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    if inspetor:
        # 2. Checklist
        areas = ["Recepção", "Elevadores", "Escadarias", "Corredores", "Corrimões", "Janelas"]
        blocos = ["Bloco A", "Bloco B"]
        nao_conformidades = []

        for bloco in blocos:
            with st.expander(f"Vistoria {bloco}"):
                for area in areas:
                    res = st.radio(f"{area} ({bloco})", ["Conforme", "Não Conforme"], key=f"{bloco}_{area}")
                    if res == "Não Conforme":
                        acao = st.selectbox(f"Ação para {area}:", ["Limpeza", "Reparo", "Troca"], key=f"ac_{bloco}_{area}")
                        nao_conformidades.append(f"{bloco}-{area} ({acao})")

        # 3. Finalização
        if st.button("Finalizar e Enviar"):
            status_geral = "OK" if not nao_conformidades else f"{len(nao_conformidades)} Pendências"
            
            # Salvar no histórico
            dados = {"Data": data_atual, "Inspetor": inspetor, "Resultado": status_geral}
            salvar_no_csv(dados)

            # Gerar texto para WhatsApp
            relatorio = f"*RELATÓRIO ZELADOR*\nData: {data_atual}\nInspetor: {inspetor}\nStatus: {status_geral}\n"
            if nao_conformidades:
                relatorio += "\n*Problemas:* " + ", ".join(nao_conformidades)
            
            url_wa = f"https://api.whatsapp.com/send?text={urllib.parse.quote(relatorio)}"
            
            st.success("Inspeção salva com sucesso!")
            st.link_button("📲 Enviar via WhatsApp", url_wa)
    else:
        st.info("Digite seu nome para iniciar.")

with aba_hist:
    st.header("Histórico de Vistorias")
    dados_h = carregar_historico()
    if dados_h is not None:
        st.dataframe(dados_h, use_container_width=True)
    else:
        st.write("Nenhum registro encontrado.")

