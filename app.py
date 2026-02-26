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
    # --- CABEÇALHO VISUAL ---
    col_v1, col_v2, col_v3 = st.columns([1, 2, 1])
    with col_v2:
        st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>🚢 ☸️</h1>", unsafe_allow_html=True)
        col_bl1, col_bl2 = st.columns(2)
        with col_bl1:
            st.markdown("<p style='text-align: center; font-size: 40px; margin-bottom: 0;'>🏢</p><p style='text-align: center; font-weight: bold;'>Bloco A</p>", unsafe_allow_html=True)
        with col_bl2:
            st.markdown("<p style='text-align: center; font-size: 40px; margin-bottom: 0;'>🏢</p><p style='text-align: center; font-weight: bold;'>Bloco B</p>", unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align: center;'>Sistema Zelador</h2>", unsafe_allow_html=True)
    st.markdown("---")

    # --- IDENTIFICAÇÃO ---
    st.subheader("1. Identificação")
    inspetor = st.text_input("Nome do Responsável pela Inspeção:")
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    if not inspetor:
        st.info("Por favor, identifique-se para começar.")
    else:
        # --- FORMULÁRIO DE INSPEÇÃO ---
        areas = ["Recepção", "Elevadores", "Escadarias", "Corredores", "Corrimões", "Janelas"]
        blocos = ["Bloco A", "Bloco B"]
        nao_conformidades = []

        st.subheader("2. Checklist de Áreas Comuns")

        for bloco in blocos:
            with st.expander(f"📋 Inspeção - {bloco}", expanded=True):
                for area in areas:
                    col_status, col_acao = st.columns([2, 3])
                    with col_status:
                        status = st.radio(f"{area}", ["Conforme", "Não Conforme"], key=f"{bloco}_{area}")
                    
                    if status == "Não Conforme":
                        with col_acao:
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

        # --- FINALIZAÇÃO ---
        st.markdown("---")
        if st.button("Finalizar e Gerar Relatório"):
            resumo_status = "OK" if not nao_conformidades else f"{len(nao_conformidades)} Pendências"
            dados_para_salvar = {
                "Data": data_atual,
                "Inspetor": inspetor,
                "Status": resumo_status
            }
            salvar_no_historico(dados_para_salvar)
            st.success("Inspeção Concluída e Salva no Histórico!")
            
            relatorio_texto = f"RELATÓRIO DE INSPEÇÃO - ZELADOR\nData: {data_atual}\nResponsável: {inspetor}\n"
            relatorio_texto += "----------------------------\n"
            
            if nao_conformidades:
                relatorio_texto += "🚨 NÃO CONFORMIDADES ENCONTRADAS:\n"
                for item in nao_conformidades:
                    relatorio_texto += f"- {item['Bloco']} | {item['Local']}: {item['Problema']} (Ação: {item['Ação']})\n"
            else:
                relatorio_texto += "✅ Tudo em conformidade!"

            st.text_area("Prévia do Relatório", relatorio_texto, height=200)

            msg_whatsapp = urllib.parse.quote(relatorio_texto)
            url_whatsapp = f"https://api.whatsapp.com/send?text={msg_whatsapp}"
            
            col_w, col_e = st.columns(2)
            with col_w:
                st.link_button("📲 WhatsApp (Escolher Contato)", url_whatsapp)
            with col_e:
                st.link_button("📧 Enviar via E-mail", f"mailto:?subject=Relatorio_Zelador&body={msg_whatsapp}")

with aba_historico:
    st.title("📊 Histórico de Inspeções")
    df_hist = carregar_historico()
    
    if df_hist is not None:
        st.dataframe(df_hist, use_container_width=True)
        
        # --- SEÇÃO DE EDIÇÃO/EXCLUSÃO ---
        with st.expander("🛠️ Gerenciar Histórico (Editar/Apagar)"):
            senha = st.text_input("Digite a senha para habilitar a edição:", type="password")
            
            if senha == "flats":
                st.warning("Cuidado: As alterações abaixo são permanentes!")
                
                opcao_exclusao = st.radio("O que deseja fazer?", ["Manter tudo", "Apagar inspeções selecionadas", "Apagar TUDO"])
                
                if opcao_exclusao == "Apagar inspeções selecionadas":
                    # Criamos uma lista de índices para o multiselect
                    indices_para_remover = st.multiselect(
                        "Selecione as inspeções para remover (pela data/inspetor):",
                        options=df_hist.index,
                        format_func=lambda x: f"{df_hist.iloc[x]['Data']} - {df_hist.iloc[x]['Inspetor']}"
                    )
                    
                    if st.button("Confirmar Exclusão Selecionada"):
                        df_novo = df_hist.drop(indices_para_remover)
                        df_novo.to_csv('historico_zelador.csv', index=False)
                        st.success("Itens removidos com sucesso! Recarregue a página.")
                        st.rerun()

                elif opcao_exclusao == "Apagar TUDO":
                    if st.button("🚨 APAGAR TODO O HISTÓRICO"):
                        if os.path.exists('historico_zelador.csv'):
                            os.remove('historico_zelador.csv')
                            st.success("Histórico limpo com sucesso!")
                            st.rerun()
            elif senha != "":
                st.error("Senha incorreta.")

        csv_data = df_hist.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Histórico Completo (CSV)",
            data=csv_data,
            file_name='historico_zelador.csv',
            mime='text/csv',
        )
    else:
        st.info("Ainda não existem inspeções registradas no histórico.")
