import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="App Zelador", page_icon="🏢")

ARQUIVO = 'historico_zelador.csv'

# --- FUNÇÃO PARA LIMPAR FORMULÁRIO ---
def resetar_formulario():
    # Limpa todas as chaves do estado da sessão relacionadas ao checklist
    for key in st.session_state.keys():
        if key.startswith(('r_', 'o_', 'corr_', 'nome_inspetor')):
            del st.session_state[key]
    st.rerun()

# --- FUNÇÕES DE PERSISTÊNCIA ---
def salvar_no_historico(dados):
    try:
        df_novo = pd.DataFrame([dados])
        if os.path.exists(ARQUIVO):
            df_novo.to_csv(ARQUIVO, mode='a', index=False, header=False, sep=';')
        else:
            df_novo.to_csv(ARQUIVO, index=False, sep=';')
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

def carregar_historico():
    if not os.path.exists(ARQUIVO):
        return None
    try:
        df = pd.read_csv(ARQUIVO, sep=';', on_bad_lines='skip')
        if 'Detalhes' not in df.columns:
            df['Detalhes'] = "Sem detalhes"
        return df
    except:
        return None

# --- INTERFACE EM ABAS ---
aba_inspecao, aba_historico = st.tabs(["📋 Nova Inspeção", "📊 Histórico"])

with aba_inspecao:
    st.title("🏢 Sistema de Inspeção")
    
    # Campo de nome com chave para permitir o reset
    inspetor = st.text_input("Nome do Responsável:", key="nome_inspetor")
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    if not inspetor:
        st.info("Digite seu nome para iniciar o checklist.")
    else:
        areas = ["Recepção", "Elevadores", "Escadarias", "Corredores", "Corrimões", "Janelas", "Garagens"]
        blocos = ["Bloco A", "Bloco B"]
        nao_conformidades = []

        # Usamos um container para agrupar o formulário
        with st.form("form_inspecao", clear_on_submit=True):
            for bloco in blocos:
                st.subheader(f"📍 {bloco}")
                for area in areas:
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        status = st.radio(f"{area}", ["Conforme", "Não Conforme"], key=f"r_{bloco}_{area}")
                    
                    if status == "Não Conforme":
                        with c2:
                            correcao = st.selectbox(
                                f"Ação para {area}:",
                                ["Limpeza imediata", "Reparo técnico", "Troca de componentes", "Sinalizar área"],
                                key=f"corr_{bloco}_{area}"
                            )
                            obs = st.text_input(f"Obs sobre {area}:", key=f"o_{bloco}_{area}")
                            
                            detalhe_item = f"[{bloco}-{area}] {obs if obs else 'Pendente'} (Ação: {correcao})"
                            nao_conformidades.append(detalhe_item.replace(";", "-"))
                st.markdown("---")

            botao_salvar = st.form_submit_button("💾 FINALIZAR E SALVAR AGORA")

        if botao_salvar:
            resumo = "OK" if not nao_conformidades else f"{len(nao_conformidades)} Pendências"
            detalhes_csv = " // ".join(nao_conformidades) if nao_conformidades else "Tudo em conformidade"
            
            dados = {
                "Data": data_atual, 
                "Inspetor": inspetor, 
                "Status": resumo, 
                "Detalhes": detalhes_csv
            }
            
            if salvar_no_historico(dados):
                st.success("✅ Inspeção salva com sucesso!")
                
                # Montar relatório para WhatsApp/Email
                relatorio = f"*RELATÓRIO DE INSPEÇÃO*\nData: {data_atual}\nResponsável: {inspetor}\nStatus: {resumo}\n\n"
                if nao_conformidades:
                    relatorio += "*DETALHES:*\n" + "\n".join(nao_conformidades)
                
                texto_url = urllib.parse.quote(relatorio)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.link_button("📲 WhatsApp", f"https://api.whatsapp.com/send?text={texto_url}", use_container_width=True)
                with col2:
                    st.link_button("📧 E-mail", f"mailto:?subject=Inspecao_{data_atual}&body={texto_url}", use_container_width=True)
                
                st.balloons()
                # Botão para limpar tudo e começar outra
                st.button("🔄 Iniciar Nova Inspeção (Limpar Campos)", on_click=resetar_formulario)

with aba_historico:
    st.title("📊 Histórico")
    df_hist = carregar_historico()
    
    if df_hist is not None and not df_hist.empty:
        colunas_vistas = [c for c in ["Data", "Inspetor", "Status"] if c in df_hist.columns]
        st.dataframe(df_hist[colunas_vistas], use_container_width=True)

        # Visualizador de Pendências
        st.markdown("---")
        pendentes = df_hist[df_hist['Status'].str.contains("Pendências", na=False)]
        if not pendentes.empty:
            st.subheader("🔍 Visualizar Detalhes")
            escolha_ver = st.selectbox("Selecione para detalhar:", pendentes.index, 
                                        format_func=lambda x: f"{df_hist.loc[x, 'Data']} - {df_hist.loc[x, 'Inspetor']}")
            if st.button("👁️ Ver Detalhes"):
                st.warning(df_hist.loc[escolha_ver, 'Detalhes'].replace(" // ", "\n"))

        # --- OPÇÕES AVANÇADAS ---
        st.markdown("---")
        with st.expander("🛠️ Opções Avançadas"):
            senha = st.text_input("Senha de Gerenciamento:", type="password", key="senha_gestao")
            if senha == "flats":
                st.subheader("🗑️ Excluir Registro Específico")
                opcoes_del = df_hist.index.tolist()
                item_para_deletar = st.selectbox(
                    "Qual inspeção deseja excluir?", 
                    opcoes_del,
                    format_func=lambda x: f"{df_hist.loc[x, 'Data']} | {df_hist.loc[x, 'Inspetor']}"
                )
                
                if st.button("Confirmar Exclusão"):
                    df_novo = df_hist.drop(item_para_deletar)
                    df_novo.to_csv(ARQUIVO, index=False, sep=';')
                    st.success("Registro excluído!")
                    st.rerun()
            elif senha != "":
                st.error("Senha incorreta")
    else:
        st.info("Nenhuma inspeção registrada.")
