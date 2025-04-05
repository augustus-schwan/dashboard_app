import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go

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
# Use o caminho adequado para o seu CSV; se estiver na raiz do repositório, use um caminho relativo:
df = pd.read_csv("dados_editados_semana1.csv")
df.columns = df.columns.str.strip().str.lower()  # Garante que as colunas sejam: data, hora, sexo, boletas, monto

# Converte a coluna 'data' para datetime (dayfirst=True) e define como índice
df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df = df.dropna(subset=['data'])
df.set_index('data', inplace=True)
df.index = pd.to_datetime(df.index, errors='coerce')

# Cria a coluna 'data_only' a partir do índice
df['data_only'] = df.index.date

# Converte a coluna 'hora' para extrair somente a hora (formato "HH:MM" deve estar no CSV)
df['hora'] = pd.to_datetime(df['hora'], errors='coerce').dt.hour
df.dropna(subset=['hora'], inplace=True)

# Exclui registros com valores de "sexo" desconhecidos (mantém apenas "F" e "M")
df = df[df['sexo'].isin(["F", "M"])]

# ========= 2) SIDEBAR COM MENUS =========
# Menu para seleção de dia (excluindo registros cujo dia do mês seja 5)
unique_days = sorted(df['data_only'].unique())
day_options = [
    pd.to_datetime(d).strftime('%Y-%m-%d')
    for d in unique_days if pd.to_datetime(d).day != 5
]
with st.sidebar.expander("Menu de Dias", expanded=True):
    selected_day_str = st.radio("Selecione um dia", options=day_options)
selected_day_date = pd.to_datetime(selected_day_str).date()

# Menu para métodos de pagamento
with st.sidebar.expander("Métodos de Pagamento", expanded=True):
    show_payment_chart = st.checkbox("Exibir Gráfico de Métodos de Pagamento")

# Menu para filtro de sexo, com opção "Total"
with st.sidebar.expander("Filtro de Sexo", expanded=True):
    selected_sexo = st.radio("Selecione o Sexo", options=["Total", "F", "M"])
if selected_sexo != "Total":
    df = df[df['sexo'] == selected_sexo]

# ========= 3) KPIs - MONTO TOTAL E BOLETAS TOTAIS =========
total_monto = df['monto'].sum()
total_boletas = df['boletas'].sum()

st.title("Dashboard de Vendas")
st.subheader("KPIs Totais")
st.markdown(
    f"""
    <div class="kpi-container">
        <div class="kpi-box">
            <div class="kpi-title">Monto Total</div>
            <div class="kpi-value">{total_monto:,.0f}</div>
        </div>
        <div class="kpi-box">
            <div class="kpi-title">Boletas Totais</div>
            <div class="kpi-value">{total_boletas:,.0f}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ========= 4) GRÁFICO DIÁRIO INTERATIVO (Plotly com Range Slider) =========
# Agrupa os dados por data e hora para obter a soma de 'monto' e 'boletas'
hourly_data = df.groupby(['data_only', 'hora']).agg({'monto': 'sum', 'boletas': 'sum'}).reset_index()
hourly_data = hourly_data[pd.to_datetime(hourly_data['data_only']).dt.day != 5]

# Filtra os dados para o dia selecionado
selected_day_data = hourly_data[hourly_data['data_only'] == selected_day_date].sort_values('hora')

# Para que o eixo x seja do tipo datetime (permitindo zoom com rangeslider),
# convertemos a coluna 'hora' (que é numérica) em um datetime, somando a hora à data selecionada.
selected_day_data['time'] = pd.to_datetime(selected_day_str) + pd.to_timedelta(selected_day_data['hora'], unit='h')

# Valores fixos dos acessos diários (conforme informado)
acessos_dict = {
    28: 1251,
    29: 1024,
    30: 1671,
    31: 891,
    1: 1228,
    2: 474,
    3: 423,
    4: 1047
}
day_number = pd.to_datetime(selected_day_str).day
acessos_totais = acessos_dict.get(day_number, "N/A")

# Cria um gráfico interativo com Plotly
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=selected_day_data['time'],
    y=selected_day_data['monto'],
    mode='lines+markers',
    name='Monto',
    line=dict(color='blue')
))
fig.add_trace(go.Scatter(
    x=selected_day_data['time'],
    y=selected_day_data['boletas'],
    mode='lines+markers',
    name='Boletas',
    line=dict(color='orange'),
    yaxis="y2"
))
fig.update_layout(
    title=f"Variação Horária em {selected_day_str} (Intervalo de 30 minutos) - Acessos Totais: {acessos_totais}",
    xaxis=dict(
        title="Hora",
        rangeslider=dict(visible=True),
        type="date"
    ),
    yaxis=dict(
        title={"text": "Monto", "font": {"color": "blue"}},
        tickfont=dict(color="blue")
    ),
    yaxis2=dict(
        title={"text": "Boletas", "font": {"color": "orange"}},
        tickfont=dict(color="orange"),
        anchor="x",
        overlaying="y",
        side="right"
    ),
    legend=dict(x=0.01, y=0.99),
    margin=dict(l=50, r=50, t=50, b=50)
)
st.plotly_chart(fig, use_container_width=True)

# ========= 5) GRÁFICO DE MÉTODOS DE PAGAMENTO (DONUT) =========
if show_payment_chart:
    st.subheader("Métodos de Pagamento")
    payment_data = {
        'Método': [
            'QR', 'VISA-MASTERCARD', 'TRANSFERENCIA', 'PERSONAL',
            'DINELCO', 'AQUI PAGO', 'CLARO', 'WEPA'
        ],
        'Porcentagem': [41.89, 28.85, 18.98, 5.78, 3.19, 0.79, 0.49, 0.02]
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
    plt.title("Cargas por Canal")
    ax_pay.legend(
        wedges,
        df_payment['Método'],
        title="Métodos",
        loc="center left",
        bbox_to_anchor=(1, 0.5)
    )
    plt.tight_layout()
    st.pyplot(fig_pay)
