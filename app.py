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
            
            relatorio_texto = f"RELATÓRIO DE INSPEÇÃO - ZELADOR\n"
            relatorio_texto += f"Data: {data_atual}\n"
            relatorio_texto += f"Responsável: {inspetor}\n"
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
        st.write("Abaixo estão as vistorias realizadas anteriormente:")
        st.dataframe(df_hist, use_container_width=True)
        
        # Botão para baixar o CSV
        csv_data = df_hist.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Histórico Completo (CSV)",
            data=csv_data,
            file_name='historico_zelador.csv',
            mime='text/csv',
        )

        st.markdown("---")
        # --- SEÇÃO DE EDIÇÃO/EXCLUSÃO ---
        with st.expander("🛠️ Gerenciar Histórico (Editar/Apagar)"):
            senha = st.text_input("Digite a senha para habilitar edições:", type="password")
            
            if senha == "flats":
                st.warning("Área de Gerenciamento Ativada")
                
                # Opção 1: Apagar uma linha específica
                st.subheader("Apagar Inspeção Específica")
                linha_para_apagar = st.number_input("Digite o índice da linha que deseja apagar:", min_value=0, max_value=len(df_hist)-1, step=1)
                if st.button("🗑️ Apagar Linha Selecionada"):
                    df_novo_hist = df_hist.drop(df_hist.index[linha_para_apagar])
                    df_novo_hist.to_csv('historico_zelador.csv', index=False)
                    st.success(f"Linha {linha_para_apagar} removida com sucesso!")
                    st.rerun()

                st.markdown("---")
                
                # Opção 2: Apagar Tudo
                st.subheader("Apagar Tudo")
                if st.button("🚨 APAGAR TODO O HISTÓRICO"):
                    if os.path.exists('historico_zelador.csv'):
                        os.remove('historico_zelador.csv')
                        st.success("Todo o histórico foi apagado!")
                        st.rerun()
            elif senha != "":
                st.error("Senha incorreta!")

    else:
        st.info("Ainda não existem inspeções registradas no histórico.")
