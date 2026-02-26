import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="App Zelador", page_icon="🏢")

# --- FUNÇÕES DE PERSISTÊNCIA ---
def salvar_no_historico(dados, detalhes=None):
    # Salva o resumo
    arquivo_hist = 'historico_zelador.csv'
    pd.DataFrame([dados]).to_csv(arquivo_hist, mode='a', index=False, header=not os.path.exists(arquivo_hist))
    
    # Salva os detalhes (se houver pendências)
    if detalhes:
        arquivo_det = 'detalhes_inspecao.csv'
        df_det = pd.DataFrame(detalhes)
        df_det['ID_Inspecao'] = dados['Data']  # Vincula pelo carimbo de data/hora
        df_det.to_csv(arquivo_det, mode='a', index=False, header=not os.path.exists(arquivo_det))

def carregar_historico():
    if os.path.exists('historico_zelador.csv'):
        return pd.read_csv(arquivo_hist := 'historico_zelador.csv')
    return None

def carregar_detalhes(id_inspecao):
    if os.path.exists('detalhes_inspecao.csv'):
        df = pd.read_csv('detalhes_inspecao.csv')
        return df[df['ID_Inspecao'] == id_inspecao]
    return None

# --- INTERFACE EM ABAS ---
aba_inspecao, aba_historico = st.tabs(["📋 Nova Inspeção", "📊 Histórico de Inspeções"])

with aba_inspecao:
    st.title("🏢 Sistema de Inspeção: Zelador")
    inspetor = st.text_input("Nome do Responsável pela Inspeção:")
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    if not inspetor:
        st.info("Por favor, identifique-se.")
    else:
        areas = ["Recepção", "Elevadores", "Escadarias", "Corredores", "Corrimões", "Janelas"]
        blocos = ["Bloco A", "Bloco B"]
        nao_conformidades = []

        for bloco in blocos:
            with st.expander(f"📋 Inspeção - {bloco}", expanded=True):
                for area in areas:
                    col1, col2 = st.columns([2, 3])
                    status = col1.radio(f"{area}", ["Conforme", "Não Conforme"], key=f"{bloco}_{area}")
                    if status == "Não Conforme":
                        correcao = col2.selectbox(f"Ação:", ["Limpeza imediata", "Reparo técnico", "Troca", "Sinalizar"], key=f"corr_{bloco}_{area}")
                        obs = col2.text_input(f"Obs:", key=f"obs_{bloco}_{area}")
                        nao_conformidades.append({"Bloco": bloco, "Local": area, "Problema": obs if obs else "Não especificado", "Ação": correcao})

        if st.button("Finalizar e Gerar Relatório"):
            resumo_status = "OK" if not nao_conformidades else f"{len(nao_conformidades)} Pendências"
            dados_resumo = {"Data": data_atual, "Inspetor": inspetor, "Status": resumo_status}
            salvar_no_historico(dados_resumo, nao_conformidades)
            st.success("Inspeção Salva!")
            st.rerun()

with aba_historico:
    st.title("📊 Histórico de Inspeções")
    df_hist = carregar_historico()
    
    if df_hist is not None:
        st.write("### 1. Selecione uma linha para ver detalhes")
        # Seleção de linha
        selecao = st.dataframe(
            df_hist, 
            use_container_width=True, 
            hide_index=True, 
            on_select="rerun", 
            selection_mode="single-row"
        )

        # Exibir detalhes se uma linha for selecionada
        if len(selecao.selection.rows) > 0:
            idx = selecao.selection.rows[0]
            linha_selecionada = df_hist.iloc[idx]
            
            st.markdown(f"### 🔍 Detalhes da Inspeção ({linha_selecionada['Data']})")
            
            if "Pendências" in linha_selecionada['Status']:
                detalhes = carregar_detalhes(linha_selecionada['Data'])
                if detalhes is not None and not detalhes.empty:
                    for _, det in detalhes.iterrows():
                        with st.chat_message("assistant"):
                            st.write(f"**{det['Bloco']} - {det['Local']}**")
                            st.write(f"⚠️ Problema: {det['Problema']}")
                            st.write(f"🛠️ Ação: {det['Ação']}")
                else:
                    st.warning("Detalhes não encontrados para este registro antigo.")
            else:
                st.success("✅ Esta inspeção não apresentou pendências.")

        st.markdown("---")
        # --- ÁREA DE GERENCIAMENTO (SENHA) ---
        with st.expander("🛠️ Gerenciar Registros (Apagar)"):
            senha = st.text_input("Senha:", type="password")
            if senha == "flats":
                df_editor = df_hist.copy()
                df_editor.insert(0, "Apagar", False)
                tabela_edicao = st.data_editor(df_editor, hide_index=True, use_container_width=True)
                
                if st.button("🗑️ Confirmar Exclusão"):
                    manter = tabela_edicao[tabela_edicao["Apagar"] == False].drop(columns=["Apagar"])
                    if manter.empty:
                        if os.path.exists('historico_zelador.csv'): os.remove('historico_zelador.csv')
                        if os.path.exists('detalhes_inspecao.csv'): os.remove('detalhes_inspecao.csv')
                    else:
                        manter.to_csv('historico_zelador.csv', index=False)
                    st.rerun()
