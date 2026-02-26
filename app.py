import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="App Zelador", page_icon="🏢")

# Inicializa o estado do modo de edição se não existir
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
    st.markdown("---")
    
    inspetor = st.text_input("Nome do Responsável pela Inspeção:")
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    if not inspetor:
        st.info("Por favor, identifique-se para começar.")
    else:
        areas = ["Recepção", "Elevadores", "Escadarias", "Corredores", "Corrimões", "Janelas"]
        blocos = ["Bloco A", "Bloco B"]
        nao_conformidades = []

        for bloco in blocos:
            with st.expander(f"📋 Inspeção - {bloco}", expanded=True):
                for area in areas:
                    col1, col2 = st.columns([2, 3])
                    with col1:
                        status = st.radio(f"{area}", ["Conforme", "Não Conforme"], key=f"{bloco}_{area}")
                    
                    if status == "Não Conforme":
                        with col2:
                            correcao = st.selectbox(f"Ação:", ["Limpeza", "Reparo", "Troca", "Sinalizar"], key=f"c_{bloco}_{area}")
                            obs = st.text_input(f"Obs:", key=f"o_{bloco}_{area}")
                            nao_conformidades.append({"Bloco": bloco, "Local": area, "Problema": obs, "Ação": correcao})

        if st.button("Finalizar e Salvar"):
            resumo = "OK" if not nao_conformidades else f"{len(nao_conformidades)} Pendências"
            salvar_no_historico({"Data": data_atual, "Inspetor": inspetor, "Status": resumo})
            st.success("Inspeção Salva!")
            st.rerun()

with aba_historico:
    st.title("📊 Histórico de Inspeções")
    df_hist = carregar_historico()
    
    if df_hist is not None and not df_hist.empty:
        st.dataframe(df_hist, use_container_width=True)
        
        # Linha de botões de controle
        col_down, col_edit = st.columns([3, 1])
        
        with col_down:
            csv = df_hist.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar CSV", data=csv, file_name='historico.csv', mime='text/csv')

        with col_edit:
            # Botão para ativar/desativar o painel de edição
            if st.button("🛠️ Editar"):
                st.session_state.modo_edicao = not st.session_state.modo_edicao

        # Painel de Edição (Só aparece se clicar no botão Editar)
        if st.session_state.modo_edicao:
            st.markdown("---")
            st.subheader("🛠️ Painel de Gerenciamento")
            senha = st.text_input("Digite a senha para apagar:", type="password")
            
            if senha == "flats":
                st.info("Senha correta. Escolha o que deseja apagar:")
                
                # Opção: Apagar selecionadas
                opcoes = [f"{i} | {r['Data']} - {r['Inspetor']}" for i, r in df_hist.iterrows()]
                selecao = st.multiselect("Selecione os registros para remover:", opcoes)
                
                col_del_sel, col_del_all = st.columns(2)
                
                with col_del_sel:
                    if st.button("🗑️ Apagar Selecionados"):
                        if selecao:
                            indices = [int(item.split(" | ")[0]) for item in selecao]
                            df_final = df_hist.drop(indices)
                            df_final.to_csv('historico_zelador.csv', index=False)
                            st.success("Registros removidos!")
                            st.session_state.modo_edicao = False
                            st.rerun()
                        else:
                            st.warning("Selecione algo primeiro.")

                with col_del_all:
                    if st.button("🚨 APAGAR TUDO"):
                        if os.path.exists('historico_zelador.csv'):
                            os.remove('historico_zelador.csv')
                        st.success("Histórico totalmente apagado!")
                        st.session_state.modo_edicao = False
                        st.rerun()
            elif senha != "":
                st.error("Senha incorreta!")
    else:
        st.info("Ainda não há dados no histórico.")
