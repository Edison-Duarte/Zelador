import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="App Zelador", page_icon="🏢")

# --- FUNÇÕES DE PERSISTÊNCIA (HISTÓRICO) ---
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

def atualizar_arquivo_historico(df):
    arquivo = 'historico_zelador.csv'
    df.to_csv(arquivo, index=False)

# --- LÓGICA DE ALERTA SEMANAL ---
df_hist_verificacao = carregar_historico()
if df_hist_verificacao is not None and not df_hist_verificacao.empty:
    ultima_data_str = df_hist_verificacao['Data'].iloc[-1].split(" ")[0]
    ultima_data = datetime.strptime(ultima_data_str, "%d/%m/%Y")
    dias_passados = (datetime.now() - ultima_data).days
    if dias_passados >= 7:
        st.error(f"⚠️ ATENÇÃO: A última vistoria foi realizada há {dias_passados} dias!")

# --- INTERFACE EM ABAS ---
aba_inspecao, aba_historico = st.tabs(["📋 Nova Inspeção", "📊 Histórico de Inspeções"])

with aba_inspecao:
    # --- CABEÇALHO VISUAL ---
    col_v1, col_v2, col_v3 = st.columns([1, 2, 1])
    with col_v2:
        st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>🚢 ☸️</h1>", unsafe_allow_html=True)
        col_bl1, col_bl2 = st.columns(2)
        with col_bl1:
            st.markdown("<p style='text-align: center; font-size: 40px; margin-bottom: 0;'>🏢</p><p style='text-align: center; font-weight: bold;'>Bloco A</p>", unsafe_allow_html=True)
        with col_bl2:
            st.markdown("<p style='text-align: center; font-size: 40px; margin-bottom: 0;'>🏢</p><p style='text-align: center; font-weight: bold;'>Bloco B</p>", unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align: center;'>Sistema Zelador</h2>", unsafe_allow_html=True)
    st.markdown("---")

    st.subheader("1. Identificação")
    inspetor = st.text_input("Nome do Responsável pela Inspeção:")
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    if not inspetor:
        st.info("Por favor, identifique-se para começar.")
    else:
        areas = ["Recepção", "Elevadores", "Escadarias", "Corredores", "Corrimões", "Janelas"]
        blocos = ["Bloco A", "Bloco B"]
        nao_conformidades = []

        st.subheader("2. Checklist de Áreas Comuns")
        for bloco in blocos:
            with st.expander(f"📋 Inspeção - {bloco}", expanded=True):
                for area in areas:
                    col_status, col_acao = st.columns([2, 3])
                    with col_status:
                        status = st.radio(f"{area}", ["Conforme", "Não Conforme"], key=f"{bloco}_{area}")
                    if status == "Não Conforme":
                        with col_acao:
                            correcao = st.selectbox(f"Ação corretiva:", ["Limpeza imediata", "Reparo técnico", "Troca de componentes"], key=f"corr_{bloco}_{area}")
                            obs = st.text_input(f"Obs:", key=f"obs_{bloco}_{area}")
                            nao_conformidades.append({"Bloco": bloco, "Local": area, "Problema": obs, "Ação": correcao})

        if st.button("Finalizar e Gerar Relatório"):
            resumo_status = "OK" if not nao_conformidades else f"{len(nao_conformidades)} Pendências"
            salvar_no_historico({"Data": data_atual, "Inspetor": inspetor, "Status": resumo_status})
            st.success("Inspeção Salva!")
            
            relatorio_texto = f"RELATÓRIO ZELADOR - {data_atual}\nResponsável: {inspetor}\nStatus: {resumo_status}\n"
            if nao_conformidades:
                for item in nao_conformidades:
                    relatorio_texto += f"- {item['Bloco']} {item['Local']}: {item['Ação']}\n"
            
            st.text_area("Relatório:", relatorio_texto, height=150)
            url_wa = f"https://api.whatsapp.com/send?text={urllib.parse.quote(relatorio_texto)}"
            st.link_button("📲 Enviar WhatsApp", url_wa)

with aba_historico:
    st.title("📊 Histórico de Inspeções")
    df_hist = carregar_historico()
    
    if df_hist is not None:
        st.dataframe(df_hist, use_container_width=True)
        
        # --- SEÇÃO DE EDIÇÃO COM SENHA ---
        with st.expander("🛠️ Editar/Apagar Registros"):
            senha = st.text_input("Digite a senha para gerenciar:", type="password")
            if senha == "flats":
                opcoes_gerenciamento = st.radio("Selecione uma ação:", ["Apenas Visualizar", "Apagar Registro Específico", "Apagar TUDO"])
                
                if opcoes_gerenciamento == "Apagar Registro Específico":
                    linha_para_apagar = st.selectbox("Selecione a inspeção (pela data/nome):", df_hist.index, format_func=lambda x: f"{df_hist.iloc[x]['Data']} - {df_hist.iloc[x]['Inspetor']}")
                    if st.button("❌ Confirmar Exclusão desta Linha"):
                        novo_df = df_hist.drop(linha_para_apagar)
                        atualizar_arquivo_historico(novo_df)
                        st.rerun()
                
                elif opcoes_gerenciamento == "Apagar TUDO":
                    st.warning("Atenção: Isso apagará todos os registros permanentemente!")
                    if st.button("🚨 APAGAR TODO O HISTÓRICO"):
                        if os.path.exists('historico_zelador.csv'):
                            os.remove('historico_zelador.csv')
                            st.success("Histórico deletado com sucesso!")
                            st.rerun()
            elif senha != "":
                st.error("Senha incorreta!")

        # Botão de Download sempre disponível
        csv_data = df_hist.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Histórico (CSV)", data=csv_data, file_name='historico_zelador.csv', mime='text/csv')
    else:
        st.info("Nenhuma inspeção registrada.")
