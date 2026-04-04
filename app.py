# app.py
# Simulación de Gasoducto Trans-Andino
# Optimización de Procesos - Estudiante: [Tu nombre]

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --------------------------------------------------
# Configuración de la página
# --------------------------------------------------
st.set_page_config(
    page_title="Gasoducto Trans-Andino",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# Estilo profesional (blanco, azul, gris)
# --------------------------------------------------
st.markdown("""
<style>
    /* Fondo general gris muy claro */
    .stApp {
        background-color: #f4f7f9;
    }
    /* Tarjeta para métricas */
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 6px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        text-align: center;
        border-top: 3px solid #1a5f8b;
    }
    /* Títulos principales en azul oscuro */
    h1, h2, h3 {
        color: #1a3e50;
        font-weight: 500;
    }
    /* Sidebar con fondo gris suave */
    .css-1d391kg {
        background-color: #e9edf0;
    }
    /* Texto en general */
    .stMarkdown, .stText, .stNumberInput, .stSelectbox {
        color: #2c3e50;
    }
    hr {
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Título principal
# --------------------------------------------------
st.title("Gasoducto Trans-Andino")
st.caption("Simulación hidráulica y económica | Optimización de Procesos")

# --------------------------------------------------
# 1. BASE DE DATOS (Tablas del enunciado)
# --------------------------------------------------
tuberias = {
    "12": {"OD_mm": 323.8, "espesor_mm": 10.31, "costo_usd_m": 185},
    "16": {"OD_mm": 406.4, "espesor_mm": 12.70, "costo_usd_m": 260},
    "20": {"OD_mm": 508.0, "espesor_mm": 15.09, "costo_usd_m": 350},
    "24": {"OD_mm": 609.6, "espesor_mm": 17.48, "costo_usd_m": 440}
}

aceros = {
    "X52": {"SMYS_psi": 52000, "F": 0.72},
    "X60": {"SMYS_psi": 60000, "F": 0.72}
}

# --------------------------------------------------
# 2. PARÁMETROS FIJOS (caso base)
# --------------------------------------------------
L_total_km = 400          # longitud total [km]
P_recepcion = 800         # presión de entrada [psia]
P_min_entrega = 500       # presión mínima requerida [psia]
T_succ_C = 20             # temperatura de succión [°C]
T_succ_R = (T_succ_C + 273.15) * 9/5   # Rankine
gamma = 0.65              # gravedad específica
Z = 0.90                  # factor de compresibilidad
k = 1.3                   # relación de calores específicos (gas natural)
eta_comp = 0.85           # eficiencia politrópica
horas_anuales = 8000      # horas de operación al año
vida_anios = 20           # años del proyecto
R_univ = 1545.4           # ft·lbf/(lbmol·R)
P_base = 14.7             # psia (presión estándar)
T_base_R = 520            # Rankine (60°F)
MW_aire = 28.97
MW_gas = gamma * MW_aire  # lb/lbmol

# --------------------------------------------------
# 3. FUNCIONES DE CÁLCULO
# --------------------------------------------------
def diametro_interno(od_mm, esp_mm):
    """Retorna diámetro interno en pulgadas"""
    return (od_mm - 2*esp_mm) / 25.4

def caida_presion_weymouth(P1, Q, L_mi, D_in, gamma, T_R, Z):
    """Ecuación de Weymouth: caída de presión (psia)"""
    const = 433.5
    term = const * (Q**2) * (L_mi * gamma * T_R * Z) / (D_in**5.33)
    P2_cuad = P1**2 - term
    if P2_cuad <= 0.1:
        return 0.1
    return np.sqrt(P2_cuad)

def potencia_compresor(Q, P_suc, P_desc, T_suc_R, Z, k, MW, eta):
    """
    Potencia al freno (BHP) usando fórmula estándar de la industria.
    Basado en Head politrópico.
    """
    r_p = P_desc / P_suc
    n = (k - 1) / k
    # Head politrópico (ft·lbf/lbm)
    H_p = (Z * R_univ * T_suc_R / MW) * (1 / n) * (r_p**n - 1)
    # Potencia de gas (GHP)
    GHP = (Q * 1e6 * P_base * 144 * H_p) / (R_univ * T_base_R * 33000)
    # Potencia al freno
    BHP = GHP / eta
    return BHP

def temp_descarga(T_suc_R, P_suc, P_desc, k):
    """Temperatura de descarga en Rankine"""
    return T_suc_R * (P_desc / P_suc)**((k-1)/k)

def maop_barlow(OD_in, espesor_in, SMYS, F):
    """Presión máxima admisible (psia)"""
    return 2 * SMYS * F * espesor_in / OD_in

def costo_tuberia(dn, factor):
    """Costo total del ducto (USD)"""
    return tuberias[dn]["costo_usd_m"] * (L_total_km * 1000) * factor

def factor_recuperacion(tasa, n):
    """Factor de recuperación de capital (CRF)"""
    if tasa == 0:
        return 1/n
    return tasa * (1+tasa)**n / ((1+tasa)**n - 1)

# --------------------------------------------------
# 4. BARRA LATERAL (configuración)
# --------------------------------------------------
with st.sidebar:
    st.markdown("## Configuración")
    st.markdown("---")
    
    st.markdown("### Económicos")
    costo_energia = st.number_input("Costo energía (USD/kWh)", value=0.05, step=0.01)
    factor_acero = st.number_input("Factor costo acero (x)", value=1.0, step=0.05)
    tasa_interes = st.number_input("Tasa interés (%)", value=8.0) / 100.0
    costo_comp_por_HP = st.number_input("Costo compresor (USD/HP)", value=1200, step=100)
    
    st.markdown("### Materiales")
    dn_sel = st.selectbox("Diámetro nominal (pulg)", options=list(tuberias.keys()))
    grado_sel = st.selectbox("Grado del acero", options=list(aceros.keys()))
    
    st.markdown("### Operación")
    Q = st.number_input("Flujo (MMscfd)", value=500, step=50)
    N = st.slider("Número de estaciones de compresión", 0, 6, 2, 1)

# --------------------------------------------------
# 5. CÁLCULOS DE MATERIALES Y GEOMETRÍA
# --------------------------------------------------
od_mm = tuberias[dn_sel]["OD_mm"]
esp_mm = tuberias[dn_sel]["espesor_mm"]
od_in = od_mm / 25.4
esp_in = esp_mm / 25.4
d_int_in = diametro_interno(od_mm, esp_mm)
SMYS = aceros[grado_sel]["SMYS_psi"]
F = aceros[grado_sel]["F"]
maop = maop_barlow(od_in, esp_in, SMYS, F)

# Longitudes
L_mi = L_total_km * 0.621371          # millas totales
L_seg_mi = L_mi / (N + 1)             # millas por segmento

# --------------------------------------------------
# 6. SIMULACIÓN DEL PERFIL DE PRESIÓN
# --------------------------------------------------
distancias_km = [0]
presiones = [P_recepcion]
P_actual = P_recepcion
HP_total = 0
T_max_C = 0
factible = True

for i in range(N + 1):
    if i < N:
        P_fin_seg = caida_presion_weymouth(P_actual, Q, L_seg_mi, d_int_in, gamma, T_succ_R, Z)
        dist_km = (i+1) * (L_total_km/(N+1))
        distancias_km.append(dist_km)
        presiones.append(P_fin_seg)
        
        if P_fin_seg < 1.0:
            st.error(f"Presión después del segmento {i+1} es demasiado baja ({P_fin_seg:.2f} psia). Diseño inviable. Aumente diámetro o reduzca flujo.")
            factible = False
            break
        
        HP = potencia_compresor(Q, P_fin_seg, P_recepcion, T_succ_R, Z, k, MW_gas, eta_comp)
        HP_total += HP
        
        T2_R = temp_descarga(T_succ_R, P_fin_seg, P_recepcion, k)
        T2_C = (T2_R - 491.67) * 5/9
        if T2_C > T_max_C:
            T_max_C = T2_C
        
        P_actual = P_recepcion
    else:
        P_final = caida_presion_weymouth(P_actual, Q, L_seg_mi, d_int_in, gamma, T_succ_R, Z)
        dist_km = (i+1) * (L_total_km/(N+1))
        distancias_km.append(dist_km)
        presiones.append(P_final)

if not factible:
    st.stop()

# --------------------------------------------------
# 7. CÁLCULO DE COSTOS
# --------------------------------------------------
costo_ducto = costo_tuberia(dn_sel, factor_acero)
costo_compresores = HP_total * costo_comp_por_HP
CAPEX = costo_ducto + costo_compresores
CRF = factor_recuperacion(tasa_interes, vida_anios)
OPEX = HP_total * 0.7457 * horas_anuales * costo_energia   # HP a kW
TAC = CAPEX * CRF + OPEX

# --------------------------------------------------
# 8. MÉTRICAS PRINCIPALES (tarjetas)
# --------------------------------------------------
st.markdown("## Resultados clave")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("TAC (USD/año)", f"${TAC:,.0f}")
    st.markdown('</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Potencia total instalada", f"{HP_total:,.0f} HP")
    st.markdown('</div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric("Presión final de entrega", f"{presiones[-1]:.1f} psia")
    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# 9. GRÁFICO DE PERFIL HIDRÁULICO
# --------------------------------------------------
st.markdown("## Perfil de presión")
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=distancias_km, y=presiones,
    mode='lines+markers',
    name='Presión',
    line=dict(color='#1a5f8b', width=2.5),
    marker=dict(size=6, color='#1a3e50')
))
fig.add_hline(y=P_min_entrega, line_dash="dash", line_color="#c0392b", annotation_text="Presión mínima de entrega (500 psia)")
fig.add_hline(y=maop, line_dash="dash", line_color="#e67e22", annotation_text=f"MAOP = {maop:.0f} psia")
fig.update_layout(
    xaxis_title="Distancia (km)",
    yaxis_title="Presión (psia)",
    template="plotly_white",
    height=450,
    margin=dict(l=0, r=0, t=30, b=0),
    font=dict(color="#2c3e50")
)
st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# 10. DESGLOSE DE COSTOS (gráfico de barras)
# --------------------------------------------------
st.markdown("## Desglose del costo anualizado")
costos_df = pd.DataFrame({
    "Concepto": ["CAPEX Tubería", "CAPEX Compresores", "OPEX Energía"],
    "Monto (USD/año)": [costo_ducto * CRF, costo_compresores * CRF, OPEX]
})
fig2 = px.bar(
    costos_df, x="Concepto", y="Monto (USD/año)",
    text="Monto (USD/año)",
    color="Concepto",
    color_discrete_sequence=["#1a3e50", "#1a5f8b", "#e67e22"],
    title="Costo Total Anualizado (TAC)"
)
fig2.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
fig2.update_layout(showlegend=False, template="plotly_white", height=400, font=dict(color="#2c3e50"))
st.plotly_chart(fig2, use_container_width=True)

# --------------------------------------------------
# 11. ALERTAS Y DETALLES TÉCNICOS
# --------------------------------------------------
st.markdown("## Validaciones")
col_al1, col_al2 = st.columns(2)
with col_al1:
    if P_recepcion > maop:
        st.error("MAOP superado: la presión de descarga excede el límite de Barlow.")
    else:
        st.success(f"MAOP OK: {P_recepcion} psia ≤ {maop:.0f} psia")
    
    if T_max_C > 65:
        st.error(f"Temperatura máxima de descarga: {T_max_C:.1f} °C > 65 °C")
    else:
        st.success(f"Temperatura OK: Máxima {T_max_C:.1f} °C ≤ 65 °C")

with col_al2:
    if presiones[-1] < P_min_entrega:
        st.error(f"Presión final insuficiente: {presiones[-1]:.1f} psia < {P_min_entrega} psia")
    else:
        st.success(f"Presión de entrega OK: {presiones[-1]:.1f} psia ≥ {P_min_entrega} psia")

with st.expander("Detalles técnicos del diseño"):
    st.write(f"**Diámetro interno:** {d_int_in:.2f} in")
    st.write(f"**Espesor de pared:** {esp_in:.3f} in")
    st.write(f"**MAOP (Barlow):** {maop:.0f} psia")
    st.write(f"**Potencia total:** {HP_total:.0f} HP → {HP_total*0.7457:.0f} kW")
    st.write(f"**CRF (tasa {tasa_interes*100:.1f}%):** {CRF:.4f}")
    st.write(f"**Peso molecular del gas:** {MW_gas:.2f} lb/lbmol")

# Pie de página
st.markdown("---")
st.markdown("Proyecto Optimización de Procesos | Simulación de Gasoducto Trans-Andino")
