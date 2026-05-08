import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# 1. 頁面配置：隱藏側邊欄，強制寬版
st.set_page_config(page_title="T-Virus Surveillance", layout="wide", initial_sidebar_state="collapsed")

# 2. 核心 CSS：強制讓地球成為背景，圖表懸浮
st.markdown("""
<style>
    /* 移除 Streamlit 預設內距 */
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    
    /* 強制隱藏所有導航與底部標籤 */
    #MainMenu, footer, header {visibility: hidden;}

    /* 地球容器：固定在視窗，佔滿 100% */
    .globe-bg {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: 0;
        background-color: #000;
    }

    /* 左側面板：浮動定位 */
    .panel-left {
        position: fixed;
        top: 80px;
        left: 20px;
        width: 22%;
        z-index: 10;
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(8px);
        padding: 15px;
        border-left: 2px solid #ff0000;
    }

    /* 右側面板：浮動定位 */
    .panel-right {
        position: fixed;
        top: 80px;
        right: 20px;
        width: 22%;
        z-index: 10;
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(8px);
        padding: 15px;
        border-right: 2px solid #ff0000;
    }

    /* 時間軸：左上方 */
    .timeline-anchor {
        position: fixed;
        top: 20px;
        left: 20px;
        width: 300px;
        z-index: 20;
        background: rgba(20, 0, 0, 0.8);
        padding: 10px;
        border: 1px solid #ff0000;
    }

    /* 圖表文字顏色 */
    h3 { color: #ff0000 !important; font-size: 14px !important; letter-spacing: 2px; }
    .stMetric label { color: #888 !important; }
    .stMetric div { color: #ff0000 !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# 3. 數據加載與過濾
@st.cache_data
def get_data():
    # 確保讀取 CSV 時不會因為編碼或格式出錯
    df = pd.read_csv('t_virus_global_outbreak_30k.csv')
    df['date'] = pd.to_datetime(df['date'])
    df['month_year'] = df['date'].dt.to_period('M').astype(str)
    return df

df = get_data()
all_months = sorted(df['month_year'].unique())

# 4. 時間軸 (左上角浮動)
st.markdown('<div class="timeline-anchor">', unsafe_allow_html=True)
selected_month = st.select_slider("TIMELINE", options=all_months)
st.markdown('</div>', unsafe_allow_html=True)

filtered_df = df[df['month_year'] == selected_month]

# 5. 地球主視覺 (佔滿背景)
# 修正數據傳遞：Globe.gl 需要 JSON 陣列
# 修正無 Bar 顯示問題：改用 Points 渲染，並確保經緯度為數值
globe_points = filtered_df[['latitude', 'longitude', 'infected', 'mutants']].dropna()
globe_points['size'] = globe_points['infected'] / globe_points['infected'].max()
data_json = globe_points.to_json(orient='records')

globe_html = f"""
<div class="globe-bg" id="globeViz"></div>
<script src="//unpkg.com/globe.gl"></script>
<script>
    const gData = {data_json};
    const world = Globe()
      (document.getElementById('globeViz'))
      .globeImageUrl('//unpkg.com/three-globe/example/img/earth-dark.jpg')
      .bumpImageUrl('//unpkg.com/three-globe/example/img/earth-topology.png')
      .backgroundColor('#000000')
      .showAtmosphere(true)
      .atmosphereColor('#ff0000')
      .atmosphereDaylightAlpha(0.1)
      
      // 使用 Point 而非 Bar (參考圖2風格)
      .pointsData(gData)
      .pointLat('latitude')
      .pointLng('longitude')
      .pointColor(d => d.mutants > 100 ? '#ff0000' : '#444444')
      .pointRadius(d => Math.min(d.size * 2, 1.5))
      .pointsMerge(true)
      
      .controls().autoRotate = true;
    world.controls().autoRotateSpeed = 0.5;
</script>
"""
# 使用全螢幕高度組件
components.html(globe_html, height=1200)

# 6. 左右浮動面板 (透過 Markdown 容器包裹圖表)
# 左面板
st.markdown('<div class="panel-left">', unsafe_allow_html=True)
st.subheader("KEY METRICS")
st.metric("INFECTED", f"{filtered_df['infected'].sum():,}")
st.metric("MORTALITY", f"{(filtered_df['deaths'].sum()/filtered_df['infected'].sum()*100):.1f}%")

st.subheader("FORCE DEPLOYMENT")
fig_ut = px.bar(filtered_df.groupby('country')['ut_forces'].sum().reset_index().nlargest(5, 'ut_forces'), 
               x='ut_forces', y='country', orientation='h', template="plotly_dark")
fig_ut.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                    height=180, margin=dict(l=0,r=0,t=0,b=0), xaxis_visible=False, yaxis_title=None)
st.plotly_chart(fig_ut, use_container_width=True, config={'displayModeBar': False})
st.markdown('</div>', unsafe_allow_html=True)

# 右面板
st.markdown('<div class="panel-right">', unsafe_allow_html=True)
st.subheader("OUTBREAK TREND")
trend = df.groupby('month_year')['infected'].sum().reset_index()
fig_line = px.line(trend, x='month_year', y='infected', template="plotly_dark")
fig_line.update_traces(line_color='#ff0000')
fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                      height=180, margin=dict(l=0,r=0,t=0,b=0), xaxis_visible=False, yaxis_visible=False)
st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})

st.subheader("STRAIN ANALYSIS")
pie_data = filtered_df[['zombified', 'mutants', 'deaths']].sum()
fig_pie = px.pie(values=pie_data.values, names=pie_data.index, hole=.7, template="plotly_dark")
fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=180, showlegend=False, margin=dict(l=0,r=0,t=0,b=0))
fig_pie.update_traces(marker=dict(colors=['#444444', '#ff0000', '#222222']))
st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
st.markdown('</div>', unsafe_allow_html=True)
