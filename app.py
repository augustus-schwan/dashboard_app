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
df = pd.read_csv("dados_editados_semana1.csv")
df.columns = df.columns.str.strip().str.lower()  # Assegura que as colunas sejam: data, hora, sexo, boletas, monto

df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df.dropna(subset=['data'], inplace=True)
df.set_index('data', inplace=True)
df.index = pd.to_datetime(df.index, errors='coerce')

df['data_only'] = df.index.date

# Converte a coluna 'hora' para extrair somente a hora (assumindo formato "HH:MM" no CSV)
df['hora'] = pd.to_datetime(df['hora'], errors='coerce').dt.hour
df.dropna(subset=['hora'], inplace=True)

# Mantém apenas F e M em "sexo"
df = df[df['sexo'].isin(["F", "M"])]

# ========= 2) SIDEBAR - MENUS =========
unique_days = sorted(df['data_only'].unique())
day_options = [
    pd.to_datetime(d).strftime('%Y-%m-%d')
    for d in unique_days if pd.to_datetime(d).day != 5
]
with st.sidebar.expander("Menu de Dias", expanded=True):
    selected_day_str = st.radio("Selecione um dia", options=day_options)
selected_day_date = pd.to_datetime(selected_day_str).date()

with st.sidebar.expander("Métodos de Pagamento", expanded=True):
    show_payment_chart = st.checkbox("Exibir Gráfico de Métodos de Pagamento")

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

# ========= 4) GRÁFICO DIÁRIO INTERATIVO (Monto e Boletas em linhas retas) =========
df_day = df[df.index.normalize() == pd.Timestamp(selected_day_date)].copy()
df_day['time'] = pd.to_datetime(selected_day_str) + pd.to_timedelta(df_day['hora'], unit='h')

# Reamostra a cada 30 minutos
df_resampled = df_day.resample('30T', on='time').agg({'monto': 'sum', 'boletas': 'sum'}).reset_index()

# Caso não haja dados para o dia selecionado
if df_resampled.empty:
    st.warning("Nenhum dado para este dia.")
else:
    # Picos (valores máximos) para dimensionar cada eixo
    max_monto_30min = df_resampled['monto'].max()
    max_boletas_30min = df_resampled['boletas'].max()

    # Valores fixos dos acessos diários
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

    fig = go.Figure()
    # Linha do Monto (reta, shape padrão 'linear')
    fig.add_trace(go.Scatter(
        x=df_resampled['time'],
        y=df_resampled['monto'],
        mode='lines+markers',
        name='Monto',
        line=dict(color='blue'),
    ))
    # Linha das Boletas (reta, shape padrão 'linear', no eixo secundário)
    fig.add_trace(go.Scatter(
        x=df_resampled['time'],
        y=df_resampled['boletas'],
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
            tickfont=dict(color="blue"),
            range=[0, max_monto_30min * 1.1 if max_monto_30min else 1]
        ),
        yaxis2=dict(
            title={"text": "Boletas", "font": {"color": "orange"}},
            tickfont=dict(color="orange"),
            anchor="x",
            overlaying="y",
            side="right",
            range=[0, max_boletas_30min * 1.1 if max_boletas_30min else 1]
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
