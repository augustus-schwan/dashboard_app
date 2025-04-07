import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime

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
df.columns = df.columns.str.strip().str.lower()  # Garante colunas: data, hora, sexo, boletas, monto

df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df.dropna(subset=['data'], inplace=True)
df.set_index('data', inplace=True)
df.index = pd.to_datetime(df.index, errors='coerce')

df['data_only'] = df.index.date

# Converte 'hora' para extrair somente a hora (ex: "HH:MM" -> HH)
df['hora'] = pd.to_datetime(df['hora'], errors='coerce').dt.hour
df.dropna(subset=['hora'], inplace=True)

# Mantém apenas F e M em "sexo"
df = df[df['sexo'].isin(["F", "M"])]

# ========= 2) MENU PRINCIPAL: SEMANA 1 =========
with st.sidebar.expander("Semana 1", expanded=True):
    # Aqui definimos os dias disponíveis (28 ao 06) manualmente ou filtrando do DataFrame.
    # Exemplo manual (se você sabe que o CSV só tem 28/03/2025 até 06/04/2025):
    dias_semana1 = pd.date_range("2025-03-28", "2025-04-06").tolist()
    # Convertemos para strings no formato "YYYY-MM-DD"
    dias_semana1_str = [d.strftime('%Y-%m-%d') for d in dias_semana1]
    
    # Seleciona o dia no menu
    selected_day_str = st.radio("Selecione o Dia (28 ao 06)", options=dias_semana1_str)
    selected_day_date = pd.to_datetime(selected_day_str).date()

    # Método de Pagamento
    show_payment_chart = st.checkbox("Exibir Gráfico de Métodos de Pagamento (Semana 1)")

    # Filtro de Sexo
    selected_sexo = st.radio("Sexo do Comprador", options=["Total", "F", "M"])

# Aplicando o filtro de sexo
if selected_sexo != "Total":
    df = df[df['sexo'] == selected_sexo]

# ========= 3) KPIs (EXEMPLO DO RESTO DO DASHBOARD) =========
# Você pode manter essa parte como "fora" do menu principal de Semana 1, ou ajustar conforme necessário.
total_monto = df['monto'].sum()
total_boletas = df['boletas'].sum()

st.title("Dashboard de Vendas")
st.subheader("KPIs Gerais (Exemplo)")
st.markdown(
    f"""
    <div class="kpi-container">
        <div class="kpi-box">
            <div class="kpi-title">Monto Total (Geral)</div>
            <div class="kpi-value">{total_monto:,.0f}</div>
        </div>
        <div class="kpi-box">
            <div class="kpi-title">Boletas Totais (Geral)</div>
            <div class="kpi-value">{total_boletas:,.0f}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ========= 4) GRÁFICO DIÁRIO (SEMANA 1) =========
# Agrupa os dados por data e hora (dia/hora) para obter soma de 'monto' e 'boletas'
hourly_data = df.groupby(['data_only', 'hora']).agg({'monto': 'sum', 'boletas': 'sum'}).reset_index()

# Filtra para o dia selecionado (entre 28/03 e 06/04)
selected_day_data = hourly_data[hourly_data['data_only'] == selected_day_date].sort_values('hora')

# Cria uma coluna 'time' combinando a data selecionada com a hora
selected_day_data['time'] = pd.to_datetime(selected_day_str) + pd.to_timedelta(selected_day_data['hora'], unit='h')

# Acessos Totais (exemplo)
acessos_dict = {
    28: 1251,
    29: 1024,
    30: 1671,
    31: 891,
    1: 1228,
    2: 474,
    3: 423,
    4: 1047,
    5: 5028,
    6: 5112
}
day_number = pd.to_datetime(selected_day_str).day
acessos_totais = acessos_dict.get(day_number, "N/A")

# Título e Acessos Totais
st.subheader(f"Semana 1 - Variação Horária em {selected_day_str} (Intervalo de 30 minutos)")
st.markdown(f"<h3 style='text-align: center;'>Acessos do Dia: {acessos_totais}</h3>", unsafe_allow_html=True)

# Cria o gráfico interativo com Plotly
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=selected_day_data['time'],
    y=selected_day_data['monto'],
    mode='lines+markers',
    name='Monto',
    line=dict(color='blue', shape='linear')
))
fig.add_trace(go.Scatter(
    x=selected_day_data['time'],
    y=selected_day_data['boletas'],
    mode='lines+markers',
    name='Boletas',
    line=dict(color='orange', shape='linear'),
    yaxis="y2"
))
fig.update_layout(
    title="",
    xaxis=dict(
        title="Hora",
        rangeslider=dict(visible=True),
        type="date"
    ),
    yaxis=dict(
        title={"text": "Monto", "font": {"color": "blue"}},
        tickfont=dict(color="blue"),
        tickformat=",.0f"
    ),
    yaxis2=dict(
        title={"text": "Boletas", "font": {"color": "orange"}},
        tickfont=dict(color="orange"),
        anchor="x",
        overlaying="y",
        side="right"
    ),
    legend=dict(x=0.01, y=0.99),
    margin=dict(l=50, r=50, t=30, b=50)
)
st.plotly_chart(fig, use_container_width=True)

# ========= 5) GRÁFICO DE MÉTODOS DE PAGAMENTO (DONUT) PARA SEMANA 1 =========
if show_payment_chart:
    st.subheader("Métodos de Pagamento (Semana 1)")
    # Exemplo atualizado do método de pagamento
    payment_data = {
        'Método': [
            'QR', 'VISA-MASTERCARD', 'TRANSFERENCIA', 'PERSONAL',
            'DINELCO', 'AQUI PAGO', 'CLARO', 'WEPA'
        ],
        # Exemplo de valores atualizados
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
