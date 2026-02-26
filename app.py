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
    st.title("🏢 Sistema de Inspeção: Zelador")
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
                    col1, col2 = st.columns([2, 3])
                    with col1:
                        status = st.radio(f"{area}", ["Conforme", "Não Conforme"], key=f"{bloco}_{area}")
                    
                    if status == "Não Conforme":
                        with col2:
                            correcao = st.selectbox(
                                f"Ação corretiva para {area}:",
                                ["Limpeza imediata", "Reparo técnico", "Troca de componentes", "Sinalizar área"],
                                key=f"corr_{bloco}_{area}"
                            )
                            obs = st.text_input(f"Obs ({area}):", key=f"obs_{bloco}_{area}")
                            nao_conformidades.append({
                                "Bloco": bloco,
                                "Local": area,
                                "Problema": obs if obs else "Não especificado",
                                "Ação": correcao
                            })

        st.markdown("---")
        if st.button("Finalizar e Gerar Relatório"):
            # Salvando o resumo e as pendências detalhadas separadamente (usando | como separador oculto)
            if nao_conformidades:
                detalhes_texto = " | ".join([f"[{n['Bloco']}] {n['Local']}: {n['Problema']} (Ação: {n['Ação']})" for n in nao_conformidades])
                resumo_status = f"🔴 {len(nao_conformidades)} Pendência(s)"
            else:
                detalhes_texto = "Tudo em conformidade."
                resumo_status = "✅ OK"

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
    
    if df_hist is not None:
        st.write("💡 **Clique em uma linha** para visualizar os detalhes das pendências abaixo.")
        
        # Exibe a tabela sem a coluna "Detalhes" para ficar limpo, mas permite seleção
        colunas_visiveis = ["Data", "Inspetor", "Status"]
        selecao = st.dataframe(
            df_hist[colunas_visiveis], 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )

        # Lógica para mostrar detalhes apenas quando clicar
        if len(selecao.selection.rows) > 0:
            index_selecionado = selecao.selection.rows[0]
            linha = df_hist.iloc[index_selecionado]
            
            st.markdown("---")
            st.subheader(f"🔍 Detalhes da Inspeção - {linha['Data']}")
            
            if "Pendência" in linha["Status"]:
                # Transforma a string de detalhes de volta em lista para exibir bonitinho
                lista_pendencias = linha["Detalhes"].split(" | ")
                for p in lista_pendencias:
                    st.warning(p)
            else:
                st.success("✅ Nenhum problema registrado nesta data.")
            st.markdown("---")

        # Botão de download
        csv_data = df_hist.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Baixar CSV Completo", data=csv_data, file_name='historico.csv', mime='text/csv')

        st.markdown("---")
        st.subheader("🛠️ Gerenciar Registros")
        senha = st.text_input("Para excluir registros, digite a senha:", type="password")
        
        if senha == "flats":
            st.info("Selecione no editor abaixo para apagar:")
            df_editor = df_hist.copy()
            df_editor.insert(0, "Selecionar", False)
            
            tabela_edicao = st.data_editor(
                df_editor,
                hide_index=True,
                use_container_width=True,
                column_config={"Selecionar": st.column_config.CheckboxColumn("Apagar?", default=False)},
                disabled=["Data", "Inspetor", "Status", "Detalhes"]
            )
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("🗑️ Apagar Selecionados"):
                    df_final = tabela_edicao[tabela_edicao["Selecionar"] == False].drop(columns=["Selecionar"])
                    df_final.to_csv('historico_zelador.csv', index=False) if not df_final.empty else os.remove('historico_zelador.csv')
                    st.rerun()
            with col_b2:
                if st.button("🚨 LIMPAR TUDO"):
                    if os.path.exists('historico_zelador.csv'):
                        os.remove('historico_zelador.csv')
                        st.rerun()
        elif senha != "":
            st.error("Senha incorreta!")
    else:
        st.info("Ainda não existem inspeções registradas.")
