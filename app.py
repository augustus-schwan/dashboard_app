import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime

# ---------- Função para traduzir o dia da semana para português ----------
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

# ---------- CSS PARA ESTILIZAÇÃO DOS KPIS ----------
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

# ---------- 1) LEITURA E PREPARAÇÃO DOS DADOS ----------
df = pd.read_csv("dados_editados_semana1.csv")
df.columns = df.columns.str.strip().str.lower()  # espera: data, hora, sexo, boletas, monto

df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df.dropna(subset=['data'], inplace=True)
df.set_index('data', inplace=True)
df.index = pd.to_datetime(df.index, errors='coerce')

df['data_only'] = df.index.date

df['hora'] = pd.to_datetime(df['hora'], errors='coerce').dt.hour
df.dropna(subset=['hora'], inplace=True)

# Se houver horas fora de [0..23], podemos filtrar:
df = df[(df['hora'] >= 0) & (df['hora'] <= 23)]

# Mantém somente "F" e "M" em "sexo"
df = df[df['sexo'].isin(["F", "M"])]

# ---------- 2) CONTROLES GERAIS NO SIDEBAR ----------
# Filtro de Sexo do Comprador (aplica-se globalmente)
selected_sexo = st.sidebar.radio("Sexo do Comprador", options=["Total", "F", "M"])
if selected_sexo != "Total":
    df = df[df['sexo'] == selected_sexo]

# Checkbox para exibir o gráfico de Métodos de Pagamento (Total)
show_payment_total = st.sidebar.checkbox("Exibir Gráfico de Métodos de Pagamento (Total)")

# ---------- Expander "Semanas" ----------
with st.sidebar.expander("Semanas", expanded=True):
    semana_option = st.radio(
        "Selecione a Semana",
        options=["Todas as Semanas", "Semana 1"]
    )

# ---------- 3) LÓGICA DE EXIBIÇÃO ----------
if semana_option == "Todas as Semanas":
    # ========== GRÁFICO DE MÉDIA DE COMPRAS POR HORA (TODAS AS SEMANAS) ==========
    st.subheader("Média de Compras por Hora - Todas as Semanas")
    
    # Agrupamos por hora e calculamos a média de 'monto'
    df_avg = df.groupby('hora')['monto'].mean().reset_index()
    # Cria o gráfico de barras
    fig_total = go.Figure(data=[go.Bar(
        x=df_avg['hora'],
        y=df_avg['monto'],
        marker_color='red'
    )])
    fig_total.update_layout(
        xaxis=dict(title="Hora do Dia", dtick=1),
        yaxis=dict(title="Média de Monto", tickformat=",.0f"),
        template="plotly_dark",
        margin=dict(l=20, r=20, t=50, b=50),
        title="Média de Compras por Hora - Todas as Semanas"
    )
    st.plotly_chart(fig_total, use_container_width=True, config={'scrollZoom': True})

else:
    # ---------- SEMANA 1 ----------
    # Filtro fixo para o período da Semana 1 (28/03 a 06/04)
    semana1_start = pd.Timestamp("2025-03-28")
    semana1_end   = pd.Timestamp("2025-04-06")
    df_semana1 = df[(df.index.normalize() >= semana1_start) & (df.index.normalize() <= semana1_end)]
    
    # KPIs da Semana 1
    total_monto_semana = df_semana1['monto'].sum()
    total_boletas_semana = df_semana1['boletas'].sum()
    ticket_medio_semana = total_monto_semana / df_semana1.shape[0] if df_semana1.shape[0] > 0 else 0
    
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
    
    # ========== GRÁFICO DE MÉDIA DE COMPRAS POR HORA (SEMANA 1) ==========
    st.subheader("Média de Compras por Hora - Semana 1")
    df_sem1_avg = df_semana1.groupby('hora')['monto'].mean().reset_index()
    # Cria um gráfico de barras
    fig_sem1 = go.Figure(data=[go.Bar(
        x=df_sem1_avg['hora'],
        y=df_sem1_avg['monto'],
        marker_color='red'
    )])
    fig_sem1.update_layout(
        xaxis=dict(title="Hora do Dia", dtick=1),
        yaxis=dict(title="Média de Monto", tickformat=",.0f"),
        template="plotly_dark",
        margin=dict(l=20, r=20, t=50, b=50),
        title="Média de Compras por Hora - Semana 1"
    )
    st.plotly_chart(fig_sem1, use_container_width=True, config={'scrollZoom': True})
    
    # ========== GRÁFICO DE ACESSOS TOTAIS (SEMANA 1) ==========
    st.subheader("Acessos Totais - Semana 1")
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
    semana1_dates = pd.date_range("2025-03-28", "2025-04-06").tolist()
    dias_str = [f"{d.strftime('%Y-%m-%d')} ({traduz_dia_semana(d)})" for d in semana1_dates]
    acessos_list = [acessos_dict.get(d.day, 0) for d in semana1_dates]
    total_acessos_semana = sum(acessos_list)
    
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
        margin=dict(l=20, r=50, t=50, b=50)
    )
    st.plotly_chart(fig_acessos, use_container_width=True)

# ---------- GRÁFICO DE MÉTODOS DE PAGAMENTO (TOTAL) ----------
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
