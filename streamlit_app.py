import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# 1. 強制設定頁面
st.set_page_config(page_title="SURVEILLANCE", layout="wide", initial_sidebar_state="collapsed")

# 2. 徹底重構 CSS：將 Streamlit 原生容器全部透明化並鎖定位置
st.markdown("""
<style>
    /* 移除原生間距與背景 */
    .stApp { background-color: #000 !important; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    header, footer, #MainMenu { visibility: hidden; }

    /* 全螢幕背景容器 */
    .full-bg {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: -1;
    }

    /* 左側懸浮面板 */
    .floating-left {
        position: fixed;
        top: 100px;
        left: 30px;
        width: 280px;
        z-index: 99;
        background: rgba(0, 0, 0, 0.4);
        padding: 20px;
        border-left: 1px solid #ff0000;
        backdrop-filter: blur(5px);
    }

    /* 右側懸浮面板 */
    .floating-right {
        position: fixed;
        top: 100px;
        right: 30px;
        width: 280px;
        z-index: 99;
        background: rgba(0, 0, 0, 0.4);
        padding: 20px;
        border-right: 1px solid #ff0000;
        backdrop-filter: blur(5px);
    }

    /* 左上角時間滑塊 */
    .timeline-box {
        position: fixed;
        top: 25px;
        left: 30px;
        width: 320px;
        z-index: 100;
        background: rgba(10, 10, 10, 0.8);
        padding: 5px 15px;
        border: 1px solid #333;
    }

    /* 文字樣式優化 */
    h3 { color: #ff0000 !important; font-size: 0.8rem !important; letter-spacing: 3px; font-weight: 300 !important; }
    .stMetric div { color: #ff0000 !important; font-size: 1.8rem !important; }
    .stMetric label { color: #666 !important; text-transform: uppercase; font-size: 0.7rem !important; }
</style>
""", unsafe_allow_html=True)

# 3. 數據加載
@st.cache_data
def load_surveillance_data():
    df = pd.read_csv('t_virus_global_outbreak_30k.csv')
    df['date'] = pd.to_datetime(df['date'])
    df['month_year'] = df['date'].dt.to_period('M').astype(str)
    return df

df = load_surveillance_data()
months = sorted(df['month_year'].unique())

# --- 介面組件開始 ---

# A. 時間滑塊 (左上)
st.markdown('<div class="timeline-box">', unsafe_allow_html=True)
current_m = st.select_slider("TIMELINE", options=months, label_visibility="collapsed")
st.markdown(f'<p style="color:#ff0000; font-size:0.7rem; margin:0;">PERIOD: {current_m}</p></div>', unsafe_allow_html=True)

filtered = df[df['month_year'] == current_m]

# B. 地球背景 (填滿整個視窗)
# 確保資料格式正確：排除 NaN 並限制點的數量提升效能
globe_df = filtered[['latitude', 'longitude', 'infected']].dropna().sample(n=min(len(filtered), 2000))
data_json = globe_df.to_json(orient='records')

globe_js = f"""
<div id="globeViz" class="full-bg"></div>
<script src="//unpkg.com/globe.gl"></script>
<script>
    const world = Globe()
      (document.getElementById('globeViz'))
      .globeImageUrl('//unpkg.com/three-globe/example/img/earth-dark.jpg')
      .backgroundColor('#000000')
      .showAtmosphere(true)
      .atmosphereColor('#ff0000')
      .pointsData({data_json})
      .pointLat('latitude')
      .pointLng('longitude')
      .pointColor(() => '#ff0000')
      .pointRadius(0.2)
      .pointAltitude(0.01)
      .pointsMerge(true);
    
    world.controls().autoRotate = true;
    world.controls().autoRotateSpeed = 0.5;
    world.pointLabel(d => `INFECTED: ${{d.infected}}`);
</script>
<style>body {{ margin: 0; }}</style>
"""
components.html(globe_js, height=2000) # 給予足夠高度但讓 CSS 控制固定定位

# C. 左側面板
st.markdown('<div class="floating-left">', unsafe_allow_html=True)
st.subheader("KEY METRICS")
st.metric("INFECTED", f"{filtered['infected'].sum():,}")
st.metric("MORTALITY", f"{(filtered['deaths'].sum()/filtered['infected'].sum()*100):.1f}%")

st.subheader("DEPLOYMENT")
# 強制灰色與紅色的簡約圖表
fig_bar = px.bar(filtered.groupby('country')['ut_forces'].sum().reset_index().nlargest(5, 'ut_forces'), 
                 x='ut_forces', y='country', orientation='h', template="plotly_dark")
fig_bar.update_traces(marker_color='#ff0000')
fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                     height=150, margin=dict(l=0,r=0,t=0,b=0), xaxis_visible=False, yaxis_title=None)
st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
st.markdown('</div>', unsafe_allow_html=True)

# D. 右側面板
st.markdown('<div class="floating-right">', unsafe_allow_html=True)
st.subheader("TREND")
hist = df.groupby('month_year')['infected'].sum().reset_index()
fig_line = px.line(hist, x='month_year', y='infected', template="plotly_dark")
fig_line.update_traces(line_color='#ff0000', line_width=1)
fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                      height=150, margin=dict(l=0,r=0,t=0,b=0), xaxis_visible=False, yaxis_visible=False)
st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})

st.subheader("STRAIN")
pie_val = filtered[['zombified', 'mutants', 'deaths']].sum()
fig_pie = px.pie(values=pie_val.values, names=pie_val.index, hole=.8, template="plotly_dark")
fig_pie.update_traces(marker=dict(colors=['#333', '#ff0000', '#111']), textinfo='none')
fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=150, showlegend=False, margin=dict(l=0,r=0,t=0,b=0))
st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
st.markdown('</div>', unsafe_allow_html=True)
