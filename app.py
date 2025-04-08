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

# ========= CSS PARA ESTILIZAÇÃO DOS KPIS =========
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

# ========= 1) LEITURA E PREPARAÇÃO DOS DADOS =========
df = pd.read_csv("dados_editados_semana1.csv")
df.columns = df.columns.str.strip().str.lower()  # Espera-se: data, hora, sexo, boletas, monto

df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df.dropna(subset=['data'], inplace=True)
df.set_index('data', inplace=True)
df.index = pd.to_datetime(df.index, errors='coerce')

df['data_only'] = df.index.date

df['hora'] = pd.to_datetime(df['hora'], errors='coerce').dt.hour
df.dropna(subset=['hora'], inplace=True)

df = df[df['sexo'].isin(["F", "M"])]

# ========= 2) MENU PRINCIPAL: SEMANA 1 =========
with st.sidebar.expander("Semana 1", expanded=True):
    # Define os dias para a Semana 1 (de 2025-03-28 a 2025-04-06)
    dias_semana1 = pd.date_range("2025-03-28", "2025-04-06").tolist()
    dias_semana1_str = [f"{d.strftime('%Y-%m-%d')} ({traduz_dia_semana(d)})" for d in dias_semana1]
    selected_day_str = st.radio("Selecione um dia (Semana 1)", options=dias_semana1_str)
    selected_day_date = pd.to_datetime(selected_day_str[:10]).date()
    
    # Opções específicas de Semana 1
    show_acessos_chart = st.checkbox("Exibir Gráfico de Acessos Totais (Semana 1)")
    selected_sexo = st.radio("Sexo do Comprador", options=["Total", "F", "M"])

if selected_sexo != "Total":
    df = df[df['sexo'] == selected_sexo]

# ========= 2.1) MENU GERAL (fora do expander "Semana 1") =========
# Opção para exibir o gráfico total de métodos de pagamento
show_payment_total = st.sidebar.checkbox("Exibir Gráfico de Métodos de Pagamento (Total)")

# ========= 3) KPIs SEMANA 1 =========
semana1_start = pd.Timestamp("2025-03-28")
semana1_end   = pd.Timestamp("2025-04-06")
df_semana1 = df[(df.index.normalize() >= semana1_start) & (df.index.normalize() <= semana1_end)]

total_monto_semana = df_semana1['monto'].sum()
total_boletas_semana = df_semana1['boletas'].sum()
ticket_medio_semana = total_monto_semana / df_semana1.shape[0] if df_semana1.shape[0] > 0 else 0

st.title("Dashboard de Vendas")
st.subheader("KPIs Semana 1")
st.markdown(
    f"""
    <div class="kpi-container">
        <div class="kpi-box">
            <div class="kpi-title">Valor</div>
            <div class="kpi-value">{total_monto_semana:,.0f}</div>
        </div>
        <div class="kpi-box">
            <div class="kpi-title">Rifas</div>
            <div class="kpi-value">{total_boletas_semana:,.0f}</div>
        </div>
        <div class="kpi-box">
            <div class="kpi-title">Ticket Médio</div>
            <div class="kpi-value">{ticket_medio_semana:,.2f}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ========= 4) GRÁFICO DIÁRIO INTERATIVO (Estilo CoinMarketCap) =========
hourly_data = df.groupby(['data_only', 'hora']).agg({'monto': 'sum', 'boletas': 'sum'}).reset_index()
selected_day_data = hourly_data[hourly_data['data_only'] == selected_day_date].sort_values('hora')
selected_day_data['time'] = pd.to_datetime(selected_day_str[:10]) + pd.to_timedelta(selected_day_data['hora'], unit='h')

acessos_dict = {
    5: 5028,
    6: 5112,
    28: 1251,
    29: 1024,
    30: 1671,
    31: 891,
    1: 1228,
    2: 474,
    3: 423,
    4: 1047
}
day_number = pd.to_datetime(selected_day_str[:10]).day
acessos_totais = acessos_dict.get(day_number, "N/A")

# Calcula a soma das boletas vendidas naquele dia (Vendas do Dia)
df_day_full = df[df.index.normalize() == pd.Timestamp(selected_day_date)]
vendas_dia = df_day_full['boletas'].sum()

# Exibe os "Acessos do Dia" e "Vendas do Dia" centralizados acima do gráfico
st.markdown(
    f"<h2 style='text-align: center;'>Acessos do Dia: {acessos_totais} | Vendas do Dia: {vendas_dia}</h2>",
    unsafe_allow_html=True
)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=selected_day_data['time'],
    y=selected_day_data['monto'],
    mode='lines',
    line=dict(color='#FF4B4B', shape='spline'),
    fill='tozeroy',
    fillcolor='rgba(255,75,75,0.2)',
    name='Monto'
))
fig.update_layout(
    paper_bgcolor='#1F1B24',
    plot_bgcolor='#1F1B24',
    hovermode='x unified',
    xaxis=dict(
        title="Hora",
        rangeslider=dict(visible=False),
        type='date',
        showgrid=False,
        color='white'
    ),
    yaxis=dict(
        title={"text": "Monto", "font": {"color": "white"}},
        tickfont=dict(color="white"),
        tickformat=",.0f",
        showgrid=False,
    ),
    font=dict(color='white'),
    margin=dict(l=20, r=20, t=50, b=50),
    title=f"Variação Horária em {selected_day_str[:10]} - Intervalo de 30 minutos"
)
st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

# ========= 5) GRÁFICO DE MÉTODOS DE PAGAMENTO (DONUT) - TOTAL =========
if show_payment_total:
    st.subheader("Métodos de Pagamento (Total)")
    payment_data = {
        'Método': [
            'QR', 'VISA-MASTERCARD', 'TRANSFERENCIA', 'PERSONAL',
            'DINELCO', 'AQUI PAGO', 'CLARO', 'WEPA'
        ],
        'Porcentagem': [54.50, 23.45, 13.33, 5.19, 2.55, 0.55, 0.42, 0.01]
    }
    df_payment = pd.DataFrame(payment_data)
    fig_pay, ax_pay = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax_pay.pie(
        df_payment['Porcentagem'],
        autopct='%1.2f%%',
        startangle=140,
        labels=None
    )
    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    fig_pay.gca().add_artist(centre_circle)
    ax_pay.axis('equal')
    plt.title("Cargas por Canal - Total")
    ax_pay.legend(
        wedges,
        df_payment['Método'],
        title="Métodos",
        loc="center left",
        bbox_to_anchor=(1, 0.5)
    )
    plt.tight_layout()
    st.pyplot(fig_pay)

# ========= 6) GRÁFICO DE ACESSOS TOTAIS =========
if show_acessos_chart:
    st.subheader("Acessos Totais")
    semana1_dates = pd.date_range("2025-03-28", "2025-04-06").tolist()
    dias_str = [f"{d.strftime('%Y-%m-%d')} ({traduz_dia_semana(d)})" for d in semana1_dates]
    acessos_list = [acessos_dict.get(d.day, None) for d in semana1_dates]
    total_acessos_semana = sum([x for x in acessos_list if x is not None])
    st.markdown(f"<h2 style='text-align: center;'>Acessos Totais: {total_acessos_semana}</h2>", unsafe_allow_html=True)
    
    df_acessos = pd.DataFrame({"Data": dias_str, "Acessos": acessos_list})
    fig_acessos = go.Figure(data=[go.Bar(
        x=df_acessos["Data"],
        y=df_acessos["Acessos"],
        marker_color='indianred'
    )])
    fig_acessos.update_layout(
        title=f"Acessos Totais: {total_acessos_semana}",
        xaxis_title="Data",
        yaxis_title="Acessos",
        template="plotly_dark",
        margin=dict(l=50, r=50, t=50, b=50)
    )
    st.plotly_chart(fig_acessos, use_container_width=True)
