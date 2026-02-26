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
        # Botão para baixar o CSV (mantido no topo para facilidade)
        csv_data = df_hist.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Baixar CSV", data=csv_data, file_name='historico.csv', mime='text/csv')

        st.markdown("---")
        
        # --- ÁREA DE EDIÇÃO DINÂMICA ---
        with st.expander("🛠️ Modo de Edição e Exclusão (Senha Necessária)"):
            senha = st.text_input("Digite a senha para gerenciar:", type="password")
            
            if senha == "flats":
                st.info("Selecione as linhas que deseja remover ou use o checkbox no topo da coluna para marcar todas.")
                
                # Adiciona uma coluna de seleção temporária
                df_com_selecao = df_hist.copy()
                df_com_selecao.insert(0, "Selecionar para Apagar", False)
                
                # Interface de edição dinâmica
                edicao = st.data_editor(
                    df_com_selecao,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Selecionar para Apagar": st.column_config.CheckboxColumn(
                            "❌",
                            help="Marque para apagar",
                            default=False,
                        )
                    },
                    disabled=["Data", "Inspetor", "Status"] # Impede editar o conteúdo, apenas o checkbox
                )
                
                # Lógica de Exclusão
                col_del1, col_del2 = st.columns(2)
                
                with col_del1:
                    if st.button("🗑️ Apagar Selecionados"):
                        # Filtra apenas o que NÃO foi selecionado
                        linhas_restantes = edicao[edicao["Selecionar para Apagar"] == False]
                        # Remove a coluna temporária de seleção antes de salvar
                        df_final = linhas_restantes.drop(columns=["Selecionar para Apagar"])
                        
                        if len(df_final) == 0:
                            if os.path.exists('historico_zelador.csv'):
                                os.remove('historico_zelador.csv')
                        else:
                            df_final.to_csv('historico_zelador.csv', index=False)
                        
                        st.success("Alterações salvas!")
                        st.rerun()
                
                with col_del2:
                    if st.button("🚨 APAGAR TUDO"):
                        if os.path.exists('historico_zelador.csv'):
                            os.remove('historico_zelador.csv')
                            st.rerun()

            elif senha != "":
                st.error("Senha incorreta!")
            else:
                # Exibição padrão quando não há senha (apenas leitura)
                st.dataframe(df_hist, use_container_width=True, hide_index=True)

    else:
        st.info("Ainda não existem inspeções registradas no histórico.")
