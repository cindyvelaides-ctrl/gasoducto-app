import streamlit as st
import plotly.graph_objects as go
import numpy as np
import math

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE ESTILO (CSS)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* fondo negro y texto blanco por defecto */
    .stApp { background-color: #000000; }
    .stMarkdown, .stText, .stSelectbox, .stSlider, .stNumberInput, .stMetric { color: #ffffff !important; }
    label, p, span, div { color: #ffffff !important; }
    
    /* título principal: mayúsculas, negrita, azul */
    h1.main-title { 
        color: #0066ff !important; 
        font-weight: bold !important; 
        text-transform: uppercase !important; 
        text-align: center;
    }
    
    /* títulos de resultados en recuadros */
    .boxed-title {
        background-color: #111111;
        border: 1px solid #333333;
        padding: 8px 12px;
        margin: 10px 0 15px 0;
        border-radius: 4px;
        font-size: 1.1rem;
        font-weight: 600;
        color: #ffffff;
    }
    
    /* cajas de alerta y validación */
    .alert-ok { background-color: #0f2b0f; border: 1px solid #2e7d32; color: #a5d6a7; padding: 8px; border-radius: 4px; margin-bottom: 5px; }
    .alert-warn { background-color: #331a00; border: 1px solid #ff9800; color: #ffcc80; padding: 8px; border-radius: 4px; margin-bottom: 5px; }
    .alert-err { background-color: #2b0f0f; border: 1px solid #c62828; color: #ef9a9a; padding: 8px; border-radius: 4px; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">optimización y simulación digital de sistemas de transporte de gas</h1>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. PANEL DE CONFIGURACIÓN (SIDEBAR)
# -----------------------------------------------------------------------------
st.sidebar.header("panel de configuración")

# parámetros económicosenergy_cost = st.sidebar.number_input("costo de energía ($/kwh)", value=0.10, step=0.01)
interest_rate = st.sidebar.number_input("tasa de interés anual (%)", value=8.0, step=0.5) / 100.0
project_life = st.sidebar.number_input("vida útil del proyecto (años)", value=20, step=1)
comp_cost_per_hp = st.sidebar.number_input("costo compresor ($/hp)", value=850, step=50)

# selección de material
pipe_data = {
    "12\"": {"do_mm": 323.8, "t_mm": 10.31, "cost_m": 185},
    "16\"": {"do_mm": 406.4, "t_mm": 12.70, "cost_m": 260},
    "20\"": {"do_mm": 508.0, "t_mm": 15.09, "cost_m": 350},
    "24\"": {"do_mm": 609.6, "t_mm": 17.48, "cost_m": 440}
}
selected_pipe = st.sidebar.selectbox("diámetro comercial", list(pipe_data.keys()))

steel_data = {
    "x52": {"smys": 52000, "f": 0.72},
    "x60": {"smys": 60000, "f": 0.72}
}
selected_steel = st.sidebar.selectbox("grado de acero", list(steel_data.keys()))

# variables operativas
q_mmscfd = st.sidebar.number_input("flujo de diseño q (mmscfd)", value=500.0, step=10.0)
n_stations = st.sidebar.slider("número de estaciones de compresión (n)", min_value=1, max_value=10, value=1)

# -----------------------------------------------------------------------------
# 3. CONSTANTES Y CONVERSIÓN DE UNIDADES
# -----------------------------------------------------------------------------
# propiedades del gas y condiciones base
gamma = 0.65          # gravedad específica
z = 0.90              # factor de compresibilidad
t_k = 293.15          # temperatura de succión [K]
t_r = t_k * 1.8       # conversión a rankine [°R] (para ecuaciones en sistema inglés)
e_eff = 0.92          # eficiencia de flujo (típica en weymouth)
eta_comp = 0.75       # eficiencia isentrópica del compresor
k_ratio = 1.30        # relación de calores específicos cp/cv para gas natural

# dimensiones de tubería (conversión mm -> pulgadas)
do_mm = pipe_data[selected_pipe]["do_mm"]
t_mm = pipe_data[selected_pipe]["t_mm"]
cost_per_m = pipe_data[selected_pipe]["cost_m"]
di_in = (do_mm - 2 * t_mm) / 25.4   # diámetro interno [in]
do_in = do_mm / 25.4                # diámetro externo [in] (para barlow)
t_in = t_mm / 25.4                  # espesor [in]

# grado de acero
smys = steel_data[selected_steel]["smys"]
f_design = steel_data[selected_steel]["f"]

# parámetros de ruta
l_km = 400.0l_mi = l_km * 0.621371              # longitud en millas
p_in = 800.0                        # presión de recepción [psia]
p_delivery_min = 500.0              # presión mínima de entrega [psia]

# -----------------------------------------------------------------------------
# 4. CÁLCULOS HIDRÁULICOS Y DE COMPRESIÓN
# -----------------------------------------------------------------------------
l_seg_mi = l_mi / n_stations        # longitud por tramo [mi]

# término constante de la ecuación de weymouth para evitar recalcular en cada iteración
weymouth_const = 433.5 * (q_mmscfd / e_eff)**2 * l_seg_mi * gamma * t_r * z / (di_in**5.33)

# arrays para guardar perfil de presión
distances = [0.0]
pressures = [p_in]

p_start = p_in
total_hp = 0.0
t2_max_c = 0.0

for i in range(n_stations):
    # caída de presión por fricción en el tramo actual
    p_end_sq = max(p_start**2 - weymouth_const, 1.0) # evita raíces negativas
    p_end = math.sqrt(p_end_sq)
    
    # registrar punto final del tramo
    seg_len_km = (l_km / n_stations) * (i + 1)
    distances.append(seg_len_km)
    pressures.append(p_end)
    
    # cálculo de potencia por estación y temperatura de descarga
    # relación de compresión necesaria para volver a p_in
    comp_ratio = p_in / p_end if p_end < p_in else 1.0
    
    # fórmula de potencia adiabática (convertida a hp)
    # q en scfd -> ft3/s. r en ft·lbf/(lb·°r). producto en ft·lbf/s. /550 -> hp
    q_scf_per_s = q_mmscfd * 1e6 / (24 * 3600)
    r_gas = 1545.0 / (gamma * 28.97) # constante específica del gas
    hp_station = (q_scf_per_s * z * r_gas * t_r / eta_comp) * (k_ratio / (k_ratio - 1)) * ((comp_ratio)**((k_ratio - 1) / k_ratio) - 1) / 550.0
    
    total_hp += hp_station
    
    # temperatura a la salida del compresor
    t2_r = t_r * (comp_ratio)**((k_ratio - 1) / k_ratio)
    t2_c = (t2_r / 1.8) - 273.15
    t2_max_c = max(t2_max_c, t2_c)
    
    # si no es la última estación, el compresor eleva la presión de vuelta a p_in
    if i < n_stations - 1:
        distances.append(seg_len_km)        pressures.append(p_in)
        p_start = p_in
    else:
        p_start = p_end # presión final de entrega

p_delivery = p_start

# -----------------------------------------------------------------------------
# 5. CÁLCULOS ECONÓMICOS
# -----------------------------------------------------------------------------
# capex
capex_pipe = cost_per_m * l_km * 1000
capex_comp = total_hp * comp_cost_per_hp
total_capex = capex_pipe + capex_comp

# factor de recuperación de capital (crf)
crf = (interest_rate * (1 + interest_rate)**project_life) / ((1 + interest_rate)**project_life - 1) if interest_rate > 0 else 1/project_life
annualized_capex = total_capex * crf

# opex (energía anual)
# 1 hp = 0.7457 kw. horas al año = 8760
opex = total_hp * 0.7457 * 8760 * energy_cost

# tac (costo total anualizado)
tac = annualized_capex + opex

# -----------------------------------------------------------------------------
# 6. SISTEMA DE VALIDACIÓN Y ALERTAS
# -----------------------------------------------------------------------------
st.markdown('<div class="boxed-title">sistema de validación y alertas</div>', unsafe_allow_html=True)

# cálculo maop (barlow)
maop = (2 * smys * t_in * f_design) / do_in

alerts_html = ""
if p_in > maop:
    alerts_html += f'<div class="alert-err">⚠️ presión de descarga ({p_in:.0f} psia) supera el maop ({maop:.0f} psia). riesgo estructural.</div>'
else:
    alerts_html += f'<div class="alert-ok">✔️ presión de operación dentro del límite maop ({maop:.0f} psia).</div>'

if t2_max_c > 65.0:
    alerts_html += f'<div class="alert-warn">⚠️ temperatura de descarga ({t2_max_c:.1f} °c) supera el límite térmico (65 °c).</div>'
else:
    alerts_html += f'<div class="alert-ok">✔️ temperatura de descarga ({t2_max_c:.1f} °c) dentro del rango seguro (< 65 °c).</div>'

if p_delivery < p_delivery_min:
    alerts_html += f'<div class="alert-err">⚠️ presión de entrega ({p_delivery:.0f} psia) es inferior a la mínima requerida ({p_delivery_min:.0f} psia).</div>'
else:
    alerts_html += f'<div class="alert-ok">✔️ presión de entrega ({p_delivery:.0f} psia) cumple con el requisito mínimo.</div>'
st.markdown(alerts_html, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 7. VISUALIZACIÓN PRINCIPAL
# -----------------------------------------------------------------------------
# dashboard de métricas
st.markdown('<div class="boxed-title">dashboard de métricas</div>', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
col1.metric(label="costo total anualizado (tac)", value=f"${tac:,.0f}")
col2.metric(label="potencia total instalada", value=f"{total_hp:,.0f} hp")
col3.metric(label="presión final de entrega", value=f"{p_delivery:.0f} psia")

# perfil hidráulico
st.markdown('<div class="boxed-title">perfil hidráulico</div>', unsafe_allow_html=True)
fig_hyd = go.Figure()
fig_hyd.add_trace(go.Scatter(x=distances, y=pressures, mode="lines+markers", name="presión [psia]", line=dict(color="#00cc96", width=2), marker=dict(size=6)))
fig_hyd.update_layout(
    xaxis_title="distancia [km]",
    yaxis_title="presión [psia]",
    template="plotly_dark",
    paper_bgcolor="#000000",
    plot_bgcolor="#000000",
    font=dict(color="#ffffff"),
    showlegend=False,
    hovermode="x unified"
)
fig_hyd.add_shape(type="line", x0=0, y0=p_delivery_min, x1=400, y1=p_delivery_min, line=dict(color="#ff4444", width=2, dash="dash"))
fig_hyd.add_annotation(x=200, y=p_delivery_min+20, text="límite mínimo entrega (500 psia)", showarrow=False, font=dict(color="#ff8888"))
st.plotly_chart(fig_hyd, use_container_width=True)

# desglose de costos
st.markdown('<div class="boxed-title">desglose de costos</div>', unsafe_allow_html=True)
cost_labels = ["capex tubería", "capex compresores", "opex energía"]
cost_values = [capex_pipe, capex_comp, opex]
fig_cost = go.Figure(data=[go.Bar(x=cost_labels, y=cost_values, marker_color=["#636efa", "#ef553b", "#00cc96"])])
fig_cost.update_layout(
    xaxis_title="concepto",
    yaxis_title="costo anualizado [usd]",
    template="plotly_dark",
    paper_bgcolor="#000000",
    plot_bgcolor="#000000",
    font=dict(color="#ffffff")
)
st.plotly_chart(fig_cost, use_container_width=True)

# nota técnica para el estudiante
with st.expander("notas técnicas y conversiones de unidades"):
    st.markdown("""
    - **ecuación de weymouth**: constante 433.5 requiere q en mmscfd, l en millas, t en °r, d en pulgadas y p en psia.
    - **temperatura**: se convierte de k a °r multiplicando por 1.8 para compatibilidad con el sistema inglés de la hidráulica.    - **potencia**: se usa la forma adiabática estándar. 1 hp = 550 ft·lbf/s. la constante de gas r se calcula como 1545/peso molecular.
    - **maop**: fórmula de barlow `p = 2·s·t·f / d`. d usado es el diámetro externo.
    - **gráficas**: se construyen con arrays explícitos para mostrar la caída por fricción (línea recta descendente) y el salto de presión en compresores.
    """)
