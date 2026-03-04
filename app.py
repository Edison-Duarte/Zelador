import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="App Zelador", page_icon="🏢")

ARQUIVO = 'historico_zelador.csv'

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
        st.error(f"Erro ao salvar no arquivo: {e}")
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

# --- INTERFACE ---
aba_inspecao, aba_historico = st.tabs(["📋 Nova Inspeção", "📊 Histórico"])

with aba_inspecao:
    st.title("🏢 Sistema de Inspeção")
    inspetor = st.text_input("Nome do Responsável:", key="input_nome")
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    if not inspetor:
        st.info("Digite seu nome para liberar o formulário.")
    else:
        areas = ["Recepção", "Elevadores", "Escadarias", "Corredores", "Corrimões", "Janelas", "Garagens"]
        blocos = ["Bloco A", "Bloco B"]
        nao_conformidades = []

        for bloco in blocos:
            with st.expander(f"📋 {bloco}", expanded=True):
                for area in areas:
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        status = st.radio(f"{area}", ["Conforme", "Não Conforme"], key=f"r_{bloco}_{area}")
                    if status == "Não Conforme":
                        with c2:
                            obs = st.text_input(f"Problema em {area}?", key=f"o_{bloco}_{area}")
                            nao_conformidades.append(f"• {bloco} - {area}: {obs if obs else 'Não detalhado'}")

        st.markdown("---")
        
        if st.button("💾 FINALIZAR E SALVAR AGORA"):
            resumo = "OK" if not nao_conformidades else f"{len(nao_conformidades)} Pendências"
            detalhes_csv = " // ".join(nao_conformidades) if nao_conformidades else "Tudo em conformidade"
            
            sucesso = salvar_no_historico({
                "Data": data_atual, 
                "Inspetor": inspetor, 
                "Status": resumo, 
                "Detalhes": detalhes_csv
            })
            
            if sucesso:
                st.success(f"✅ Inspeção de {inspetor} salva com sucesso!")
                
                # --- MONTAGEM DO TEXTO PARA ENVIO ---
                texto_relatorio = f"*RELATÓRIO DE INSPEÇÃO*\n\n"
                texto_relatorio += f"*Data:* {data_atual}\n"
                texto_relatorio += f"*Responsável:* {inspetor}\n"
                texto_relatorio += f"*Status:* {resumo}\n\n"
                
                if nao_conformidades:
                    texto_relatorio += "*PENDÊNCIAS ENCONTRADAS:*\n"
                    for item in nao_conformidades:
                        texto_relatorio += f"{item}\n"
                else:
                    texto_relatorio += "✅ Todas as áreas estão em conformidade."

                # --- BOTÕES DE COMPARTILHAMENTO ---
                st.markdown("### 📲 Enviar Relatório")
                
                # Encode para URL
                texto_url = urllib.parse.quote(texto_relatorio)
                url_whatsapp = f"https://api.whatsapp.com/send?text={texto_url}"
                url_email = f"mailto:?subject=Relatorio de Inspecao {data_atual}&body={texto_url}"

                col_w, col_e = st.columns(2)
                with col_w:
                    st.link_button("📲 Enviar via WhatsApp", url_whatsapp, use_container_width=True)
                with col_e:
                    st.link_button("📧 Enviar via E-mail", url_email, use_container_width=True)
                
                st.balloons()

with aba_historico:
    st.title("📊 Histórico")
    df_hist = carregar_historico()
    
    if df_hist is not None and not df_hist.empty:
        colunas_exibir = [c for c in ["Data", "Inspetor", "Status"] if c in df_hist.columns]
        st.dataframe(df_hist[colunas_exibir], use_container_width=True)

        st.markdown("---")
        if "Status" in df_hist.columns and "Detalhes" in df_hist.columns:
            pendentes = df_hist[df_hist['Status'].str.contains("Pendências", na=False)]
            if not pendentes.empty:
                st.subheader("🔍 Detalhes das Pendências")
                escolha = st.selectbox("Selecione a inspeção:", pendentes.index, 
                                        format_func=lambda x: f"{df_hist.loc[x, 'Data']} - {df_hist.loc[x, 'Inspetor']}")
                
                if st.button("👁️ Abrir Detalhes"):
                    conteudo = df_hist.loc[escolha, 'Detalhes'].replace(" // ", "\n")
                    st.warning(f"**Relatório:**\n\n{conteudo}")
            else:
                st.info("Nenhuma pendência para detalhar.")
        
        # Opção de resetar caso o arquivo corrompa
        with st.expander("🛠️ Opções Avançadas"):
            if st.button("🚨 Resetar Histórico"):
                if os.path.exists(ARQUIVO):
                    os.remove(ARQUIVO)
                    st.rerun()
    else:
        st.info("Nenhuma inspeção registrada ainda.")
