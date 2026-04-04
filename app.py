
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --------------------------------------------------
# Datos de tuberías (Tabla 1 del enunciado)
# --------------------------------------------------
tuberias = {
    "12": {"OD_mm": 323.8, "espesor_mm": 10.31, "costo_usd_m": 185},
    "16": {"OD_mm": 406.4, "espesor_mm": 12.70, "costo_usd_m": 260},
    "20": {"OD_mm": 508.0, "espesor_mm": 15.09, "costo_usd_m": 350},
    "24": {"OD_mm": 609.6, "espesor_mm": 17.48, "costo_usd_m": 440}
}

# Datos de aceros (Tabla 2)
aceros = {
    "X52": {"SMYS_psi": 52000, "F": 0.72},
    "X60": {"SMYS_psi": 60000, "F": 0.72}
}

# --------------------------------------------------
# Parámetros fijos (del caso base)
# --------------------------------------------------
L_total_km = 400
P_recepcion = 800
P_min_entrega = 500
T_succ_C = 20
T_succ_R = (T_succ_C + 273.15) * 9/5      # Rankine
gamma = 0.65
Z = 0.90
k = 1.3
eta_comp = 0.85
horas_anuales = 8000
vida_anios = 20
R_univ = 1545                              # ft·lbf/(lbmol·R)
MW_aire = 28.97
MW_gas = gamma * MW_aire
R_gas = R_univ / MW_gas                    # ft·lbf/(lbm·R)

# --------------------------------------------------
# Funciones
# --------------------------------------------------
def diametro_interno(od_mm, esp_mm):
    id_mm = od_mm - 2 * esp_mm
    return id_mm / 25.4                     # pulgadas

def caida_presion_weymouth(P1, Q, L_mi, D_in, gamma, T_R, Z):
    """P1, P2 en psia; Q MMscfd; L_mi millas; D_in pulgadas; T_R Rankine"""
    const = 433.5
    term = const * (Q**2) * (L_mi * gamma * T_R * Z) / (D_in**5.33)
    P2_cuad = P1**2 - term
    # Evitamos presión cero o negativa para no dividir por cero después
    if P2_cuad <= 0.1:
        return 0.1
    return np.sqrt(P2_cuad)

def potencia_compresor(Q, P_suc, P_desc, T_suc_R, Z, R_gas, k, eta):
    """Potencia en HP - con corrección de unidades en densidad estándar"""
    if P_suc <= 0:
        return 0   # protección extra
    Q_scf_s = Q * 1e6 / (24 * 3600)
    # Densidad en condiciones estándar: 14.7 psia, 60°F = 520 R
    # Convertir 14.7 psia a lbf/ft² multiplicando por 144
    P_std_lbf_ft2 = 14.7 * 144
    T_std_R = 520
    Z_std = 1.0
    rho_std = (P_std_lbf_ft2 * MW_gas) / (Z_std * R_univ * T_std_R)   # lb/scf
    m_dot = Q_scf_s * rho_std                                           # lb/s
    n = (k - 1) / k
    head = (Z * R_gas * T_suc_R) * (1/n) * ((P_desc / P_suc)**n - 1)    # ft·lbf/lb
    HP = (m_dot * head) / (550 * eta)
    return HP

def temp_descarga(T_suc_R, P_suc, P_desc, k):
    return T_suc_R * (P_desc / P_suc)**((k - 1)/k)

def maop_barlow(OD_in, espesor_in, SMYS, F):
    return 2 * SMYS * F * espesor_in / OD_in

def costo_tuberia(dn, factor):
    return tuberias[dn]["costo_usd_m"] * (L_total_km * 1000) * factor

def factor_recuperacion(tasa, n):
    if tasa == 0:
        return 1/n
    return tasa * (1 + tasa)**n / ((1 + tasa)**n - 1)

# --------------------------------------------------
# Configuración de Streamlit
# --------------------------------------------------
st.set_page_config(page_title="Gasoducto Trans-Andino", layout="wide")
st.title("📊 Simulación de Gasoducto con Compresión")
st.markdown("Proyecto Optimización de Procesos - Universidad [Tu Universidad]")

# Sidebar
st.sidebar.header("⚙️ Configuración del diseño")
costo_energia = st.sidebar.number_input("Costo de energía (USD/kWh)", value=0.05, step=0.01)
factor_acero = st.sidebar.number_input("Factor de costo del acero (x veces)", value=1.0, step=0.05)
tasa_interes = st.sidebar.number_input("Tasa de interés (%)", value=8.0) / 100.0
costo_comp_por_HP = st.sidebar.number_input("Costo del compresor (USD/HP)", value=1200, step=100)

dn_sel = st.sidebar.selectbox("Diámetro nominal (pulgadas)", options=list(tuberias.keys()))
grado_sel = st.sidebar.selectbox("Grado del acero", options=list(aceros.keys()))

Q = st.sidebar.number_input("Flujo de gas (MMscfd)", value=500, step=50)
N = st.sidebar.slider("Número de estaciones de compresión", 0, 6, 2, 1)

# --------------------------------------------------
# Cálculos de materiales
# --------------------------------------------------
od_mm = tuberias[dn_sel]["OD_mm"]
esp_mm = tuberias[dn_sel]["espesor_mm"]
od_in = od_mm / 25.4
esp_in = esp_mm / 25.4
d_int_in = diametro_interno(od_mm, esp_mm)
SMYS = aceros[grado_sel]["SMYS_psi"]
F = aceros[grado_sel]["F"]
maop = maop_barlow(od_in, esp_in, SMYS, F)

L_mi = L_total_km * 0.621371          # millas totales
L_seg_mi = L_mi / (N + 1)             # millas por segmento

# --------------------------------------------------
# Simulación del perfil de presión
# --------------------------------------------------
distancias_km = [0]
presiones = [P_recepcion]
P_actual = P_recepcion
HP_total = 0
T_max_C = 0

for i in range(N + 1):
    if i < N:
        P_fin_seg = caida_presion_weymouth(P_actual, Q, L_seg_mi, d_int_in, gamma, T_succ_R, Z)
        dist_km = (i+1) * (L_total_km/(N+1))
        distancias_km.append(dist_km)
        presiones.append(P_fin_seg)

        # Verificar que la presión no sea demasiado baja antes de comprimir
        if P_fin_seg < 1.0:
            st.error(f"⚠️ La presión después del segmento {i+1} es demasiado baja ({P_fin_seg:.2f} psia). El diseño no es factible. Aumente el diámetro o reduzca el flujo.")
            st.stop()

        HP = potencia_compresor(Q, P_fin_seg, P_recepcion, T_succ_R, Z, R_gas, k, eta_comp)
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

# --------------------------------------------------
# Costos
# --------------------------------------------------
costo_ducto = costo_tuberia(dn_sel, factor_acero)
costo_compresores = HP_total * costo_comp_por_HP
CAPEX = costo_ducto + costo_compresores
CRF = factor_recuperacion(tasa_interes, vida_anios)
OPEX = HP_total * 0.7457 * horas_anuales * costo_energia   # HP a kW
TAC = CAPEX * CRF + OPEX

# --------------------------------------------------
# Alertas
# --------------------------------------------------
alerta_maop = P_recepcion > maop
alerta_temp = T_max_C > 65
alerta_presion = presiones[-1] < P_min_entrega

# --------------------------------------------------
# Mostrar resultados
# --------------------------------------------------
st.subheader("📌 Resultados principales")
col1, col2, col3 = st.columns(3)
col1.metric("Costo Total Anualizado (TAC)", f"${TAC:,.0f} USD/año")
col2.metric("Potencia total instalada", f"{HP_total:,.0f} HP")
col3.metric("Presión final de entrega", f"{presiones[-1]:.1f} psia")

# Gráfico de presión
st.subheader("📈 Perfil de presión a lo largo del gasoducto")
fig_presion = go.Figure()
fig_presion.add_trace(go.Scatter(x=distancias_km, y=presiones, mode='lines+markers', name='Presión', line=dict(color='blue', width=3)))
fig_presion.add_hline(y=P_min_entrega, line_dash="dash", line_color="red", annotation_text="P mínima entrega (500 psia)")
fig_presion.add_hline(y=maop, line_dash="dash", line_color="orange", annotation_text=f"MAOP = {maop:.1f} psia")
fig_presion.update_layout(xaxis_title="Distancia (km)", yaxis_title="Presión (psia)", template="plotly_white")
st.plotly_chart(fig_presion, use_container_width=True)

# Gráfico de costos
st.subheader("💰 Desglose del Costo Total Anualizado")
costos_anuales = pd.DataFrame({
    "Concepto": ["CAPEX Tubería", "CAPEX Compresores", "OPEX Energía"],
    "Monto (USD/año)": [costo_ducto * CRF, costo_compresores * CRF, OPEX]
})
fig_costos = px.bar(costos_anuales, x="Concepto", y="Monto (USD/año)", text="Monto (USD/año)", color="Concepto", title="TAC por componente")
st.plotly_chart(fig_costos, use_container_width=True)

# Alertas
st.subheader("⚠️ Validación de diseño")
if alerta_maop:
    st.error(f"❌ ALERTA MAOP: La presión de descarga ({P_recepcion} psia) supera el límite de Barlow ({maop:.1f} psia).")
else:
    st.success(f"✅ MAOP OK: {P_recepcion} psia ≤ {maop:.1f} psia")

if alerta_temp:
    st.error(f"❌ ALERTA TÉRMICA: Temperatura máxima de descarga = {T_max_C:.1f} °C > 65 °C.")
else:
    st.success(f"✅ Temperatura OK: Máxima = {T_max_C:.1f} °C ≤ 65 °C")

if alerta_presion:
    st.error(f"❌ ALERTA DE ENTREGA: Presión final = {presiones[-1]:.1f} psia < {P_min_entrega} psia.")
else:
    st.success(f"✅ Presión de entrega OK: {presiones[-1]:.1f} psia ≥ {P_min_entrega} psia")

with st.expander("🔍 Ver detalles técnicos"):
    st.write(f"**Diámetro interno:** {d_int_in:.2f} in")
    st.write(f"**Espesor de pared:** {esp_in:.3f} in")
    st.write(f"**MAOP calculado:** {maop:.1f} psia")
    st.write(f"**Potencia total:** {HP_total:.0f} HP → {HP_total*0.7457:.0f} kW")
    st.write(f"**CRF (tasa {tasa_interes*100:.1f}%, {vida_anios} años):** {CRF:.4f}")
