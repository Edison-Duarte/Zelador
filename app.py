import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="App Zelador", page_icon="🏢")

ARQUIVO = 'historico_zelador.csv'

# --- FUNÇÃO DE CALLBACK PARA LIMPAR ---
def resetar_formulario():
    # Deleta as chaves do session_state. 
    # O Streamlit recarregará a página sozinho após este callback terminar.
    for key in list(st.session_state.keys()):
        if key.startswith(('r_', 'o_', 'corr_', 'nome_inspetor')):
            st.session_state.pop(key, None)
    # st.rerun() REMOVIDO: Desnecessário aqui.

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

# --- ABAS ---
aba_inspecao, aba_historico = st.tabs(["📋 Nova Inspeção", "📊 Histórico"])

with aba_inspecao:
    st.title("🏢 Sistema de Inspeção")
    
    # Campo de nome
    inspetor = st.text_input("Nome do Responsável:", key="nome_inspetor")
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    if not inspetor:
        st.info("Digite seu nome para iniciar o checklist.")
    else:
        areas = ["Recepção", "Elevadores", "Escadarias", "Corredores", "Corrimões", "Janelas", "Garagens"]
        blocos = ["Bloco A", "Bloco B"]
        nao_conformidades = []

        for bloco in blocos:
            st.markdown(f"### 📍 {bloco}")
            for area in areas:
                c1, c2 = st.columns([2, 3])
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

        # Botão de salvar
        if st.button("💾 FINALIZAR E SALVAR AGORA"):
            resumo = "OK" if not nao_conformidades else f"{len(nao_conformidades)} Pendências"
            detalhes_csv = " // ".join(nao_conformidades) if nao_conformidades else "Tudo em conformidade"
            
            sucesso = salvar_no_historico({
                "Data": data_atual, "Inspetor": inspetor, "Status": resumo, "Detalhes": detalhes_csv
            })
            
            if sucesso:
                st.success("✅ Inspeção salva!")
                
                # Links de compartilhamento
                relatorio = f"*RELATÓRIO DE INSPEÇÃO*\nData: {data_atual}\nResponsável: {inspetor}\nStatus: {resumo}\n\n"
                if nao_conformidades:
                    relatorio += "*DETALHES:*\n" + "\n".join(nao_conformidades)
                
                texto_url = urllib.parse.quote(relatorio)
                
                col_w, col_e = st.columns(2)
                with col_w:
                    st.link_button("📲 WhatsApp", f"https://api.whatsapp.com/send?text={texto_url}", use_container_width=True)
                with col_e:
                    st.link_button("📧 E-mail", f"mailto:?subject=Inspecao_{data_atual}&body={texto_url}", use_container_width=True)
                
                st.balloons()
                
                # Botão de reset usando o Callback corretamente
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
            st.subheader("🔍 Visualizar Pendências")
            escolha_ver = st.selectbox("Selecione para detalhar:", pendentes.index, 
                                        format_func=lambda x: f"{df_hist.loc[x, 'Data']} - {df_hist.loc[x, 'Inspetor']}")
            if st.button("👁️ Ver Detalhes"):
                st.warning(df_hist.loc[escolha_ver, 'Detalhes'].replace(" // ", "\n"))

        # Opções Avançadas (Excluir registro selecionado)
        with st.expander("🛠️ Opções Avançadas"):
            senha = st.text_input("Senha:", type="password", key="senha_adm")
            if senha == "flats":
                opcoes_del = df_hist.index.tolist()
                item_del = st.selectbox("Excluir qual registro?", opcoes_del,
                                        format_func=lambda x: f"{df_hist.loc[x, 'Data']} | {df_hist.loc[x, 'Inspetor']}")
                if st.button("Confirmar Exclusão"):
                    df_novo = df_hist.drop(item_del)
                    df_novo.to_csv(ARQUIVO, index=False, sep=';')
                    st.rerun() # Aqui o rerun é válido pois não é um callback!
