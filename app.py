import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="App Zelador", page_icon="🏢")

# --- FUNÇÕES DE PERSISTÊNCIA ---
def salvar_no_historico(dados, detalhes=None):
    arquivo_hist = 'historico_zelador.csv'
    arquivo_detalhes = 'detalhes_zelador.csv'
    
    # Salva resumo
    df_novo = pd.DataFrame([dados])
    if os.path.exists(arquivo_hist):
        df_novo.to_csv(arquivo_hist, mode='a', index=False, header=False)
    else:
        df_novo.to_csv(arquivo_hist, index=False)
    
    # Salva detalhes (se houver não conformidades)
    if detalhes:
        df_detalhes = pd.DataFrame(detalhes)
        df_detalhes['Data_ID'] = dados['Data'] # Chave para ligar as tabelas
        if os.path.exists(arquivo_detalhes):
            df_detalhes.to_csv(arquivo_detalhes, mode='a', index=False, header=False)
        else:
            df_detalhes.to_csv(arquivo_detalhes, index=False)

def carregar_historico():
    if os.path.exists('historico_zelador.csv'):
        return pd.read_csv('historico_zelador.csv')
    return None

def carregar_detalhes(data_id):
    if os.path.exists('detalhes_zelador.csv'):
        df = pd.read_csv('detalhes_zelador.csv')
        return df[df['Data_ID'] == data_id]
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
            resumo_status = "OK" if not nao_conformidades else f"{len(nao_conformidades)} Pendências"
            dados_para_salvar = {
                "Data": data_atual,
                "Inspetor": inspetor,
                "Status": resumo_status
            }
            salvar_no_historico(dados_para_salvar, nao_conformidades)
            
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
                st.link_button("📲 WhatsApp", url_whatsapp)
            with col_e:
                st.link_button("📧 E-mail", f"mailto:?subject=Relatorio_Zelador&body={msg_whatsapp}")

with aba_historico:
    st.title("📊 Histórico de Inspeções")
    df_hist = carregar_historico()
    
    if df_hist is not None:
        st.write("Selecione uma linha para visualizar os detalhes das pendências:")
        
        # Seleção de linha para ver detalhes
        selecao = st.dataframe(
            df_hist, 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )

        # Verificar se algo foi selecionado
        if len(selecao.selection.rows) > 0:
            index_selecionado = selecao.selection.rows[0]
            data_id = df_hist.iloc[index_selecionado]['Data']
            status_sel = df_hist.iloc[index_selecionado]['Status']
            
            st.markdown(f"### 🔍 Detalhes da Inspeção ({data_id})")
            if status_sel == "OK":
                st.success("Nenhuma pendência registrada nesta data.")
            else:
                detalhes_df = carregar_detalhes(data_id)
                if detalhes_df is not None and not detalhes_df.empty:
                    st.table(detalhes_df.drop(columns=['Data_ID']))
                else:
                    st.warning("Detalhes não encontrados para este registro antigo.")

        csv_data = df_hist.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Baixar CSV", data=csv_data, file_name='historico.csv', mime='text/csv')

        st.markdown("---")
        st.subheader("🛠️ Gerenciar Registros")
        senha = st.text_input("Para excluir registros, digite a senha:", type="password")
        
        if senha == "flats":
            st.info("Selecione as inspeções que deseja apagar:")
            df_editor = df_hist.copy()
            df_editor.insert(0, "Selecionar", False)
            
            tabela_edicao = st.data_editor(
                df_editor,
                hide_index=True,
                use_container_width=True,
                column_config={"Selecionar": st.column_config.CheckboxColumn("Apagar?", default=False)},
                disabled=["Data", "Inspetor", "Status"]
            )
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("🗑️ Apagar Selecionados"):
                    df_final = tabela_edicao[tabela_edicao["Selecionar"] == False].drop(columns=["Selecionar"])
                    df_final.to_csv('historico_zelador.csv', index=False)
                    st.success("Registros atualizados!")
                    st.rerun()
            
            with col_b2:
                if st.button("🚨 LIMPAR TODO O HISTÓRICO"):
                    for f in ['historico_zelador.csv', 'detalhes_zelador.csv']:
                        if os.path.exists(f): os.remove(f)
                    st.rerun()
        elif senha != "":
            st.error("Senha incorreta!")
    else:
        st.info("Ainda não existem inspeções registradas.")
