import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="App Zelador", page_icon="🏢")

# --- FUNÇÕES DE PERSISTÊNCIA ---
def salvar_no_historico(dados, lista_pendencias):
    arquivo_hist = 'historico_zelador.csv'
    arquivo_det = 'detalhes_zelador.csv'
    
    # Salva Resumo
    df_novo = pd.DataFrame([dados])
    df_novo.to_csv(arquivo_hist, mode='a', index=False, header=not os.path.exists(arquivo_hist))
    
    # Salva Detalhes (vinculados pela data/hora exata)
    if lista_pendencias:
        df_det = pd.DataFrame(lista_pendencias)
        df_det['id_inspecao'] = dados['Data']
        df_det.to_csv(arquivo_det, mode='a', index=False, header=not os.path.exists(arquivo_det))

def carregar_historico():
    if os.path.exists('historico_zelador.csv'):
        return pd.read_csv('historico_zelador.csv')
    return None

def carregar_detalhes(id_inspecao):
    if os.path.exists('detalhes_zelador.csv'):
        df = pd.read_csv('detalhes_zelador.csv')
        return df[df['id_inspecao'] == id_inspecao]
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
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

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
                            correcao = st.selectbox(f"Ação para {area}:", ["Limpeza imediata", "Reparo técnico", "Troca", "Sinalizar"], key=f"corr_{bloco}_{area}")
                            obs = st.text_input(f"Obs ({area}):", key=f"obs_{bloco}_{area}")
                            nao_conformidades.append({"Bloco": bloco, "Local": area, "Problema": obs if obs else "Não especificado", "Ação": correcao})

        if st.button("Finalizar e Gerar Relatório"):
            resumo_status = "OK" if not nao_conformidades else f"{len(nao_conformidades)} Pendências"
            dados_salvar = {"Data": data_atual, "Inspetor": inspetor, "Status": resumo_status}
            salvar_no_historico(dados_salvar, nao_conformidades)
            st.success("Inspeção Salva!")
            st.rerun()

with aba_historico:
    st.title("📊 Histórico de Inspeções")
    df_hist = carregar_historico()
    
    if df_hist is not None:
        st.info("💡 Clique em uma linha da tabela para ver os detalhes das pendências abaixo.")
        
        # Tabela interativa com seleção de linha
        evento_selecao = st.dataframe(
            df_hist, 
            use_container_width=True, 
            hide_index=True, 
            on_select="rerun", 
            selection_mode="single-row"
        )

        # Exibir detalhes se houver seleção
        selecionado = evento_selecao.get("selection", {}).get("rows", [])
        if selecionado:
            idx = selecionado[0]
            linha = df_hist.iloc[idx]
            st.markdown(f"### 🔍 Detalhes: {linha['Data']}")
            
            if "Pendências" in str(linha['Status']):
                detalhes = carregar_detalhes(linha['Data'])
                if detalhes is not None and not detalhes.empty:
                    for _, row in detalhes.iterrows():
                        st.warning(f"**{row['Bloco']} - {row['Local']}**\n\n* **Problema:** {row['Problema']}\n* **Ação:** {row['Ação']}")
                else:
                    st.write("Detalhes detalhados não encontrados para este registro.")
            else:
                st.success("✅ Nenhuma pendência registrada nesta vistoria.")

        st.markdown("---")
        with st.expander("🛠️ Gerenciar Registros (Senha: flats)"):
            senha = st.text_input("Senha para gerenciar:", type="password")
            if senha == "flats":
                df_editor = df_hist.copy()
                df_editor.insert(0, "Selecionar", False)
                edicao = st.data_editor(df_editor, hide_index=True, use_container_width=True)
                
                col_del1, col_del2 = st.columns(2)
                with col_del1:
                    if st.button("🗑️ Apagar Selecionados"):
                        df_final = edicao[edicao["Selecionar"] == False].drop(columns=["Selecionar"])
                        df_final.to_csv('historico_zelador.csv', index=False)
                        st.rerun()
                with col_del2:
                    if st.button("🚨 APAGAR TUDO"):
                        if os.path.exists('historico_zelador.csv'): os.remove('historico_zelador.csv')
                        if os.path.exists('detalhes_zelador.csv'): os.remove('detalhes_zelador.csv')
                        st.rerun()
    else:
        st.info("Ainda não existem inspeções registradas.")
