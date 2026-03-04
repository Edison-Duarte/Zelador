import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="App Zelador", page_icon="🏢")

ARQUIVO = 'historico_zelador.csv'

# --- FUNÇÃO DE CALLBACK PARA LIMPAR (SEM RERUN INTERNO) ---
def resetar_formulario():
    # Remove as chaves do estado da sessão para limpar os campos
    for key in list(st.session_state.keys()):
        if key.startswith(('r_', 'o_', 'corr_', 'nome_inspetor')):
            st.session_state.pop(key, None)

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
    
    inspetor = st.text_input("👤 Nome do Responsável:", key="nome_inspetor")
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    if not inspetor:
        st.info("Por favor, digite seu nome para exibir o checklist.")
    else:
        # Itens com destaque (Negrito e Emojis)
        itens_checklist = {
            "🛋️ **Recepção**": "Recepção",
            "🛗 **Elevadores**": "Elevadores",
            "🪜 **Escadarias**": "Escadarias",
            "🛤️ **Corredores**": "Corredores",
            "🧼 **Corrimões**": "Corrimões",
            "🪟 **Janelas**": "Janelas",
            "🚗 **Garagens**": "Garagens"
        }
        
        blocos = ["Bloco A", "Bloco B"]
        nao_conformidades = []

        for bloco in blocos:
            st.markdown(f"### 📍 {bloco}")
            for label, area_id in itens_checklist.items():
                c1, c2 = st.columns([2, 3])
                with c1:
                    # Exibe o nome em destaque
                    status = st.radio(label, ["Conforme", "Não Conforme"], key=f"r_{bloco}_{area_id}")
                
                if status == "Não Conforme":
                    with c2:
                        correcao = st.selectbox(
                            f"Ação Corretiva ({area_id}):",
                            ["Limpeza imediata", "Reparo técnico", "Troca de componentes", "Sinalizar área"],
                            key=f"corr_{bloco}_{area_id}"
                        )
                        obs = st.text_input(f"Observação:", placeholder="Ex: Lâmpada queimada", key=f"o_{bloco}_{area_id}")
                        
                        detalhe_item = f"[{bloco}-{area_id}] {obs if obs else 'Pendente'} (Ação: {correcao})"
                        nao_conformidades.append(detalhe_item.replace(";", "-"))
            st.markdown("---")

        # Botão de finalizar
        if st.button("💾 FINALIZAR E SALVAR AGORA"):
            resumo = "OK" if not nao_conformidades else f"{len(nao_conformidades)} Pendências"
            detalhes_csv = " // ".join(nao_conformidades) if nao_conformidades else "Tudo em conformidade"
            
            sucesso = salvar_no_historico({
                "Data": data_atual, "Inspetor": inspetor, "Status": resumo, "Detalhes": detalhes_csv
            })
            
            if sucesso:
                st.success("✅ Inspeção salva com sucesso!")
                
                # Relatório formatado para envio
                relatorio = f"*RELATÓRIO DE INSPEÇÃO*\n📅 Data: {data_atual}\n👤 Responsável: {inspetor}\n📊 Status: {resumo}\n\n"
                if nao_conformidades:
                    relatorio += "*PENDÊNCIAS:*\n" + "\n".join(nao_conformidades)
                
                texto_url = urllib.parse.quote(relatorio)
                
                c_w, c_e = st.columns(2)
                with c_w:
                    st.link_button("📲 Enviar via WhatsApp", f"https://api.whatsapp.com/send?text={texto_url}", use_container_width=True)
                with c_e:
                    st.link_button("📧 Enviar via E-mail", f"mailto:?subject=Relatorio_Zelador&body={texto_url}", use_container_width=True)
                
                st.balloons()
                
                # Botão de Reset (usa o callback automático do Streamlit)
                st.button("🔄 Iniciar Nova Inspeção (Limpar Campos)", on_click=resetar_formulario)

with aba_historico:
    st.title("📊 Histórico")
    df_hist = carregar_historico()
    
    if df_hist is not None and not df_hist.empty:
        colunas_vistas = [c for c in ["Data", "Inspetor", "Status"] if c in df_hist.columns]
        st.dataframe(df_hist[colunas_vistas], use_container_width=True)

        st.markdown("---")
        pendentes = df_hist[df_hist['Status'].str.contains("Pendências", na=False)]
        if not pendentes.empty:
            st.subheader("🔍 Visualizar Detalhes")
            escolha_ver = st.selectbox("Selecione para detalhar:", pendentes.index, 
                                        format_func=lambda x: f"{df_hist.loc[x, 'Data']} - {df_hist.loc[x, 'Inspetor']}")
            if st.button("👁️ Ver O que foi pontuado"):
                st.warning(df_hist.loc[escolha_ver, 'Detalhes'].replace(" // ", "\n"))

        with st.expander("🛠️ Opções Avançadas"):
            senha = st.text_input("Senha Adm:", type="password", key="senha_adm")
            if senha == "flats":
                opcoes_del = df_hist.index.tolist()
                item_del = st.selectbox("Qual registro excluir?", opcoes_del,
                                        format_func=lambda x: f"{df_hist.loc[x, 'Data']} | {df_hist.loc[x, 'Inspetor']}")
                if st.button("Excluir Definitivamente"):
                    df_novo = df_hist.drop(item_del)
                    df_novo.to_csv(ARQUIVO, index=False, sep=';')
                    st.rerun()
