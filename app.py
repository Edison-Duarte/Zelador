import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="App Zelador", page_icon="🏢")

ARQUIVO = 'historico_zelador.csv'

# --- FUNÇÕES DE PERSISTÊNCIA ---
def salvar_no_historico(dados):
    try:
        df_novo = pd.DataFrame([dados])
        if os.path.exists(ARQUIVO):
            # Salva sem o cabeçalho se o arquivo já existir
            df_novo.to_csv(ARQUIVO, mode='a', index=False, header=False, sep=';')
        else:
            # Cria o arquivo com cabeçalho
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

        # Criamos o checklist
        for bloco in blocos:
            with st.expander(f"📋 {bloco}", expanded=True):
                for area in areas:
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        status = st.radio(f"{area}", ["Conforme", "Não Conforme"], key=f"r_{bloco}_{area}")
                    if status == "Não Conforme":
                        with c2:
                            obs = st.text_input(f"Qual o problema em {area}?", key=f"o_{bloco}_{area}")
                            nao_conformidades.append(f"[{bloco}-{area}] {obs if obs else 'Não detalhado'}")

        st.markdown("---")
        
        # O BOTÃO DE SALVAMENTO
        if st.button("💾 FINALIZAR E SALVAR AGORA"):
            if not inspetor:
                st.warning("O nome do inspetor é obrigatório!")
            else:
                resumo = "OK" if not nao_conformidades else f"{len(nao_conformidades)} Pendências"
                detalhes_str = " // ".join(nao_conformidades) if nao_conformidades else "Tudo em conformidade"
                
                sucesso = salvar_no_historico({
                    "Data": data_atual, 
                    "Inspetor": inspetor, 
                    "Status": resumo, 
                    "Detalhes": detalhes_str
                })
                
                if sucesso:
                    st.toast("Dados gravados com sucesso!", icon="✅")
                    st.success("✅ Inspeção salva no histórico! Você já pode consultar na outra aba.")
                    # Pequeno delay para o usuário ver a mensagem antes de limpar
                    st.balloons()
                else:
                    st.error("Falha crítica ao tentar gravar os dados. Verifique se o arquivo CSV não está aberto em outro programa.")

with aba_historico:
    st.title("📊 Histórico")
    df_hist = carregar_historico()
    
    if df_hist is not None and not df_hist.empty:
        # Mostra a tabela (apenas colunas principais)
        colunas_exibir = [c for c in ["Data", "Inspetor", "Status"] if c in df_hist.columns]
        st.dataframe(df_hist[colunas_exibir], use_container_width=True)

        st.markdown("---")
        # Visualizador de detalhes
        if "Status" in df_hist.columns and "Detalhes" in df_hist.columns:
            pendentes = df_hist[df_hist['Status'].str.contains("Pendências", na=False)]
            if not pendentes.empty:
                st.subheader("🔍 O que foi pontuado?")
                escolha = st.selectbox("Selecione a inspeção:", pendentes.index, 
                                        format_func=lambda x: f"{df_hist.loc[x, 'Data']} - {df_hist.loc[x, 'Inspetor']}")
                
                if st.button("👁️ Abrir Detalhes"):
                    conteudo = df_hist.loc[escolha, 'Detalhes'].replace(" // ", "\n")
                    st.warning(f"**Relatório de Pendências:**\n\n{conteudo}")
            else:
                st.info("Nenhuma pendência para detalhar.")
    else:
        st.info("Nenhuma inspeção registrada ainda.")
