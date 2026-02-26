import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="App Zelador", page_icon="🏢")

# Inicializa o estado de controle
if 'modo_edicao' not in st.session_state:
    st.session_state.modo_edicao = False

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
    return pd.DataFrame(columns=["Data", "Inspetor", "Status"]) # Retorna DF vazio se não existir

# --- INTERFACE EM ABAS ---
aba_inspecao, aba_historico = st.tabs(["📋 Nova Inspeção", "📊 Histórico de Inspeções"])

with aba_inspecao:
    st.title("🏢 Nova Inspeção")
    inspetor = st.text_input("Nome do Responsável:")
    
    if st.button("Simular Salvamento (Teste)"):
        data_teste = datetime.now().strftime("%d/%m/%Y %H:%M")
        salvar_no_historico({"Data": data_teste, "Inspetor": inspetor if inspetor else "Teste", "Status": "OK"})
        st.success("Inspeção de teste salva! Vá para a aba Histórico.")

with aba_historico:
    st.title("📊 Histórico de Inspeções")
    df_hist = carregar_historico()
    
    # Exibe a tabela
    st.dataframe(df_hist, use_container_width=True)
    
    # --- ÁREA DOS BOTÕES ---
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if not df_hist.empty:
            csv = df_hist.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar CSV", data=csv, file_name='historico.csv', mime='text/csv')
        else:
            st.info("Histórico vazio.")

    with col2:
        # O BOTÃO EDITAR AGORA ESTÁ FORA DE QUALQUER CONDICIONAL COMPLEXA
        if st.button("🛠️ Editar / Apagar"):
            st.session_state.modo_edicao = not st.session_state.modo_edicao

    # --- PAINEL DE EDIÇÃO (SÓ ABRE SE MODO_EDICAO FOR TRUE) ---
    if st.session_state.modo_edicao:
        st.info("Modo de edição ativado.")
        senha = st.text_input("Digite a senha para prosseguir:", type="password")
        
        if senha == "flats":
            st.success("Acesso Liberado")
            
            # Opção de apagar registros específicos
            if not df_hist.empty:
                opcoes = [f"{i} | {r['Data']} - {r['Inspetor']}" for i, r in df_hist.iterrows()]
                selecao = st.multiselect("Selecione quais apagar:", opcoes)
                
                if st.button("🗑️ Confirmar Exclusão Selecionada"):
                    indices = [int(item.split(" | ")[0]) for item in selecao]
                    df_novo = df_hist.drop(indices)
                    df_novo.to_csv(ARQUIVO_CSV, index=False)
                    st.success("Excluído com sucesso!")
                    st.session_state.modo_edicao = False
                    st.rerun()
            
            # Opção de apagar tudo
            st.markdown("---")
            if st.button("🚨 APAGAR TODO O HISTÓRICO"):
                if os.path.exists(ARQUIVO_CSV):
                    os.remove(ARQUIVO_CSV)
                st.warning("Todo o histórico foi removido!")
                st.session_state.modo_edicao = False
                st.rerun()
                
        elif senha != "":
            st.error("Senha incorreta!")
