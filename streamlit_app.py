import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json

# 設定頁面配置
st.set_page_config(layout="wide", page_title="T-Virus 監測系統")

# --- 1. 座標維度表 (依據您的數據校正) ---
# 強制校正座標，避免台北市等地點飄移到海面上
GEO_LOOKUP = {
    "Taipei_City": [25.0330, 121.5654],
    "Vladivostok": [43.1155, 131.8853],
    "London_City": [51.5074, -0.1278],
    "Rockfort_Island": [-67.6167, 62.8667],
    "Sao_Paulo": [-23.5505, -46.6333],
    "Marseille": [43.2965, 5.3698],
    "Vancouver": [49.2827, -123.1207],
    # ... 其餘 42 個地點會自動對應
}

# --- 2. 數據讀取與自動轉換 ---
@st.cache_data
def load_data():
    # 讀取您的數據檔案
    df = pd.read_csv('t_virus_global_outbreak_30k_cleaned.csv')
    
    # [修正點] 將您的 'date' 欄位轉換為 datetime 格式
    df['date'] = pd.to_datetime(df['date'])
    
    # 建立一個隱藏的 'month_year' 欄位，專門給時間軸滑桿使用
    df['month_year'] = df['date'].dt.strftime('%Y-%m')
    
    # 座標校正邏輯：如果維度表有定義就強制校正，否則保留原始數據
    df['latitude'] = df.apply(lambda x: GEO_LOOKUP.get(x['admin_region'], [x['latitude'], x['longitude']])[0], axis=1)
    df['longitude'] = df.apply(lambda x: GEO_LOOKUP.get(x['admin_region'], [x['latitude'], x['longitude']])[1], axis=1)
    
    return df

# 執行讀取
try:
    df = load_data()

    # --- 3. 側邊欄控制 ---
    st.sidebar.title("☣️ 病毒擴散控制面板")
    
    # 使用我們建立的 month_year 進行排序與選擇
    month_options = sorted(df['month_year'].unique())
    selected_month = st.sidebar.select_slider(
        "選擇監控月份",
        options=month_options,
        value=month_options[0]
    )

    # --- 4. 數據聚合 (篩選選定月份) ---
    filtered_df = df[df['month_year'] == selected_month]
    
    # 將數據按地區加總，準備給地球儀繪圖
    agg_data = filtered_df.groupby(['admin_region', 'country', 'latitude', 'longitude']).agg({
        'infected': 'sum',
        'zombified': 'sum',
        'deaths': 'sum'
    }).reset_index()

    # 轉換為 JSON 格式
    points_json = agg_data.to_json(orient='records')

    # --- 5. 3D 地球儀視覺化 (Globe.gl) ---
    globe_html = f"""
    <div id="globeViz"></div>
    <script src="//unpkg.com/globe.gl"></script>
    <script>
        const gData = {points_json};
        const world = Globe()
          (document.getElementById('globeViz'))
          .globeImageUrl('//unpkg.com/three-globe/example/img/earth-night.jpg')
          .pointLat('latitude')
          .pointLng('longitude')
          .pointColor(() => '#ff4b4b')
          .pointAltitude(d => Math.min(d.infected / 2000000, 0.5)) 
          .pointRadius(1.2)
          .pointLabel(d => `
            <div style="background:rgba(0,0,0,0.85);color:white;padding:10px;border-radius:5px;border:1px solid #ff4b4b;">
              <b style="color:#ff4b4b;">${{d.admin_region}}</b> (${{d.country}})<br/>
              -------------------------<br/>
              確診感染: ${{d.infected.toLocaleString()}}<br/>
              殭屍化: ${{d.zombified.toLocaleString()}}<br/>
              死亡人數: ${{d.deaths.toLocaleString()}}
            </div>
          `);
        
        world.controls().autoRotate = true;
        world.controls().autoRotateSpeed = 0.5;
    </script>
    <style> body {{ margin: 0; background: #0e1117; }} </style>
    """

    # 渲染介面
    st.title(f"T-Virus 全球爆發監測中心 ({selected_month})")
    
    # 建立兩欄佈局
    col1, col2 = st.columns([2, 1])
    
    with col1:
        components.html(globe_html, height=650)
    
    with col2:
        st.subheader("📊 地區爆發詳情")
        st.dataframe(
            agg_data[['admin_region', 'infected', 'zombified', 'deaths']],
            hide_index=True,
            use_container_width=True
        )

except Exception as e:
    st.error(f"應用程式執行錯誤: {e}")
