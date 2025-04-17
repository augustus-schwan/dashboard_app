import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime

# Função para traduzir o dia da semana para português
def traduz_dia_semana(dt):
    dias = {
        'Monday': 'Segunda',
        'Tuesday': 'Terça',
        'Wednesday': 'Quarta',
        'Thursday': 'Quinta',
        'Friday': 'Sexta',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo'
    }
    return dias.get(dt.strftime('%A'), dt.strftime('%A'))

# CSS para estilização dos KPIs
st.markdown(
    """
    <style>
    .kpi-container {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-bottom: 20px;
    }
    .kpi-box {
        background-color: #f0f2f6;
        border: 2px solid #d1d1d1;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        width: 200px;
        height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .kpi-title {
        font-size: 18px;
        color: #555;
        margin-bottom: 10px;
    }
    .kpi-value {
        font-size: 32px;
        color: #000;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Leitura e preparação dos dados
df = pd.read_csv("dados_editados_semana1.csv")
df.columns = df.columns.str.strip().str.lower()

df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df.dropna(subset=['data'], inplace=True)
df.set_index('data', inplace=True)

df['hora'] = pd.to_datetime(df['hora'], errors='coerce').dt.hour
df.dropna(subset=['hora'], inplace=True)
# Filtra apenas horas válidas
df = df[(df['hora'] >= 0) & (df['hora'] <= 23)]
# Filtra sexo
df = df[df['sexo'].isin(["F","M"])]

# Controles globais
selected_sexo = st.sidebar.radio("Sexo do Comprador", options=["Total","F","M"])
if selected_sexo != "Total":
    df = df[df['sexo'] == selected_sexo]
show_payment_total = st.sidebar.checkbox("Exibir Gráfico de Métodos de Pagamento (Total)")

# Menu de Semanas
with st.sidebar.expander("Semanas", expanded=True):
    semana_option = st.radio("Selecione a Semana", options=["Todas as Semanas","Semana 1"])

# Exibição
if semana_option == "Todas as Semanas":
    st.subheader("Média de Compras por Hora - Todas as Semanas")
    df_avg = df.groupby('hora')['monto'].mean().reindex(range(24), fill_value=0).reset_index()
    fig = go.Figure(data=[go.Bar(
        x=df_avg['hora'],
        y=df_avg['monto'],
        marker_color='indianred'
    )])
    fig.update_layout(
        title="Média de Compras por Hora - Todas as Semanas",
        xaxis=dict(title="Hora do Dia", dtick=1),
        yaxis=dict(title="Média de Monto", tickformat=",.0f"),
        template="plotly_dark",
        margin=dict(l=20,r=20,t=50,b=50)
    )
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom':True})
else:
    # KPIs da Semana 1
    semana1_start = pd.Timestamp("2025-03-28")
    semana1_end = pd.Timestamp("2025-04-06")
    df_sem1 = df[(df.index.normalize() >= semana1_start) & (df.index.normalize() <= semana1_end)]
    total_monto = df_sem1['monto'].sum()
    total_boletas = df_sem1['boletas'].sum()
    ticket_medio = total_monto / df_sem1.shape[0] if df_sem1.shape[0]>0 else 0

    st.subheader("KPIs Semana 1")
    st.markdown(
        f"""
        <div class="kpi-container">
            <div class="kpi-box">
                <div class="kpi-title">Valor</div>
                <div class="kpi-value">{total_monto:,.0f}</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-title">Rifas</div>
                <div class="kpi-value">{total_boletas:,.0f}</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-title">Ticket Médio</div>
                <div class="kpi-value">{ticket_medio:,.2f}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Gráfico Média por Hora - Semana 1
    st.subheader("Média de Compras por Hora - Semana 1")
    df_sem1_avg = df_sem1.groupby('hora')['monto'].mean().reindex(range(24), fill_value=0).reset_index()
    fig1 = go.Figure(data=[go.Bar(
        x=df_sem1_avg['hora'],
        y=df_sem1_avg['monto'],
        marker_color='indianred'
    )])
    fig1.update_layout(
        title="Média de Compras por Hora - Semana 1",
        xaxis=dict(title="Hora do Dia", dtick=1),
        yaxis=dict(title="Média de Monto", tickformat=",.0f"),
        template="plotly_dark",
        margin=dict(l=20,r=20,t=50,b=50)
    )
    st.plotly_chart(fig1, use_container_width=True, config={'scrollZoom':True})

    # Gráfico de Acessos Totais - Semana 1
    st.subheader("Acessos Totais - Semana 1")
    acessos = {28:1251,29:1024,30:1671,31:891,1:1228,2:474,3:423,4:1047,5:5028,6:5112}
    dates = pd.date_range("2025-03-28","2025-04-06")
    dias = [d.strftime('%Y-%m-%d') for d in dates]
    vals = [acessos.get(d.day,0) for d in dates]
    total_acessos = sum(vals)
    st.markdown(f"<h2 style='text-align:center;'>Acessos Totais: {total_acessos}</h2>", unsafe_allow_html=True)
    df_ac = pd.DataFrame({"Data":dias,"Acessos":vals})
    fig2 = go.Figure(data=[go.Bar(x=df_ac['Data'], y=df_ac['Acessos'], marker_color='indianred')])
    fig2.update_layout(
        title=f"Acessos Totais: {total_acessos}",
        xaxis_title="Data", yaxis_title="Acessos",
        template="plotly_dark",
        margin=dict(l=20,r=20,t=50,b=50)
    )
    st.plotly_chart(fig2, use_container_width=True)

# Gráfico de Métodos de Pagamento (Total)
if show_payment_total:
    st.subheader("Métodos de Pagamento (Total)")
    pdm = pd.DataFrame({
        'Método':['QR','VISA-MASTERCARD','TRANSFERENCIA','PERSONAL','DINELCO','AQUI PAGO','CLARO','WEPA'],
        'Porcentagem':[54.5,23.45,13.33,5.19,2.55,0.55,0.42,0.01]
    })
    fig_pay = go.Figure(go.Pie(
        labels=pdm['Método'],
        values=pdm['Porcentagem'],
        hole=0.5,
        marker=dict(colors=None)
    ))
    fig_pay.update_layout(
        title="Cargas por Canal - Total",
        template="plotly_dark",
        margin=dict(l=20,r=20,t=50,b=50),
        legend=dict(orientation="h", y=-0.1)
    )
    st.plotly_chart(fig_pay, use_container_width=True)
