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
# Use o caminho adequado para o seu CSV (caminho relativo se o arquivo estiver no repositório)
df = pd.read_csv("dados_editados_semana1.csv")
df.columns = df.columns.str.strip().str.lower()  # Espera-se: data, hora, sexo, boletas, monto

df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df.dropna(subset=['data'], inplace=True)
df.set_index('data', inplace=True)
df.index = pd.to_datetime(df.index, errors='coerce')

df['data_only'] = df.index.date

# Converte a coluna 'hora' para extrair somente a hora (assumindo formato "HH:MM")
df['hora'] = pd.to_datetime(df['hora'], errors='coerce').dt.hour
df.dropna(subset=['hora'], inplace=True)

# Mantém apenas registros com "sexo" = F ou M
df = df[df['sexo'].isin(["F", "M"])]

# ========= 2) MENU PRINCIPAL: SEMANA 1 =========
with st.sidebar.expander("Semana 1", expanded=True):
    # Define os dias para a Semana 1 (de 2025-03-28 a 2025-04-06)
    dias_semana1 = pd.date_range("2025-03-28", "2025-04-06").tolist()
    dias_semana1_str = [f"{d.strftime('%Y-%m-%d')} ({traduz_dia_semana(d)})" for d in dias_semana1]
    selected_day_str = st.radio("Selecione um dia (Semana 1)", options=dias_semana1_str)
    # Converte para data (usando os 10 primeiros caracteres "YYYY-MM-DD")
    selected_day_date = pd.to_datetime(selected_day_str[:10]).date()
    
    show_payment_chart = st.checkbox("Exibir Gráfico de Métodos de Pagamento (Semana 1)")
    selected_sexo = st.radio("Sexo do Comprador", options=["Total", "F", "M"])

if selected_sexo != "Total":
    df = df[df['sexo'] == selected_sexo]

# ========= 3) KPIs SEMANA 1 =========
# Filtra os dados para a semana 1 (de 2025-03-28 a 2025-04-06)
semana1_start = pd.Timestamp("2025-03-28")
semana1_end   = pd.Timestamp("2025-04-06")
df_semana1 = df[(df.index.normalize() >= semana1_start) & (df.index.normalize() <= semana1_end)]

total_monto_semana = df_semana1['monto'].sum()
total_boletas_semana = df_semana1['boletas'].sum()
# Ticket Médio calculado como total de Monto dividido pelo número de vendas (linhas de df_semana1)
ticket_medio_semana = total_monto_semana / df_semana1.shape[0] if df_semana1.shape[0] > 0 else 0

st.title("Dashboard de Vendas")
st.subheader("KPIs Semana 1")
st.markdown(
    f"""
    <div class="kpi-container">
        <div class="kpi-box">
            <div class="kpi-title">Monto Total</div>
            <div class="kpi-value">{total_monto_semana:,.0f}</div>
        </div>
        <div class="kpi-box">
            <div class="kpi-title">Boletas Totais</div>
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
# Agrupa os dados por data e hora para a semana 1
hourly_data = df.groupby(['data_only', 'hora']).agg({'monto': 'sum', 'boletas': 'sum'}).reset_index()

# Filtra os dados para o dia selecionado
selected_day_data = hourly_data[hourly_data['data_only'] == selected_day_date].sort_values('hora')

# Converte a coluna 'hora' para datetime, somando à data selecionada (para o eixo x)
selected_day_data['time'] = pd.to_datetime(selected_day_str[:10]) + pd.to_timedelta(selected_day_data['hora'], unit='h')

# Valores fixos dos acessos do dia (incluindo dias 05 e 06)
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

# Exibe os "Acessos do Dia" centralizados abaixo do título do gráfico
st.markdown(f"<h2 style='text-align: center;'>Acessos do Dia: {acessos_totais}</h2>", unsafe_allow_html=True)

# Cria o gráfico interativo com Plotly (estilo CoinMarketCap)
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
        rangeslider=dict(visible=False),  # Remove a barra de range slider
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

# ========= 5) GRÁFICO DE MÉTODOS DE PAGAMENTO (DONUT) PARA SEMANA 1 =========
if show_payment_chart:
    st.subheader("Métodos de Pagamento (Semana 1)")
    # Exemplo atualizado dos métodos de pagamento (valores conforme a imagem atualizada)
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
    plt.title("Cargas por Canal - Semana 1")
    ax_pay.legend(
        wedges,
        df_payment['Método'],
        title="Métodos",
        loc="center left",
        bbox_to_anchor=(1, 0.5)
    )
    plt.tight_layout()
    st.pyplot(fig_pay)
