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
# Use o caminho adequado; se estiver na raiz do repositório, use caminho relativo
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

# ========= 2) CONTROLES NO SIDEBAR =========
# Controle global: Sexo do Comprador (aplicado a todos os gráficos)
selected_sexo = st.sidebar.radio("Sexo do Comprador", options=["Total", "F", "M"])
if selected_sexo != "Total":
    df = df[df['sexo'] == selected_sexo]

# Controle global: Exibir Gráfico de Métodos de Pagamento (Total)
show_payment_total = st.sidebar.checkbox("Exibir Gráfico de Métodos de Pagamento (Total)")

# Expander "Semanas" com opção de "Todas as Semanas" ou "Semana 1"
with st.sidebar.expander("Semanas", expanded=True):
    semana_option = st.radio("Selecione a Semana", options=["Todas as Semanas", "Semana 1"])
    if semana_option == "Semana 1":
        # Se Semana 1 for escolhida, permite selecionar um dia dentro da semana 1:
        dias_semana1 = pd.date_range("2025-03-28", "2025-04-06").tolist()
        dias_semana1_str = [f"{d.strftime('%Y-%m-%d')} ({traduz_dia_semana(d)})" for d in dias_semana1]
        selected_day_str = st.radio("Selecione um dia (Semana 1)", options=dias_semana1_str)
        selected_day_date = pd.to_datetime(selected_day_str[:10]).date()
        show_acessos_chart = st.checkbox("Exibir Gráfico de Acessos Totais (Semana 1)")
    else:
        # Para "Todas as Semanas", não há seleção de dia nem gráfico de acessos por dia
        pass

# ========= 3) EXIBIÇÃO DOS GRÁFICOS =========
if semana_option == "Todas as Semanas":
    st.subheader("Média de Compras por Hora (Todas as Semanas)")
    # Agregar dados por hora (0-23) para todo o dataset
    df_avg = df.groupby('hora')['monto'].mean().reset_index()
    # Cria um gráfico interativo onde x = hora e y = média de monto
    fig_total = go.Figure()
    fig_total.add_trace(go.Scatter(
        x=df_avg['hora'],
        y=df_avg['monto'],
        mode='lines+markers',
        line=dict(color='#FF4B4B', shape='linear'),
        name='Média Monto'
    ))
    fig_total.update_layout(
        title="Média de Compras por Hora - Todas as Semanas",
        xaxis=dict(title="Hora do Dia", dtick=1),
        yaxis=dict(title="Média de Monto", tickformat=",.0f"),
        template="plotly_dark",
        margin=dict(l=20, r=20, t=50, b=50)
    )
    st.plotly_chart(fig_total, use_container_width=True, config={'scrollZoom': True})
    
    # Opcional: Gráfico de acessos para todas as semanas se necessário (aqui você pode implementar caso haja dados)
    
else:  # Se "Semana 1" for escolhida
    # ========= KPIs SEMANA 1 =========
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
    
    # ========= Gráfico Diário Interativo para Semana 1 (Variação Horária) =========
    hourly_data = df.groupby(['data_only', 'hora']).agg({'monto': 'sum', 'boletas': 'sum'}).reset_index()
    selected_day_data = hourly_data[hourly_data['data_only'] == selected_day_date].sort_values('hora')
    selected_day_data['time'] = pd.to_datetime(selected_day_str[:10]) + pd.to_timedelta(selected_day_data['hora'], unit='h')
    
    # Dicionário fixo de acessos
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
    
    # Calcula as vendas do dia: soma das boletas vendidas no dia selecionado
    df_day_full = df[df.index.normalize() == pd.Timestamp(selected_day_date)]
    vendas_dia = df_day_full['boletas'].sum()
    
    # Exibe "Acessos do Dia" e "Vendas do Dia" juntos
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
            showgrid=False
        ),
        font=dict(color='white'),
        margin=dict(l=20, r=20, t=50, b=50),
        title=f"Variação Horária em {selected_day_str[:10]} - Intervalo de 30 minutos"
    )
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
    
    # ========= Gráfico de Acessos Totais para Semana 1 =========
    if show_acessos_chart:
        st.subheader("Acessos Totais")
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
            margin=dict(l=50, r=50, t=50, b=50)
        )
        st.plotly_chart(fig_acessos, use_container_width=True)

# ========= Gráfico de Métodos de Pagamento (Total) =========
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
