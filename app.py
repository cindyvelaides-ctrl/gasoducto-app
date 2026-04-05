import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from math import sqrt

# --------------------------------------------------------------
# Configuración de la página (fondo negro, título en mayúscula y azul)
# --------------------------------------------------------------
st.set_page_config(page_title="OPTIMIZACIÓN DE GASODUCTO TRANS-ANDINO", layout="wide")

# CSS personalizado: fondo negro, letras blancas, títulos azules, recuadros para resultados
st.markdown(
    """
    <style>
        /* Fondo negro general */
        .stApp {
            background-color: black;
        }
        /* Color de texto base blanco */
        body, .stMarkdown, .stText, .stNumberInput label, .stSelectbox label, .stSlider label {
            color: white !important;
        }
        /* Título principal: mayúscula, negrita, azul */
        .titulo-principal {
            color: #1E88E5;
            font-weight: bold;
            text-transform: uppercase;
            text-align: center;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        /* Subtítulos y otros textos en blanco */
        h2, h3, h4 {
            color: white;
        }
        /* Recuadros para métricas */
        .recuadro-metrica {
            background-color: #1e1e1e;
            border-left: 5px solid #1E88E5;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        }
        .recuadro-metrica p {
            font-size: 1.2rem;
            margin: 0;
            color: white;
        }
        .recuadro-metrica .valor {
            font-size: 1.8rem;
            font-weight: bold;
            color: #1E88E5;
        }
        /* Sidebar con fondo gris oscuro y texto blanco */
        .css-1d391kg, .css-12oz5g7 {
            background-color: #0E1117;
        }
        .sidebar .sidebar-content {
            background-color: #0E1117;
        }
        /* Alertas */
        .stAlert {
            background-color: #2c2c2c;
            color: white;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Título principal (azul, mayúscula, negrita)
st.markdown('<p class="titulo-principal">Optimización y Simulación Digital de Sistemas de Transporte de Gas</p>', unsafe_allow_html=True)
st.markdown("### Gasoducto Trans-Andino | Diseño técnico-económico")

# --------------------------------------------------------------
# Funciones auxiliares (cálculos)
# --------------------------------------------------------------

def pulgadas_a_mm(pulg):
    return pulg * 25.4

def mm_a_pulg(mm):
    return mm / 25.4

def km_a_millas(km):
    return km * 0.621371

def celsius_a_rankine(c):
    return (c + 273.15) * 9/5

def obtener_diametro_interno(diam_nom_pulg, cedula=40):
    """
    Retorna el diámetro interno en pulgadas para tubería Schedule 40.
    Datos según tabla del enunciado.
    """
    # Datos: (OD_mm, espesor_mm)
    tabla = {
        12: (323.8, 10.31),
        16: (406.4, 12.70),
        20: (508.0, 15.09),
        24: (609.6, 17.48)
    }
    od_mm, espesor_mm = tabla[diam_nom_pulg]
    id_mm = od_mm - 2*espesor_mm
    return mm_a_pulg(id_mm)

def costo_tuberia_por_metro(diam_nom_pulg):
    """Costo base en USD/m según tabla del enunciado."""
    costos = {12: 185, 16: 260, 20: 350, 24: 440}
    return costos[diam_nom_pulg]

def barlow_pmax(smys_psi, factor_diseno, espesor_pulg, od_pulg):
    """Presión máxima admisible (MAOP) en psia según Barlow."""
    return (2 * smys_psi * factor_diseno * espesor_pulg) / od_pulg

def weymouth_constante(Q, E, L_millas, gamma, T_rankine, Z, D_pulg):
    """
    Retorna el término C de la ecuación de Weymouth:
    P1^2 - P2^2 = C
    """
    factor = 433.5 * (Q / E)**2
    numerador = L_millas * gamma * T_rankine * Z
    denominador = D_pulg**5.33
    return factor * numerador / denominador

def calcular_perfil_y_estaciones(Q, D_pulg, L_km, gamma, T_rankine, Z, E,
                                 P_inicial_psia, P_entrega_min_psia,
                                 N_estaciones, smys_psi, espesor_pulg, od_pulg, factor_diseno=0.72):
    """
    Realiza el balance hacia atrás para determinar presiones de descarga y succión,
    potencia y temperaturas.
    Retorna:
        - lista de distancias (km) para graficar
        - lista de presiones (psia) en esos puntos
        - lista de potencias por estación (HP)
        - lista de temperaturas de descarga (°C)
        - mensajes de alerta (lista)
        - bandera de factibilidad
    """
    L_millas_tot = km_a_millas(L_km)
    L_seg_millas = L_millas_tot / N_estaciones
    L_seg_km = L_km / N_estaciones

    # Constante C de Weymouth por segmento (depende solo de propiedades y Q)
    # Nota: C = 433.5*(Q/E)^2 * (L_seg*gamma*T*Z)/D^5.33
    C_seg = weymouth_constante(Q, E, L_seg_millas, gamma, T_rankine, Z, D_pulg)

    # Inicializar vectores para almacenar presiones en cada punto de estación
    # Tendremos N_estaciones + 1 puntos: [inicio, tras seg1, tras seg2, ..., final]
    P_suction = [0.0] * N_estaciones      # presión de succión de cada estación
    P_discharge = [0.0] * N_estaciones    # presión de descarga
    P_seg_end = [0.0] * (N_estaciones)    # presión al final de cada segmento (entrada a siguiente estación o final)
    
    # Presión final objetivo = P_entrega_min_psia
    P_final_obj = P_entrega_min_psia
    P_seg_end[N_estaciones-1] = P_final_obj  # después del último segmento
    
    # Recorrido hacia atrás para calcular presión de descarga necesaria en cada estación
    for i in range(N_estaciones-1, -1, -1):
        # P_down = presión al final del segmento i
        P_down = P_seg_end[i]
        # Presión requerida al inicio del segmento (que es la descarga de la estación i)
        P_up_req = sqrt(P_down**2 + C_seg)
        P_discharge[i] = P_up_req
        
        if i == 0:
            # Primera estación: la succión es la presión de recepción fija
            P_suction[i] = P_inicial_psia
        else:
            # Para i>0, la succión es la presión al final del segmento anterior
            P_suction[i] = P_seg_end[i-1]
        
        # Ahora, la presión al final del segmento anterior (si i>0) se calcula hacia adelante:
        # pero aún no lo tenemos para i-1. Hacemos: para i-1, P_seg_end[i-1] = P_discharge[i-1]? No.
        # En este loop, necesitamos también calcular la presión al inicio del segmento i (que es P_discharge[i])
        # pero P_seg_end[i-1] será la presión después de comprimir en estación i-1 y recorrer el segmento i-1.
        # Debemos resolver hacia atrás completamente: después de obtener P_discharge[i], podemos obtener
        # P_seg_end[i-1] a partir de P_suction[i]? No, P_suction[i] = P_seg_end[i-1].
        # Entonces:
        if i > 0:
            P_seg_end[i-1] = P_suction[i]
    
    # Verificar que la primera estación no requiera una relación de compresión imposible (r<1)
    alertas = []
    factible = True
    # Calcular potencias y temperaturas, además verificar MAOP y temperatura
    total_HP = 0.0
    T1_kelvin = 293.15  # 20°C
    T1_rankine = celsius_a_rankine(20)
    k = 1.3   # relación de calores específicos para gas natural
    eta = 0.85  # eficiencia adiabática
    # Constante R para la fórmula de potencia: R_univ = 1545 ft·lbf/(lbmol·R)
    M_gas = 28.97 * gamma   # masa molar lb/lbmol
    R_esp = 1545 / M_gas    # ft·lbf/(lb·R)
    
    potencias_HP = []
    temps_desc_c = []
    
    for i in range(N_estaciones):
        r = P_discharge[i] / P_suction[i]
        if r < 1.0:
            alertas.append(f"⚠️ Estación {i+1}: relación de compresión {r:.3f} < 1. Diseño inviable.")
            factible = False
            potencias_HP.append(0)
            temps_desc_c.append(0)
            continue
        
        # Potencia (HP) según ecuación del enunciado
        # HP = (Q*1e6)/(24*3600*eta) * (Z*R_esp*T1)/(k-1) * (r^((k-1)/k)-1)
        Q_scfd = Q * 1e6
        flujo_masico = Q_scfd / (24 * 3600)   # scf/s
        term1 = flujo_masico / eta
        term2 = (Z * R_esp * T1_rankine) / (k - 1)
        term3 = (r**((k-1)/k) - 1)
        HP = term1 * term2 * term3
        potencias_HP.append(HP)
        total_HP += HP
        
        # Temperatura de descarga (Rankine)
        T2_rankine = T1_rankine * (r**((k-1)/k))
        T2_celsius = (T2_rankine - 491.67) * 5/9
        temps_desc_c.append(T2_celsius)
        if T2_celsius > 65:
            alertas.append(f"⚠️ Estación {i+1}: Temperatura de descarga {T2_celsius:.1f}°C > 65°C.")
            factible = False
        
        # Verificar MAOP
        pmax = barlow_pmax(smys_psi, factor_diseno, espesor_pulg, od_pulg)
        if P_discharge[i] > pmax:
            alertas.append(f"⚠️ Estación {i+1}: Presión de descarga {P_discharge[i]:.0f} psia > MAOP ({pmax:.0f} psia).")
            factible = False
    
    # Generar perfil de presión a lo largo de toda la tubería (resolución fina)
    distancias_km = []
    presiones_psia = []
    # Iterar sobre cada segmento
    for i in range(N_estaciones):
        # punto inicial del segmento = descarga de estación i
        P_start = P_discharge[i]
        # para cada segmento, dividimos en 20 puntos
        for j in range(21):
            frac = j / 20.0
            dist = i * L_seg_km + frac * L_seg_km
            # Presión según Weymouth: P^2 = P_start^2 - C_seg * (distancia_recorrida / L_seg)
            # distancia recorrida en millas dentro del segmento
            dist_rec_millas = km_a_millas(frac * L_seg_km)
            C_total_rec = weymouth_constante(Q, E, dist_rec_millas, gamma, T_rankine, Z, D_pulg)
            P_actual = sqrt(max(0, P_start**2 - C_total_rec))
            distancias_km.append(dist)
            presiones_psia.append(P_actual)
    # Presión final (aseguramos)
    distancias_km.append(L_km)
    presiones_psia.append(P_seg_end[N_estaciones-1])
    
    # Última presión final real
    P_final_real = P_seg_end[N_estaciones-1]
    if P_final_real < P_entrega_min_psia - 1:
        alertas.append(f"⚠️ Presión final {P_final_real:.1f} psia < {P_entrega_min_psia} psia requerida.")
        factible = False
    
    return distancias_km, presiones_psia, potencias_HP, temps_desc_c, total_HP, P_final_real, alertas, factible

# --------------------------------------------------------------
# Sidebar: configuración
# --------------------------------------------------------------
st.sidebar.markdown("## ⚙️ Panel de Configuración")
st.sidebar.markdown("Modifique los parámetros del diseño:")

# Parámetros económicos
st.sidebar.subheader("💰 Parámetros Económicos")
costo_energia = st.sidebar.number_input("Costo de energía (USD/kWh)", min_value=0.01, value=0.05, step=0.01, format="%.3f")
factor_costo_aceros = st.sidebar.number_input("Factor costo del acero (multiplicador)", min_value=0.5, value=1.0, step=0.05)
tasa_interes = st.sidebar.number_input("Tasa de interés anual (%)", min_value=0.0, value=8.0, step=0.5) / 100.0
vida_util = st.sidebar.number_input("Vida útil del proyecto (años)", min_value=5, value=20, step=1)
costo_compresor_por_HP = st.sidebar.number_input("Costo de compresor (USD/HP)", min_value=100, value=800, step=50)
horas_operacion = st.sidebar.number_input("Horas operación anuales", min_value=1000, value=8000, step=500)

# Selección de materiales
st.sidebar.subheader("🔩 Materiales")
diam_nom = st.sidebar.selectbox("Diámetro nominal (pulgadas)", [12, 16, 20, 24], format_func=lambda x: f"{x}\"")
grado_acero = st.sidebar.selectbox("Grado de acero", ["X52", "X60"], index=0)
if grado_acero == "X52":
    smys = 52000
else:
    smys = 60000
factor_diseno = 0.72

# Variables operativas
st.sidebar.subheader("📈 Variables Operativas")
Q_diseno = st.sidebar.number_input("Flujo de gas Q (MMscfd)", min_value=100, max_value=2000, value=500, step=10)
N_est = st.sidebar.slider("Número de estaciones de compresión", min_value=1, max_value=10, value=3, step=1)

# --------------------------------------------------------------
# Datos fijos del caso base
# --------------------------------------------------------------
L_total_km = 400.0
P_recepcion = 800.0      # psia
P_entrega_min = 500.0    # psia
gamma_gas = 0.65
Z_factor = 0.90
T_succion_C = 20.0
T_rankine = celsius_a_rankine(T_succion_C)
E_weymouth = 0.92        # eficiencia de la tubería

# Obtener propiedades geométricas de la tubería
ID_pulg = obtener_diametro_interno(diam_nom)
OD_mm, espesor_mm = {12:(323.8,10.31),16:(406.4,12.70),20:(508.0,15.09),24:(609.6,17.48)}[diam_nom]
OD_pulg = mm_a_pulg(OD_mm)
espesor_pulg = mm_a_pulg(espesor_mm)

# Cálculo del diseño
distancias, presiones, potencias, temps, total_HP, P_final, alertas, factible = calcular_perfil_y_estaciones(
    Q_diseno, ID_pulg, L_total_km, gamma_gas, T_rankine, Z_factor, E_weymouth,
    P_recepcion, P_entrega_min, N_est, smys, espesor_pulg, OD_pulg, factor_diseno
)

# --------------------------------------------------------------
# Cálculo de costos (TAC)
# --------------------------------------------------------------
# CAPEX tubería
longitud_m = L_total_km * 1000
costo_tubo_base = costo_tuberia_por_metro(diam_nom) * longitud_m
costo_tubo_total = costo_tubo_base * factor_costo_aceros
# CAPEX compresores
costo_compresores = total_HP * costo_compresor_por_HP
CAPEX_total = costo_tubo_total + costo_compresores

# CRF
if tasa_interes == 0:
    CRF = 1 / vida_util
else:
    CRF = (tasa_interes * (1+tasa_interes)**vida_util) / ((1+tasa_interes)**vida_util - 1)

# OPEX (energía)
potencia_kW = total_HP * 0.7457
energia_anual_kWh = potencia_kW * horas_operacion
OPEX_energia = energia_anual_kWh * costo_energia
# (Podría agregarse mantenimiento, pero por simplicidad solo energía)
OPEX_total = OPEX_energia

TAC = (CAPEX_total * CRF) + OPEX_total

# --------------------------------------------------------------
# Panel principal: métricas en recuadros
# --------------------------------------------------------------
st.markdown("## 📊 Tablero de Resultados")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
    <div class="recuadro-metrica">
        <p>Costo Total Anualizado (TAC)</p>
        <p class="valor">${TAC:,.0f} /año</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="recuadro-metrica">
        <p>Potencia Total Instalada</p>
        <p class="valor">{total_HP:,.0f} HP</p>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="recuadro-metrica">
        <p>Presión Final de Entrega</p>
        <p class="valor">{P_final:.1f} psia</p>
    </div>
    """, unsafe_allow_html=True)

# --------------------------------------------------------------
# Gráfico de perfil de presión (Plotly)
# --------------------------------------------------------------
st.markdown("## 📈 Perfil Hidráulico: Presión vs Distancia")
fig = go.Figure()
fig.add_trace(go.Scatter(x=distancias, y=presiones, mode='lines', name='Presión en tubería',
                         line=dict(color='#1E88E5', width=3)))
# Marcar posiciones de estaciones
dist_estaciones = [i * (L_total_km / N_est) for i in range(N_est)]
pres_estaciones = []
for i, d in enumerate(dist_estaciones):
    idx = min(range(len(distancias)), key=lambda j: abs(distancias[j]-d))
    pres_estaciones.append(presiones[idx])
fig.add_trace(go.Scatter(x=dist_estaciones, y=pres_estaciones, mode='markers',
                         marker=dict(color='red', size=10, symbol='triangle-up'),
                         name='Estación de compresión'))
fig.update_layout(
    title="Presión a lo largo del gasoducto",
    xaxis_title="Distancia (km)",
    yaxis_title="Presión (psia)",
    template="plotly_dark",
    paper_bgcolor="black",
    plot_bgcolor="black",
    font_color="white"
)
st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------------------
# Desglose de costos (gráfico de barras)
# --------------------------------------------------------------
st.markdown("## 💰 Desglose de Costos Anualizados")
capex_anual = CAPEX_total * CRF
datos_costos = {
    "Concepto": ["CAPEX Tubería", "CAPEX Compresores", "OPEX Energía"],
    "Monto (USD/año)": [costo_tubo_total * CRF, costo_compresores * CRF, OPEX_energia]
}
df_costos = pd.DataFrame(datos_costos)
st.bar_chart(df_costos.set_index("Concepto"), color="#1E88E5")

# También opcional: gráfico de torta con plotly
fig_pie = go.Figure(data=[go.Pie(labels=datos_costos["Concepto"], values=datos_costos["Monto (USD/año)"],
                                 hole=0.3, marker=dict(colors=["#1E88E5", "#FFA000", "#43A047"]))])
fig_pie.update_layout(template="plotly_dark", paper_bgcolor="black", font_color="white")
st.plotly_chart(fig_pie, use_container_width=True)

# --------------------------------------------------------------
# Validaciones y alertas
# --------------------------------------------------------------
st.markdown("## ⚠️ Validaciones de Seguridad y Cumplimiento")
if alertas:
    for alert in alertas:
        st.error(alert)
else:
    if factible:
        st.success("✅ Todos los parámetros cumplen las restricciones: presión de entrega ≥500 psia, MAOP respetado, temperatura <65°C.")
    else:
        st.warning("⚠️ Existen incumplimientos. Revise las alertas específicas.")

# Mostrar detalles de cada estación (tabla)
st.markdown("## 🏭 Detalle por Estación de Compresión")
if N_est > 0:
    df_est = pd.DataFrame({
        "Estación": [f"{i+1}" for i in range(N_est)],
        "Presión succión (psia)": [P_recepcion if i==0 else None for i in range(N_est)],  # simplificado
        "Presión descarga (psia)": [f"{p:.1f}" for p in presiones[::len(presiones)//N_est][:N_est]],
        "Potencia (HP)": [f"{p:.0f}" for p in potencias],
        "Temperatura descarga (°C)": [f"{t:.1f}" for t in temps]
    })
    st.dataframe(df_est, use_container_width=True)

# Nota final sobre unidades
st.caption("Nota: Las ecuaciones siguen el enunciado. La potencia se calcula con la fórmula provista, eficiencia η=0.85, k=1.3.")
