import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="App Zelador", page_icon="🏢")

# --- SIMULAÇÃO DE BANCO DE DATAS (Em um app real, viria de um CSV ou SQL) ---
# Simulando que a última vistoria foi há 8 dias para testar o alerta
if 'ultima_vistoria' not in st.session_state:
    st.session_state['ultima_vistoria'] = datetime.now() - timedelta(days=8)

# --- LÓGICA DE ALERTA SEMANAL ---
dias_passados = (datetime.now() - st.session_state['ultima_vistoria']).days

if dias_passados >= 7:
    st.error(f"⚠️ ATENÇÃO: A última vistoria foi realizada há {dias_passados} dias. É necessário realizar uma nova inspeção semanal!")

st.title("🏢 Sistema de Inspeção: Zelador")
st.markdown("---")

# --- IDENTIFICAÇÃO ---
st.subheader("1. Identificação")
inspetor = st.text_input("Nome do Responsável pela Inspeção:")
data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

if not inspetor:
    st.info("Por favor, identifique-se para começar.")
    st.stop()

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

# --- GERAÇÃO DE RELATÓRIO ---
st.markdown("---")
if st.button("Finalizar e Gerar Relatório"):
    st.success("Inspeção Concluída!")
    
    # Criar Resumo
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

    # --- BOTÕES DE ENVIO ---
    msg_whatsapp = urllib.parse.quote(relatorio_texto)
    tel_gestor = "5511999999999" # Substitua pelo número real
    
    col_w, col_e = st.columns(2)
    
    with col_w:
        st.markdown(f'[Send to WhatsApp](https://wa.me/{tel_gestor}?text={msg_whatsapp})')
    
    with col_e:
        st.markdown(f'[Send by Email](mailto:gestor@condominio.com?subject=Relatorio_Zelador&body={msg_whatsapp})')
    
    # Atualiza a data da última vistoria
    st.session_state['ultima_vistoria'] = datetime.now()
