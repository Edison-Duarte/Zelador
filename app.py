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
    # Usamos sep=';' para evitar conflito com vírgulas digitadas no texto
    if os.path.exists(ARQUIVO):
        df_novo.to_csv(ARQUIVO, mode='a', index=False, header=False, sep=';')
    else:
        df_novo.to_csv(ARQUIVO, index=False, sep=';')

def carregar_historico():
    if not os.path.exists(ARQUIVO):
        return None
    
    try:
        # Tenta ler com ponto-e-vírgula (padrão novo)
        df = pd.read_csv(ARQUIVO, sep=';', on_bad_lines='skip', encoding='utf-8')
    except:
        try:
            # Se falhar, tenta ler com vírgula (padrão antigo)
            df = pd.read_csv(ARQUIVO, sep=',', on_bad_lines='skip', encoding='utf-8')
        except:
            return "CORROMPIDO"

    # Garante que as colunas essenciais existam para não dar erro de exibição
    colunas = ["Data", "Inspetor", "Status", "Detalhes"]
    for col in colunas:
        if col not in df.columns:
            df[col] = "N/A"
    return df

# --- INTERFACE EM ABAS ---
aba_inspecao, aba_historico = st.tabs(["📋 Nova Inspeção", "📊 Histórico de Inspeções"])

with aba_inspecao:
    st.title("🏢 Sistema de Inspeção")
    inspetor = st.text_input("Nome do Responsável pela Inspeção:")
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    if not inspetor:
        st.info("Por favor, identifique-se para começar.")
    else:
        # Itens atualizados com Garagens
        areas = ["Recepção", "Elevadores", "Escadarias", "Corredores", "Corrimões", "Janelas", "Garagens"]
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
                            correcao = st.selectbox(
                                f"Ação para {area}:",
                                ["Limpeza imediata", "Reparo técnico", "Troca de componentes", "Sinalizar área"],
                                key=f"corr_{bloco}_{area}"
                            )
                            obs = st.text_input(f"Obs ({area}):", key=f"obs_{bloco}_{area}")
                            # Limpeza de caracteres que quebram CSV
                            obs_limpa = (obs if obs else "Pendente").replace(";", "-").replace("\n", " ")
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
    st.title("📊 Histórico de Inspeções")
    df_hist = carregar_historico()
    
    if df_hist is "CORROMPIDO":
        st.error("O arquivo de histórico está corrompido devido à mudança de formato.")
        if st.button("🚨 Resetar Arquivo Corrompido"):
            if os.path.exists(ARQUIVO): os.remove(ARQUIVO)
            st.rerun()
    elif df_hist is not None and not df_hist.empty:
        # Exibição segura da tabela
        st.dataframe(df_hist[["Data", "Inspetor", "Status"]], use_container_width=True)
        
        st.markdown("---")
        st.subheader("🔍 Detalhes das Pendências")
        
        # Filtra apenas quem tem pendências para o seletor
        pendentes = df_hist[df_hist['Status'].str.contains("Pendências", na=False)]
        
        if not pendentes.empty:
            escolha = st.selectbox("Selecione a inspeção para ver os detalhes:", 
                                    pendentes.index, 
                                    format_func=lambda x: f"{df_hist.loc[x, 'Data']} - {df_hist.loc[x, 'Inspetor']}")
            
            if st.button("👁️ Mostrar Pendências"):
                conteudo = df_hist.loc[escolha, 'Detalhes'].replace(" / ", "\n")
                st.warning(f"**Relatório de Problemas:**\n\n{conteudo}")
        else:
            st.info("Nenhuma pendência detalhada para exibir.")

        with st.expander("🛠️ Gerenciar Histórico"):
            senha = st.text_input("Senha:", type="password")
            if senha == "flats":
                if st.button("🚨 APAGAR TODO O HISTÓRICO"):
                    if os.path.exists(ARQUIVO): os.remove(ARQUIVO)
                    st.rerun()
    else:
        st.info("Ainda não existem inspeções registradas.")
