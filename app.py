import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y DISEÑO (CSS)
# ==========================================
# Le decimos a Streamlit que use toda la pantalla
st.set_page_config(page_title="Gemelo Digital - Transporte de Gas", layout="wide")

# Metemos código CSS para cambiar colores y letras como nos pediste
st.markdown("""
    <style>
    /* Fondo negro para toda la página */
    .stApp {
        background-color: #000000;
        color: white;
    }
    
    /* Título principal en Arial, tamaño 20, color azul acuamarine */
    h1 {
        font-family: 'Arial', sans-serif !important;
        font-size: 20px !important;
        color: #7FFFD4 !important; /* Aquamarine */
        font-weight: bold;
    }
    
    /* Subtítulos bon24\"": {"D_ext_mm": 609.6, "espesor_mm": 17.48, "costo_m": 440}
}

grados_acero = {
    "X52": {"SMYS": 52000, "F": 0.72},
    "X60": {"SMYS": 60000, "F": 0.72}
}

# Constantes dadas por el profe y conversiones necesarias
L_km = 400
L_millas = L_km / 1.60934 # Weymouth usa millas
T_succion_C = 20
T_Rankine = (T_succion_C * 1.8) + 32 + 460.67 # Weymouth usa Rankine
gravedad_esp = 0.65
Z = 0.90
Pin_psia = 800
Pout_min_psia = 500

# Parámetros asumidos para el compresor porque no estaban todos en el PDF
eficiencia_compresor = 0.75 
k_gas = 1.3
R_gas = 53.28 # Constante de gas típica

# --- MA# 2. BASE DE DATOS TÉCNICA (Como en el PDF)
# ==========================================
# Diccionario con los datos de las tuberías
tuberias = {
    "12": {"d_ext_mm": 323.8, "esp_mm": 10.31, "costo_m": 185},
    "16": {"d_ext_mm": 406.4, "esp_mm": 12.70, "costo_m": 260},
    "20": {"d_ext_mm": 508.0, "esp_mm": 15.09, "costo_m": 350},
    "24": {"d_ext_mm": 609.6, "esp_mm": 17.48, "costo_m": 440}
}

# Diccionario con los grados de acero
grados_acero = {
    "X52": {"smys": 52000, "factor_F": 0.72},
    "X60": {"smys": 60000, "factor_F": 0.72}
}

# Constantes del problema
L_total = 400 # km
P_recepcion = 800 # psia
P_min_entrega = 500 # psia
T_succion_K = 293itos y legibles en blanco */
    h2, h3, h4 {
        font-family: 'Trebuchet MS', Helvetica, sans-serif !important;
        color: #FFFFFF !important;
    }
    
    /* Texto normal en blanco para que se lea en el fondo negro */
    p, span, label, div {
        color: #F0F0F0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Título de la app
st.title("Proyecto: Optimización y Simulación Digital de Sistemas de Transporte de Gas")

# ==========================================
# 2. BASE DE DATOS TÉCNICA (Tablas del PDF)
# ==========================================
# Usamos diccionarios simples porque es más fácil que usar Pandas avanzado
datos_tuberia = {
    "12 pulg": {"D_ext_mm": 323.8, "espesor_mm": 10.31, "costo_m": 185},
    "16 pulg": {"D_ext_mm": 406.4, "espesor_mm": 12.70, "costo_m": 260},
    "20 pulg": {"D_ext_mm": 508.0, "espesorQUETACIÓN DE LA PÁGINA ---
# Dividimos la pantalla en 2: la parte principal (col_main) y la barra derecha (col_right)
col_main, col_right = st.columns([3, 1])

# ==========================================
# PARTE DERECHA: PANEL DE CONFIGURACIÓN
# ==========================================
with col_right:
    st.markdown("### ⚙️ Panel de Configuración")
    
    st.markdown("**1. Parámetros Económicos**")
    costo_energia = st.number_input("Costo de energía (USD/kWh)", value=0.10, step=0.01)
    tasa_interes = st.number_input("Tasa de interés (%)", value=10.0, step=0.5) / 100
    anos_vida = st.number_input("Años de vida del proyecto", value=20)
    
    st.markdown("**2. Selección de Material**")
    diametro_seleccionado = st.selectbox("Diámetro Nominal (pulg)", list(tuberias.keys()), index=2) # Por defecto 20"
    grado_seleccionado = st.selectbox("Grado del Acero", list(grados_acero.keys()))
    
    .15 # Kelvin (20°C)
gravedad_esp = 0.65
Z = 0.90
E_weymouth = 1.0 # Eficiencia asumida
k_gas = 1.3 # Exponente adiabático típico para gas natural
eficiencia_comp = 0.75 # Eficiencia del compresor típica

# ==========================================
# 3. INTERFAZ: DIVISIÓN DE PANTALLA (CONTROLES A LA DERECHA)
# ==========================================
# Creamos dos columnas: una que ocupa el 75% (izquierda) y otra el 25% (derecha)
col_principal, col_derecha = st.columns([3, 1])

# --- PANEL DE CONFIGURACIÓN (DERECHA) ---
with col_derecha:
    st.markdown("### ⚙️ Panel de Configuración")
    
    st.markdown("#### 1. Parámetros Económicos")
    costo_energia = st.number_input("Costo de Energía (USD/kWh)", value=0.08, step=0.01)
    tasa_interes = st.number_input("Tasa de Interés (%)", value=10.0, step=1.0) / _mm": 15.09, "costo_m": 350},
    "24 pulg": {"D_ext_mm": 609.6, "espesor_mm": 17.48, "costo_m": 440}
}

datos_acero = {
    "X52": {"SMYS": 52000, "F": 0.72},
    "X60": {"SMYS": 60000, "F": 0.72}
}

# ==========================================
# 3. ESTRUCTURA DE LA INTERFAZ (Columnas)
# ==========================================
# Creamos dos columnas.st.markdown("**3. Variables Operativas**")
    Q_flujo = st.number_input("Flujo de gas (MMscfd)", value=500.0, step=10.0)
    num_estaciones = st.number_input("Número de estaciones de compresión", min_value=0, max_value=10, value=2, step=1)

# ==========================================
# CÁLCULOS MATEMÁTICOS (El "Gemelo Digital")
# ==========================================

# 1. Propiedades de la tubería elegida
tubo = tuberias[diametro_seleccionado]
D_ext_pulgadas = tubo["D_ext100
    vida_util = 20 # Años típicos de proyecto
    
    st.markdown("#### 2. Selección de Material")
    diametro_seleccionado = st.selectbox("Diámetro Nominal (pulg)", options=list(tuberias.keys()), index=2)
    grado_seleccionado = st.selectbox("Grado de Acero", options=list(grados_acero.keys()))
    
    st.markdown("#### 3. Variables Operativas")
    flujo_Q = st.number_input("Flujo de Gas (MMscfd)", value=500.0, step=10.0)
    num_estaciones = st.number_input("Número de Estaciones de Compresión", min_value=0, La izquierda (grande) para gráficos, la derecha (pequeña) para controles
col_principal, col_derecha = st.columns([3, 1])

# --- BARRA DESPLEGABLE LADO DERECHO ---
with col_derecha:
    st.markdown("### ⚙️ Panel de Configuración")
    _mm"] / 25.4 # Convertimos mm a pulgadas
espesor_pulgadas = tubo["espesor_mm"] / 25.4 # Convertimos mm a pulgadas
D_int_pulgadas = D_ext_pulgadas - (2 * espesor_pulgadas) # Diámetro interno real

# 2. Verificación MAOP (Barlow)
SMYS = grados_acero[ max_value=10, value=1, step=1)

# ==========================================
# 4. CÁLCULOS MATEMÁTICOS (El "Cerebro")
# ==========================================
# Obtenemos los valores elegidos por el usuario
tubo_actual = tuberias[diametro_seleccionado]
# Expander es la barrita desplegable que pediste
    with st.expander("Modificar Parámetros Aquí", expanded=True):
        
        st.markdown("**1. Parámetros Económicos**")
        costo_energia = st.number_input("Costo Energía (USD/kWh)", value=0.08, step=0.01)
        tasa_interes = st.slider("Tasa de interésgrado_seleccionado]["SMYS"]
F_diseno = grados_acero[grado_seleccionado]["F"]
# Formula de Barlow: P = (2 * SMYS * espesor) / D_ext * F
MAOP = (2 * SMYS * espesor_pulgadas / D_ext_pulgadas) * F_diseno

# 3. Hidráulica: División del gasoducto en tramos
# Si hay N estaciones, hay N+1 tramos de tubería
num_tramos = num_estaciones + 1
L_tramo_millas = L_millas / num_tramos
L_tramo_km = L_km / num_tramos

# Factor de Weymouth (E asumimos 1 por simplicidad)
E = 1.0
# Constante de la parte derecha de la ecuacion de Weymouth
termino_weymouth = 433.5 * ((Q_flujo/E)**2) * ((L_tramo_millas * gravedad_esp * T_Rankine * Z) / (D_int_pulgadas**5.33))

# Vectores para graficar
distancias_grafico = [0]
presiones_grafico = [Pin_psia]
hp_total = 0
temperatura_salida = T_succionacero_actual = grados_acero[grado_seleccionado]

# Conversiones importantes a pulgadas para las fórmulas gringas (Weymouth y Barlow)
d_ext_pulgadas = tubo_actual["d_ext_mm"] / 25.4
esp_pulgadas = tubo_actual["esp_mm"] / 25.4
# Diámetro interno en pulgadas
d_int_pulgadas = d_ext_pulgadas - (2 * esp_pulgadas)

# Dividimos la distancia según las estaciones
segmentos = num_estaciones + 1
longitud_segmento_km = L_total / segmentos

# Listas para guardar los datos de las gráficas
distancias_plot = [0]
presiones_plot = [P_recepcion]

P_actual = P_recepcion
HP_total = 0
alerta_temperatura = False
temperatura_max = 20.0

# Bucle para simular cómo cae la presión por cada tramo del tubo
for i in range(segmentos):
    # Ecuación de Weymouth (Despejando P2)
    # P1^2 - P2^2 = 433.5 * (Q/E)^2 * (L*g*T*Z) / D^5.33
    parte_derecha = 433 (%)", min_value=1, max_value=20, value=10)
        
        st.markdown("**2. Selección de Material**")
        diametro_sel = st.selectbox("Diámetro de Tubería", list(datos_tuberia.keys()))
        acero_sel = st.selectbox("Grado de_C
falla_presion = False

presion_actual = Pin_psia

for i in range(num_tramos):
    # Calculamos la presion al final del tramo usando Weymouth: P2 = sqrt(P1^2 - termino)
    P2_cuadrado = (presion_actual**2) - termino_weymouth
    
    if P2_cuadrado <= 0:
        falla_presion =.5 * ((flujo_Q/E_weymouth)**2) * ((longitud_segmento_km * gravedad_esp * T_succion_K * Z) / (d_int_pulgadas**5.33))
    
    P_final_cuadrado = (P_actual**2) - parte_derecha
    
    if P_final_cuadrado > 0:
        P_final_segmento = math.sqrt(P_final_cuadrado)
    else:
        P Acero", list(datos_acero.keys()))
        
        st.markdown("**3. Variables Operativas**")
        flujo_gas = st.slider("Flujo de gas Q (MMscfd)", 100, 1000, 500)
        num_estaciones = st.number_input("Número de estaciones de compresión (N)", min_value=0, max_value=10, value=2)

# ==========================================
# 4. CÁLCULOS MATEMÁTICOS (El "Gemelo Digital")
# ==========================================
# Constantes del problema
L_total_km = 400.0
P_in = 800.0 # psia
T_in_K = 293.15 # 20°C
gravedad_esp = 0.65
Z = 0.90
E = 1.0 # Eficiencia asumida

# Extrayendo datos seleccionados por el usuario
D_ext_mm = datos_tuberia[diametro_sel]["D_ext_mm"]
espesor_mm = datos_tuberia[diametro_sel]["espesor_mm"]
costo_tubo_m = datos_tuberia[diametro_sel]["costo_m"]
smys = datos_acero[acero_sel]["SMYS"]
factor_f = datos_acero[acero_sel]["F"]

# CONVERSIONES DE UNIDADES (Súper importante para que la fórmula no explote)
D_ext True
        presion_final_tramo = 0
    else:
        presion_final_tramo = np.sqrt(P2_cuadrado)
    
    # Agregamos al gráfico (caída de presión en el tubo)
    distancia_actual = (i+1) * L_tramo_km
    distancias_grafico.append(distancia_actual)
    presiones_grafico.append(presion_final_tramo)
    
    # Si no es el último tramo, pasamos por una estación compresora_final_segmento = 0 # Significa que la presión cayó a cero (no llega el gas)

    distancias_plot.append(longitud_segmento_km * (i + 1))
    presiones_plot.append(P_final_segmento)
    
    # Si no es el último tramo, hay una estación que sube la presión de vuelta a 800
    if i < num_estaciones:
        if que vuelve a subir a 800 psia
    if i < num_tramos - 1 and not falla_presion:
        P_in_compresor = presion_final_tramo
        P_out_compresor = Pin_psia # Asumimos que comprime de nuevo hasta los 800
        
        # Fórmula de Potencia (simplificada en unidades compatibles)
        # HP = Q * 10^6 / (24*3600*eta) * (Z*R*T1 / (k-1)) * ((Pout/Pin)^((k-1)/k) - 1)
        relacion_compresion = P_out_compresor / P_in_compresor
        potencia_factor = (relacion_compresion**((k_gas-1)/k_gas)) - 1
        hp_tramo = (Q_flujo * 1e6 / (24 * 3600 * eficiencia_compresor)) * ((Z * R_gas * T_Rankine) / (k_gas - 1)) * potencia_factor
        hp_total += hp_tramo
        
        # Cálculo de Temperatura de descarga del compresor
        T2_Rankine = T_Rankine * (relacion_compresion**((k_gas-1)/k_gas))
        T2_C = (T2_Rankine - 460.67 - 32) / 1.8
        if T2_C > temperatura_salida:
            temperatura_salida = T2_C
        
        # Agregamos el subidón de presión en la misma distancia (para el gráfico)
        distancias_grafico. P_final_segmento > 0:
            # Fórmula de Potencia (HP)
            ratio_compresion = P_recepcion / P_final_segmento
            # Constante R para el aire/gas modificado, usamos un aproximado estándar
            R_gas = 51.5 
            
            # HP fórmula del PDF adaptada
            hp_tramo = ((flujo_Q * 1e6) / (24 * 3600 * eficiencia_comp)) * ((Z * R_gas * T_succion_K) / (k_gas - 1)) * ((ratio_compresion**((k_gas-1)/k_gas)) - 1)
            HP_total += hp_tramo
            
            # Fórmula de Temperatura
            T2_K = T_succion_K * (ratio_compresion**((k_gas-1)/k_gas))
            T2_C = T2_K - 273.15
            if T2_C > temperatura_max:
                temperatura_max = T2_C
            if T2_C > 65:
                alerta_temperatura = True
                
        # Subimos la presión en la gráfica por la estación
        distancias_plot.append(longitud_segmento_km * (i + 1))
        presiones_plot.append(P_recepcion)
        P_actual = P_recepcion # Reiniciamos la presión para el siguiente tramo

presion_llegada = presiones_plot[-1]

# Validaciones de Seguridad
# Fórmula de Barlow: P_max = (2 * SMYS * espesor) / D_ext_pulg = D_ext_mm / 25.4
espesor_pulg = espesor_mm / 25.4
D_interno_pulg = D_ext_pulg - (2 * espesor_pulg)
L_total_millas = L_total_km * 0.621371
T_in_R = T_in_K * 1.8 # De Kelvin a Rankine para Weymouth

# Dividimos el tubo en segmentos dependiendo de cuántas estaciones haya
segmentos = num_estaciones + 1
L_segmento_millas = L_total_millas / segmentos
L_segmento_km = L_total_km / segmentos

# Variables para guardar resultados
presiones_distancia = [0.0]
presiones_valores = [P_in]
potencia_total_hp = 0
max_temp_out = T_in_K # Empezamos con la temp de entrada

# Calculo de Presión Máxima de Operación (Barlow)
MAOP = (2 * smys * espesor_pulg / D_ext_pulg) * factor_f

# Lógica del flujo por los segmentos
p_actual = P_in
alerta_falla_flujo = False

for i in range(segmentos):
    # Ecuación de Weymouth despejando P2
    # P1^2 - P2^2 = 433.5 * (Q/E)^2 * (L * gamma * T * Z) / D^5.33
    parte_dere * F
MAOP = (2 * acero_actual["smys"] * esp_pulgadas) / d_ext_pulgadas * acero_actual["factor_F"]
alerta_maop = P_recepcion > MAOP
alerta_entrega = presion_llegada < P_min_entrega

# Cálculos Económicos
# CAPEX: Tubería (costo por metro * 400,000 metros) + Compresores (Aprox $1500 por HP)
capex_tuberia = tubo_actual["costo_m"] * (L_total * 1000)
capex_compresores = HP_total * 1500 
CAPEX_total = capex_tuberia + capex_compresores

# Factor de Recuperación de Capital (CRF)
CRF = (tasa_interes * ((1 + tasa_interes)**vida_util)) / (((1 + tasa_interes)**vida_util) - 1)

# OPEX: Energía de los compresores (HP a kW = 0.746) * 24 horas * 365 días * costo energía
OPEX_anual = (HP_total * 0.746) * 24 * 365 * costo_energia

# TAC
TAC = (CAPEX_total * CRF) + OPEX_anual

# ==========================================
# 5. VISUALIZACIÓN PRINCIPAL (IZQUIERDA)
# ==========================================
with col_principalappend(distancia_actual)
        presiones_grafico.append(P_out_compresor)
        presion_actual = P_out_compresor
    else:
        presion_actual = presion_final_tramo

presion_final_entrega = presion_actual

# 4. Cálculo Económico
costo_tuberia_total = tubo["costo_m"] * (L_km * 1000) # $/m * metros
costo_compresores_total = hp_total * 1500 # Asumimos 1500 USD por cada HP instalado
CAPEX = costo_tuberia_total + costo_compresores_total

# CRF (Capital Recovery Factor)
CRF = (tasa_interes * (1 + tasa_interes)**anos_vida) / (((1 + tasa_interes)**anos_vida) - 1)

# OPEX (Costo de energía)
# 1 HP = 0.7457 kW, asumiendo operación 24/7 (8760 horas al año)
energia_kwh = hp_total * 0.7457 * 8760
OPEX = energia_kwh * costo_energia

TAC = (CAPEX * CRF) + OPEX

# ==========================================
# PARTE PRINCIPAL: DASHBOARD Y RESULTADOS
# ==========================================
with col_main:
    st.markdown("<h1>Proyecto: Optimización y Simulación Digital de Sistemas de Transporte de Gas</h1>", unsafe_allow_html=cha = 433.5 * ((flujo_gas/E)**2) * ((L_segmento_millas * gravedad_esp * T_in_R * Z) / (D_interno_pulg**5.33))
    
    p2_cuadrado = (p_actual**2) - parte_derecha
    
    # Si p2_cuadrado es negativo, significa que la presión llegó a cero antes de terminar
    if p2_cuadrado <= 0:
        p_llegada = 0
        alerta_falla_flujo = True
    else:
        p_llegada = math.sqrt(p2_cuadrado)
        
    presiones_distancia.append((i+1) * L_segmento_km)
    presiones_valores.append(p_llegada)
    
    # Si no es el último segmento, hay una estación de compresión que vuelve a subir la presión a P_in
    if i < segmentos - 1:
        if p_llegada > 0:
            # Fórmula de Potencia del PDF (Simplificada con unidades estándar)
            # HP = (Q*10^6 / 24*3600*eta) * (Z*R*T / k-1) * [ (Pout/Pin)^((k-1)/k) - 1 ]
            k = 1.3
            eta = 0.75 # Eficiencia compresor
            R = 0.287 # Constante de gas
            
            # Cálculo de temperatura de salida del compresor
            T_out_K = T_in_K * ((P_in / p_llegada)**((k-1)/k))
            if T_out_K > max_temp_out:
                max_temp_out = T_out_K
            
            # Cálculo de HP (lo hicimos aprox porque la profe no dio R específico)
            hp_estacion = (flujo_gas * 1000000 / (24 * 3600 * eta)) * (Z * R * T_in_K / (k-1)) * (((P_in / p_llegada)**((k-1)/k)) - 1)
            potencia_total_hp += hp_estacion
            
        p_actual = P_in
        presiones_distancia.append((i+1) * L_segmento_km)
        presiones_valores.append(p_actual)

presion:
    st.markdown("<h1>Proyecto: Optimización y Simulación Digital de Sistemas de Transporte de Gas</h1>", unsafe_allow_html=True)
    
    # --- SISTEMA DE VALIDACIÓN Y ALERTAS ---
    st.markdown("### 🚦 Sistema de Validación y Alertas")
    col_a1, col_a2, col_a3 = st.columns(3)
    
    with col_a1:
        if alerta_maop:
            st.error(f"⚠️ MAOP Excedido. MAOP={MAOP:.1f} psia")
        else:
            st.success(f"✅ MAOP Seguro (Límite: {MAOP:.1f} psia)")
            
    with col_a2:
        if alerta_temperatura:
            st.error(f"🔥 Temp Alta: {temperatura_max:.1f}°C (>65°C)")
        else:
            st.success(f"❄️ Temp Segura: {temperatura_max:.1f}°C")
            
    with col_a3:
        if alerta_entrega:
            st.error(f"❌ Entrega fallida: {presion_llegada:.1f} psia (<500)")
        elif presion_llegada == 0:True)
    st.markdown("### Dashboard Principal")
    
    # --- MÉTRICAS ---
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Costo Anualizado (TAC)", f"${TAC:,.2f}")
    with m2:
        st.metric("Potencia Instalada", f"{hp_total:,.0f} HP")
    with m3:
        st.metric("Presión Final de Entrega", f"{presion_final_entrega:,.1f} psia")
        
    st.divider()
    
    # --- C. SISTEMA DE VALIDACIÓN Y ALERTAS ---
    st.markdown("### Sistema de Validación")
    
    # 1. Verificación MAOP
    if Pin_psia > MAOP:
        st.error(f"🚨 Peligro: Presión inicial ({Pin_psia} psia) SUPERA el límite MAOP ({MAOP:.1f} psia). Cambie espesor o grado de acero.")
    else_final = presiones_valores[-1]
max_temp_C = max_temp_out - 273.15 # Pasamos a Centígrados

# --- CÁLCULOS ECONÓMICOS ---
capex_tuberia = costo_tubo_m * (L_total_km * 1000)
costo_por_hp = 1500 # Valor asumido en la industria
capex_compresores = potencia_total_hp * costo_por_hp
capex_total = capex_tuberia + capex_compresores

# Factor de Recuperación de Capital (CRF) - Asumimos n = 20 años
n_anios = 20
i_tasa = tasa_interes / 100
if i_tasa > 0:
    CRF = (i_t
            st.error("❌ El gas no llega al final (Presión 0)")
        else:
            st.success(f"✅ Entrega ok: {presion_llegada:.1f} psia")

    # --- DASHBOARD DE MÉTRICAS ---
    st.markdown("### 📊 Dashboard de Resultados")
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Costo Total Anualizado (TAC)", f"${TAC/1e6:.2f} MM")
    col_m2.metric("Potencia Total (HP)", f"{HP_total:.0f} HP")
    col_m3.metric("Presión Final", f"{presion_llegada:.1f} psia")

    # --- PERFIL HIDRÁULICO (Gráfico dinámico con Plotly) ---
    st.markdown("### 📉 Perfil Hidráulico (Presión vs Distancia)")
    
    fig_hidraulica = go.Figure()
    fig_hidraulica.add_trace(go.Scatter(x=distancias_plot:
        st.success(f"✅ Diseño seguro por MAOP (Límite: {MAOP:.1f} psia).")
        
    # 2. Verificación Térmica
    if temperatura_salida > 65:
        st.error(f"🌡️ Alerta Térmica: La temperatura de descarga supera los 65°C (Alcanzó {temperatura_salida:.1f}°C).")
    else:
        st.success(f"✅ Temperatura en rango seguro (Máxima: {temperatura_salida:.1f}°C).")
        
    # 3. Cumplimiento de Entrega
    if falla_presion:
        st.error("📉 El gasoducto se queda sin presión antes de llegar. Necesita más estaciones de compresión o mayor diámetro.")
    elif presion_final_entrega < Pout_min_psia:
        st.warning(f"⚠️ Presión de entrega insuficiente. Llegó a {presion_final_entrega:.1f} psia, mínimo requerido es {Pout_min_psia} psia.")
    else:
        st.success("✅ Cumple con la presión mínima de entrega.")

    st.divider()

    #asa * ((1 + i_tasa)**n_anios)) / (((1 + i_tasa)**n_anios) - 1)
else:
    CRF = 1/n_anios

# OP, y=presiones_plot, mode='lines+markers', 
                                        line=dict(color=' --- B. VISUALIZACIÓN PRINCIPAL (GRÁFICOS) ---
    st.markdown("### Perfil Hidráulico y Análisis Económico")
    
    graf_col1, graf_col2 = st.columns(2)
EX (Energía) - Asumimos 8000 horas de operación al año. 1 HP = 0aquamarine', width=3),
                                        marker=dict(size=8, color='white'),
                                        name    
    with graf_col1:
        # Gráfico Perfil Hidráulico usando Plotly
        df_="Perfil de Presión"))
    # Línea de la presión mínima
    fig_hidraulica.add_grafico = pd.DataFrame({
            "Distancia [km]": distancias_grafico,
            ".7457 kW
opex_energia = potencia_total_hp * 0.7457Presión [psia]": presiones_grafico
        })
        fig_presion = px.linehline(y=500, line_dash="dash", line_color="red", annotation_text="Presión Mínima * 8000 * costo_energia

TAC = (capex_total * CRF) + opex_(df_grafico, x="Distancia [km]", y="Presión [psia]", 
                              title (500 psia)")
    
    fig_hidraulica.update_layout(
        plot_bgcolor='black',
energia

# ==========================================
# 5. VISUALIZACIÓN PRINCIPAL (Lado Izquierdo)
#        paper_bgcolor='black',
        font=dict(color='white'),
        xaxis_title="Distancia [km]",
        yaxis_title="Presión [psia]",
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig_hidraulica, use_container_width=True)

    # --- DESGL="Perfil Hidráulico del Gasoducto",
                              markers=True)
        # Línea roja punteada para mostrar la presión mínima
        fig_presion.add_hline(y=Pout_min_psia, line_dash="dash", line_color="red", annotation_text="Presión Mínima (500 psia)") ==========================================
with col_principal:
    # --- SISTEMA DE VALIDACIÓN Y ALERTAS ---
    st.markdown("### 🚨 Sistema de Validación")
    alerta_col1, alerta_col2, alerta_col3 = st.columns(3)
    
    with alerta_col1:
        if P_OSE DE COSTOS (Gráfico de sectores) ---
    st.markdown("### 💰 Desglose de
        # Para que se vea bien en fondo negro
        fig_presion.update_layout(plot_bgcolor='black', paper_bgcolor='black', font_color='white')
        st.plotly_chart(fig_presin > MAOP:
            st.error(f"¡MAOP Superado! Presión={P_in} > MA Costos")
    etiquetas_costos = ['CAPEX Tubería', 'CAPEX Compresoresion, use_container_width=True)

    with graf_col2:
        # Gráfico DesOP={round(MAOP,1)}")
        else:
            st.success(f"MAOP Seguro (Max', 'OPEX Anual (Energía)']
    valores_costos = [capex_tuberia * CRF, capex_: {round(MAOP,1)} psia)")
            
    with alerta_col2:
        ifglose de Costos
        # Evaluamos el peso del CAPEX anualizado vs OPEX
        costos = { max_temp_C > 65:
            st.error(f"¡Alerta Térmicacompresores * CRF, OPEX_anual] # Comparamos todo anualizado
    
    fig_costos = go
            "Categoría": ["CAPEX Anualizado", "OPEX (Energía)"],
            "C! Temp={round(max_temp_C,1)}°C")
        else:
            st..Figure(data=[go.Pie(labels=etiquetas_costos, values=valores_costos, hole=.osto (USD)": [CAPEX * CRF, OPEX]
        }
        df_costos = pd.DataFrame(costos)
        fig_costos = px.pie(df_costos, namessuccess(f"Temp. Segura ({round(max_temp_C,1)}°C)")
            3)])
    fig_costos.update_traces(marker=dict(colors=['#1f77b4', '#
    with alerta_col3:
        if presion_final < 500 or alerta_fallaff7f0e', '#2ca02c']))
    fig_costos.update_layout(="Categoría", values="Costo (USD)", 
                            title="Desglose del TAC (CAPEX vs OPEX
        plot_bgcolor='black',
        paper_bgcolor='black',
        font=dict(color='_flujo:
            st.error(f"¡Falla en Entrega! Pf={round(presion_)",
                            color_discrete_sequence=['aquamarine', '#4da6ff'])
        fig_costos.update_layoutwhite'),
        margin=dict(l=20, r=20, t=20, bfinal,1)} psia")
        else:
            st.success(f"Entrega Cumplida ({=20)
    )
    st.plotly_chart(fig_costos, use_container_(paper_bgcolor='black', font_color='white')
        st.plotly_chart(fig_costround(presion_final,1)} psia)")

    # --- DASHBOARD DE MÉTRICAS ---
    os, use_container_width=True)
