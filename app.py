import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="App Zelador", page_icon="🏢")

# Inicializa o estado para o painel de edição
if 'modo_edicao' not in st.session_state:
    st.session_state.modo_edicao = False

ARQUIVO = 'historico_zelador.csv'

# --- FUNÇÕES DE PERSISTÊNCIA (HISTÓRICO) ---
def salvar_no_historico(dados):
    df_novo = pd.DataFrame([dados])
    # Usamos o separador ";" para que vírgulas no texto não quebrem as colunas do CSV
    if os.path.exists(ARQUIVO):
        df_novo.to_csv(ARQUIVO, mode='a', index=False, header=False, sep=';')
    else:
        df_novo.to_csv(ARQUIVO, index=False, sep=';')

def carregar_historico():
    if os.path.exists(ARQUIVO):
        try:
            # on_bad_lines='skip' ignora linhas corrompidas e sep=';' garante leitura correta
            df = pd.read_csv(ARQUIVO, sep=';', on_bad_lines='skip')
            
            # CORREÇÃO DE ERROS: Se o arquivo for antigo e não tiver a coluna Detalhes, cria ela vazia
            if 'Detalhes' not in df.columns:
                df['Detalhes'] = "Registro antigo: detalhes não disponíveis"
            return df
        except:
            return None
    return None

# --- LÓGICA DE ALERTA SEMANAL ---
df_hist_verificacao = carregar_historico()
if df_hist_verificacao is not None and not df_hist_verificacao.empty:
    try:
        ultima_data_str = df_hist_verificacao['Data'].iloc[-1].split(" ")[0]
        ultima_data = datetime.strptime(ultima_data_str, "%d/%m/%Y")
        dias_passados = (datetime.now() - ultima_data).days
        if dias_passados >= 7:
            st.error(f"⚠️ ATENÇÃO: A última vistoria foi realizada há {dias_passados} dias!")
    except:
        pass

# --- INTERFACE EM ABAS ---
aba_inspecao, aba_historico = st.tabs(["📋 Nova Inspeção", "📊 Histórico de Inspeções"])

with aba_inspecao:
    st.title("🏢 Sistema de Inspeção: Zelador")
    st.markdown("---")

    st.subheader("1. Identificação")
    inspetor = st.text_input("Nome do Responsável pela Inspeção:")
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    if not inspetor:
        st.info("Por favor, identifique-se para começar.")
    else:
        areas = ["Recepção", "Elevadores", "Escadarias", "Corredores", "Corrimões", "Janelas", "Garagens"]
        blocos = ["Bloco A", "Bloco B"]
        nao_conformidades_lista = []

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
                            # Limpamos o texto para não conter o separador do CSV
                            obs_limpa = (obs if obs else "Não especificado").replace(";", "-")
                            nao_conformidades_lista.append(f"{bloco}|{area}: {obs_limpa} ({correcao})")

        st.markdown("---")
        if st.button("Finalizar e Gerar Relatório"):
            resumo_status = "OK" if not nao_conformidades_lista else f"{len(nao_conformidades_lista)} Pendências"
            # Unimos os detalhes em uma única string para salvar no CSV
            detalhes_texto = " // ".join(nao_conformidades_lista) if nao_conformidades_lista else "Tudo em conformidade"
            
            dados_para_salvar = {
                "Data": data_atual,
                "Inspetor": inspetor,
                "Status": resumo_status,
                "Detalhes": detalhes_texto
            }
            salvar_no_historico(dados_para_salvar)
            st.success("Inspeção Concluída!")
            st.rerun()

with aba_historico:
    st.title("📊 Histórico de Inspeções")
    df_hist = carregar_historico()
    
    if df_hist is not None and not df_hist.empty:
        # Exibimos apenas as colunas resumo para manter a tabela limpa
        st.write("Vistorias realizadas:")
        st.dataframe(df_hist[["Data", "Inspetor", "Status"]], use_container_width=True)
        
        # --- BOTÃO PARA VISUALIZAR PENDÊNCIAS ---
        st.markdown("---")
        st.subheader("🔍 Visualizar Detalhes das Pendências")
        
        # Filtramos apenas as inspeções que possuem pendências
        pendentes_df = df_hist[df_hist['Status'].str.contains("Pendências", na=False)]
        
        if not pendentes_df.empty:
            escolha = st.selectbox(
                "Selecione uma inspeção com pendências para detalhar:",
                pendentes_df.index,
                format_func=lambda x: f"{df_hist.loc[x, 'Data']} - {df_hist.loc[x, 'Inspetor']}"
            )
            
            if st.button("👁️ Visualizar O que foi pontuado"):
                detalhes_view = df_hist.loc[escolha, 'Detalhes'].replace(" // ", "\n")
                st.warning(f"**Relatório de Não Conformidades:**\n\n{detalhes_view}")
        else:
            st.info("Não há pendências registradas para visualizar.")

        # --- AÇÕES E GERENCIAMENTO ---
        st.markdown("---")
        col_down, col_edit = st.columns([3, 1])
        with col_down:
            csv_data = df_hist.to_csv(index=False, sep=';').encode('utf-8')
            st.download_button("📥 Baixar CSV", csv_data, "historico_zelador.csv", "text/csv")
        
        with col_edit:
            if st.button("🛠️ Editar"):
                st.session_state.modo_edicao = not st.session_state.modo_edicao

        if st.session_state.modo_edicao:
            senha = st.text_input("Senha para exclusão:", type="password")
            if senha == "flats":
                st.subheader("⚙️ Excluir Registros")
                opcoes = [f"{idx} | {row['Data']} - {row['Inspetor']}" for idx, row in df_hist.iterrows()]
                selecionados = st.multiselect("Selecione para apagar:", opcoes)
                
                if st.button("🗑️ Apagar Selecionados"):
                    indices = [int(s.split(" | ")[0]) for s in selecionados]
                    df_novo = df_hist.drop(indices)
                    df_novo.to_csv(ARQUIVO, index=False, sep=';')
                    st.success("Removido!")
                    st.rerun()

                if st.button("🚨 APAGAR TUDO"):
                    if os.path.exists(ARQUIVO): os.remove(ARQUIVO)
                    st.rerun()
            elif senha != "":
                st.error("Senha incorreta!")
    else:
        st.info("Ainda não existem inspeções registradas.")
