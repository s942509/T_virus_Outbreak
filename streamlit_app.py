import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components
import json

# 1. Page Configuration
st.set_page_config(page_title="T-Virus Global Surveillance", layout="wide", initial_sidebar_state="collapsed")

# 2. Advanced CSS for Overlay Layout & Red-Grey Theme
st.markdown("""
<style>
    /* Full screen background image/globe setup */
    .stApp {
        background-color: #0a0a0a !important;
        color: #d1d1d1;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Transparent Containers */
    .stMain, .block-container {
        padding: 0 !important;
        background: transparent !important;
    }

    /* Floating Panel Styling */
    [data-testid="column"] {
        background: rgba(20, 20, 20, 0.4);
        backdrop-filter: blur(5px);
        border: 0.5px solid rgba(255, 0, 0, 0.1);
        padding: 15px !important;
        border-radius: 5px;
    }

    /* Positioning the Slider at top-left */
    .slider-container {
        position: absolute;
        top: 20px;
        left: 20px;
        width: 300px;
        z-index: 1000;
        background: rgba(10, 10, 10, 0.7);
        padding: 10px;
        border: 1px solid #ff0000;
    }

    /* Typography */
    h3 {
        font-size: 14px !important;
        color: #ff0000 !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Data Processing
@st.cache_data
def load_data():
    df = pd.read_csv('t_virus_global_outbreak_30k.csv')
    df['date'] = pd.to_datetime(df['date'])
    df['month_year'] = df['date'].dt.to_period('M').astype(str)
    return df

df = load_data()
all_months = sorted(df['month_year'].unique())

# 4. Floating UI Controls (Top-Left)
with st.container():
    st.markdown('<div class="slider-container">', unsafe_allow_html=True)
    selected_month = st.select_slider("TIMELINE", options=all_months, label_visibility="visible")
    st.markdown('</div>', unsafe_allow_html=True)

filtered_df = df[df['month_year'] == selected_month]

# 5. Main Visualization: Full-Screen Globe (Underlay)
# Preparation for Globe.gl
globe_data = filtered_df[['latitude', 'longitude', 'infected', 'mutants']].copy()
# Red-Grey gradient logic
globe_data['color'] = globe_data['mutants'] / (globe_data['infected'] + 1)
json_data = globe_data.to_json(orient='records')

globe_html = f"""
<div id="globeViz" style="position: absolute; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -1;"></div>
<script src="//unpkg.com/globe.gl"></script>
<script>
    const data = {json_data};
    const world = Globe()
        (document.getElementById('globeViz'))
        .backgroundColor('#000000')
        .globeImageUrl('//unpkg.com/three-globe/example/img/earth-dark.jpg')
        .bumpImageUrl('//unpkg.com/three-globe/example/img/earth-topology.png')
        .showAtmosphere(true)
        .atmosphereColor('#ff0000')
        .atmosphereDaylightAlpha(0.1)
        
        // Point style instead of Bars (as per Ref 2)
        .pointsData(data)
        .pointLat('latitude')
        .pointLng('longitude')
        .pointColor(d => d.color > 0.05 ? '#ff0000' : '#4a4a4a')
        .pointRadius(d => Math.sqrt(d.infected) * 0.005)
        .pointsMerge(true)
        
        // Auto rotation
        .controls().autoRotate = true;
        world.controls().autoRotateSpeed = 0.3;
</script>
"""
components.html(globe_html, height=1000)

# 6. Analysis Charts (Floating Overlay)
# We use columns but with CSS to make them float/transparent
c1, _, c2 = st.columns([1, 1.5, 1])

with c1:
    st.markdown("<br><br><br>", unsafe_allow_html=True) # Offset for slider
    st.subheader("KEY METRICS")
    st.metric("INFECTED", f"{filtered_df['infected'].sum():,}")
    st.metric("MORTALITY", f"{(filtered_df['deaths'].sum()/filtered_df['infected'].sum()*100):.1f}%")
    
    st.subheader("UT DEPLOYMENT")
    fig_ut = px.bar(filtered_df.groupby('country')['ut_forces'].sum().reset_index().nlargest(5, 'ut_forces'), 
                   x='ut_forces', y='country', orientation='h',
                   template="plotly_dark", color_discrete_sequence=['#ff0000'])
    fig_ut.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                        height=200, margin=dict(l=0, r=0, t=0, b=0), xaxis_visible=False)
    st.plotly_chart(fig_ut, use_container_width=True, config={'displayModeBar': False})

with c2:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.subheader("OUTBREAK TREND")
    trend_df = df.groupby('month_year')['infected'].sum().reset_index()
    fig_line = px.line(trend_df, x='month_year', y='infected', template="plotly_dark",
                      color_discrete_sequence=['#ff0000'])
    fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                          height=200, margin=dict(l=0, r=0, t=0, b=0), yaxis_visible=False)
    st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})
    
    st.subheader("MUTATION ANALYSIS")
    pie_data = filtered_df[['zombified', 'mutants', 'deaths']].sum().reset_index()
    fig_pie = px.pie(pie_data, values=0, names='index', hole=.6,
                    template="plotly_dark", color_discrete_sequence=['#4a4a4a', '#ff0000', '#2a2a2a'])
    fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=200, showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
