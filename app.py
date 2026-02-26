import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="App Zelador", page_icon="🏢")

# --- FUNÇÕES DE PERSISTÊNCIA ---
def salvar_no_historico(dados):
    arquivo = 'historico_zelador.csv'
    df_novo = pd.DataFrame([dados])
    if os.path.exists(arquivo):
        # Lê o existente para garantir que as colunas batam
        df_antigo = pd.read_csv(arquivo)
        df_final = pd.concat([df_antigo, df_novo], ignore_index=True)
        df_final.to_csv(arquivo, index=False)
    else:
        df_novo.to_csv(arquivo, index=False)

def carregar_historico():
    arquivo = 'historico_zelador.csv'
    if os.path.exists(arquivo):
        df = pd.read_csv(arquivo)
        # Garante que a coluna Detalhes exista para não dar erro em arquivos antigos
        if "Detalhes" not in df.columns:
            df["Detalhes"] = "Sem detalhes registrados"
        return df
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
                                "Bloco": bloco, "Local": area, "Problema": obs if obs else "Não especificado", "Ação": correcao
                            })

        st.markdown("---")
        if st.button("Finalizar e Gerar Relatório"):
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
        st.write("💡 **Selecione uma linha** para ver os detalhes:")
        
        # Mostra apenas colunas principais
        colunas_v = ["Data", "Inspetor", "Status"]
        
        # O pulo do gato: seleção de linha
        selecao = st.dataframe(
            df_hist[colunas_v], 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )

        # Se houver linha selecionada, mostra os detalhes
        if len(selecao.selection.rows) > 0:
            idx = selecao.selection.rows[0]
            linha = df_hist.iloc[idx]
            
            st.info(f"🔍 **Detalhes da Inspeção ({linha['Data']})**")
            detalhes = linha['Detalhes'].split(" | ")
            for item in detalhes:
                st.write(f"• {item}")
        
        st.markdown("---")
        # Botão de download
        csv_data = df_hist.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Baixar CSV", data=csv_data, file_name='historico.csv', mime='text/csv')

        # --- GERENCIAMENTO (SENHA) ---
        st.subheader("🛠️ Gerenciar Registros")
        senha = st.text_input("Senha para excluir:", type="password")
        if senha == "flats":
            if st.button("🚨 LIMPAR TODO O HISTÓRICO"):
                if os.path.exists('historico_zelador.csv'):
                    os.remove('historico_zelador.csv')
                    st.rerun()
    else:
        st.info("Ainda não existem inspeções registradas.")
