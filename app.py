import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ========= CSS PARA ESTILIZAÇÃO DOS KPIs =========
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
df.columns = df.columns.str.strip().str.lower()  # Garante que as colunas sejam: data, hora, sexo, boletas, monto

df['data'] = pd.to_datetime(df['data'], dayfirst=True)
df.set_index('data', inplace=True)

df['hora'] = pd.to_datetime(df['hora'], errors='coerce').dt.hour
df.dropna(subset=['hora'], inplace=True)

# Cria coluna para agrupamento diário
df['data_only'] = df.index.date

# ========= 2) KPIs - Monto Total e Boletas Totais =========
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

# ========= 3) SIDEBAR COM MENUS =========
# Menu para seleção de dia (excluindo registros do dia 5)
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

# ========= 4) GRÁFICO DIÁRIO (Variação Horária) =========
# Agrupa os dados por data e hora para obter a soma de 'monto' e 'boletas'
hourly_data = df.groupby(['data_only', 'hora']).agg({'monto': 'sum', 'boletas': 'sum'}).reset_index()
hourly_data = hourly_data[pd.to_datetime(hourly_data['data_only']).dt.day != 5]

# Filtra os dados para o dia selecionado
selected_day_data = hourly_data[hourly_data['data_only'] == selected_day_date].sort_values('hora')

st.subheader(f"Variação Horária em {selected_day_str}")

fig_day, ax1 = plt.subplots(figsize=(12, 6))
ax2 = ax1.twinx()

line1, = ax1.plot(selected_day_data['hora'], selected_day_data['monto'], marker='o', color='blue', label='Monto')
ax1.set_xlabel("Hora")
ax1.set_ylabel("Monto", color='blue')

line2, = ax2.plot(selected_day_data['hora'], selected_day_data['boletas'], marker='o', color='orange', label='Boletas')
ax2.set_ylabel("Boletas", color='orange')

# ========= Acessos Totais Diários =========
# Valores fixos conforme informado
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

# Anotação com acessos totais
ax1.text(0.05, 0.95, f"Acessos Totais: {acessos_totais}", transform=ax1.transAxes,
         fontsize=12, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.5))

plt.title(f"Variação Horária em {selected_day_str}")
# Combina as legendas de ambos os eixos
lines, labels = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines + lines2, labels + labels2, loc='upper right')
st.pyplot(fig_day)

# ========= 5) GRÁFICO DE MÉTODOS DE PAGAMENTO (DONUT) =========
if show_payment_chart:
    st.subheader("Métodos de Pagamento")
    
    # Dados fixos dos métodos de pagamento (informados separadamente)
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
        labels=None  # Não exibe labels diretamente nos wedges
    )
    # Efeito donut (círculo branco no centro)
    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    fig_pay.gca().add_artist(centre_circle)
    ax_pay.axis('equal')
    plt.title("Cargas por Canal")
    
    # Legenda lateral para os métodos de pagamento
    ax_pay.legend(
        wedges,
        df_payment['Método'],
        title="Métodos",
        loc="center left",
        bbox_to_anchor=(1, 0.5)
    )
    plt.tight_layout()
    st.pyplot(fig_pay)
