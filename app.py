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
        df = pd.read_csv(arquivo)
        # CORREÇÃO DO ERRO: Se a coluna Detalhes não existir no arquivo antigo, cria ela vazia
        if 'Detalhes' not in df.columns:
            df['Detalhes'] = "Sem detalhes (registro antigo)"
        return df
    return None

# --- INTERFACE EM ABAS ---
aba_inspecao, aba_historico = st.tabs(["📋 Nova Inspeção", "📊 Histórico de Inspeções"])

with aba_inspecao:
    st.title("🏢 Sistema de Inspeção: Zelador")
    inspetor = st.text_input("Nome do Responsável pela Inspeção:")
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    if not inspetor:
        st.info("Por favor, identifique-se para começar.")
    else:
        # Itens atualizados incluindo Garagens
        areas = ["Recepção", "Elevadores", "Escadarias", "Corredores", "Corrimões", "Janelas", "Garagens"]
        blocos = ["Bloco A", "Bloco B"]
        nao_conformidades = []

        st.subheader("2. Checklist de Áreas Comuns")

        for bloco in blocos:
            with st.expander(f"📋 Inspeção - {bloco}", expanded=True):
                for area in areas:
                    col1, col2 = st.columns([2, 3])
                    with col1:
                        status = st.radio(f"{area}", ["Conforme", "Não Conforme"], key=f"{bloco}_{area}")
                    
                    if status == "Não Conforme":
                        with col2:
                            correcao = st.selectbox(
                                f"Ação para {area}:",
                                ["Limpeza imediata", "Reparo técnico", "Troca de componentes", "Sinalizar área"],
                                key=f"corr_{bloco}_{area}"
                            )
                            obs = st.text_input(f"Obs ({area}):", key=f"obs_{bloco}_{area}")
                            nao_conformidades.append(f"[{bloco}-{area}] {obs if obs else 'Não especificado'} (Ação: {correcao})")

        st.markdown("---")
        if st.button("Finalizar e Salvar"):
            resumo_status = "OK" if not nao_conformidades else f"{len(nao_conformidades)} Pendências"
            texto_detalhes = " | ".join(nao_conformidades) if nao_conformidades else "Tudo em conformidade"
            
            dados_para_salvar = {
                "Data": data_atual,
                "Inspetor": inspetor,
                "Status": resumo_status,
                "Detalhes": texto_detalhes
            }
            salvar_no_historico(dados_para_salvar)
            st.success("Inspeção Concluída!")
            st.rerun()

with aba_historico:
    st.title("📊 Histórico de Inspeções")
    df_hist = carregar_historico()
    
    if df_hist is not None:
        # Exibe a tabela sem a coluna de detalhes (para ficar limpo)
        st.dataframe(df_hist[["Data", "Inspetor", "Status"]], use_container_width=True)
        
        st.markdown("---")
        st.subheader("🔍 Visualizar Detalhes das Pendências")
        
        # Filtra apenas quem tem pendências
        pendentes = df_hist[df_hist['Status'].str.contains("Pendências", na=False)]
        
        if not pendentes.empty:
            escolha = st.selectbox(
                "Selecione a inspeção para ver o que foi pontuado:",
                pendentes.index,
                format_func=lambda x: f"{df_hist.loc[x, 'Data']} - {df_hist.loc[x, 'Inspetor']}"
            )
            
            if st.button("👁️ Mostrar Detalhes"):
                conteudo = df_hist.loc[escolha, 'Detalhes'].replace(" | ", "\n")
                st.warning(f"**Pendências encontradas:**\n\n{conteudo}")
        else:
            st.info("Não há pendências detalhadas para exibir.")

        # --- SEÇÃO DE GERENCIAMENTO (APAGAR) ---
        with st.expander("🛠️ Gerenciar Histórico"):
            senha = st.text_input("Senha:", type="password")
            if senha == "flats":
                if st.button("🚨 APAGAR TUDO"):
                    if os.path.exists('historico_zelador.csv'):
                        os.remove('historico_zelador.csv')
                        st.rerun()
