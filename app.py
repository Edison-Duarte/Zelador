import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="App Zelador", page_icon="🏢")

# Inicializa o estado do modo de edição para que ele não "suma" ao digitar
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

# --- FUNÇÕES DE PERSISTÊNCIA ---
ARQUIVO_CSV = 'historico_zelador.csv'

def salvar_no_historico(dados):
    df_novo = pd.DataFrame([dados])
    if os.path.exists(ARQUIVO_CSV):
        df_novo.to_csv(ARQUIVO_CSV, mode='a', index=False, header=False)
    else:
        df_novo.to_csv(ARQUIVO_CSV, index=False)

def carregar_historico():
    if os.path.exists(ARQUIVO_CSV):
        return pd.read_csv(ARQUIVO_CSV)
    return pd.DataFrame(columns=["Data", "Inspetor", "Status"])

# --- INTERFACE EM ABAS ---
aba_inspecao, aba_historico = st.tabs(["📋 Nova Inspeção", "📊 Histórico de Inspeções"])

with aba_inspecao:
    st.title("🏢 Sistema de Inspeção")
    inspetor = st.text_input("Nome do Responsável:")
    if st.button("Salvar Inspeção de Teste"):
        salvar_no_historico({"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Inspetor": inspetor, "Status": "OK"})
        st.success("Salvo! Verifique o Histórico.")

with aba_historico:
    st.title("📊 Histórico de Inspeções")
    df_hist = carregar_historico()
    
    if not df_hist.empty:
        st.dataframe(df_hist, use_container_width=True)
        
        # BOTÃO EDITAR
        if st.button("🛠️ Editar / Apagar Registros"):
            st.session_state.edit_mode = not st.session_state.edit_mode

        # SE O MODO EDIÇÃO ESTIVER ATIVO
        if st.session_state.edit_mode:
            st.markdown("---")
            st.subheader("🔑 Área Restrita")
            senha = st.text_input("Digite a senha para habilitar a exclusão:", type="password")
            
            if senha == "flats":
                st.success("Acesso Liberado!")
                
                # Opção 1: Selecionar um ou mais para apagar
                opcoes = [f"{i} | {r['Data']} - {r['Inspetor']}" for i, r in df_hist.iterrows()]
                selecionados = st.multiselect("Selecione as inspeções para APAGAR:", opcoes)
                
                col_del_sel, col_del_all = st.columns(2)
                
                with col_del_sel:
                    if st.button("🗑️ Apagar Selecionados"):
                        indices = [int(s.split(" | ")[0]) for s in selecionados]
                        df_novo = df_hist.drop(indices)
                        df_novo.to_csv(ARQUIVO_CSV, index=False)
                        st.success("Registros apagados!")
                        st.session_state.edit_mode = False
                        st.rerun()

                with col_del_all:
                    if st.button("🚨 APAGAR TUDO"):
                        if os.path.exists(ARQUIVO_CSV):
                            os.remove(ARQUIVO_CSV)
                        st.warning("Histórico limpo!")
                        st.session_state.edit_mode = False
                        st.rerun()
            elif senha != "":
                st.error("Senha incorreta!")
    else:
        st.info("Nenhuma inspeção encontrada no histórico.")
