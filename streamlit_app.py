import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json

# Page config
st.set_page_config(layout="wide", page_title="T-Virus Monitoring System")

# 1. Geographic Lookup Table for 49 Regions
GEO_LOOKUP = {
    "Base_Echo": [-80.0, 0.0], "Base_Omega": [-85.0, 10.0], "Rockfort_Island": [-67.6167, 62.8667],
    "Brisbane": [-27.4698, 153.0251], "Melbourne": [-37.8136, 144.9631], "Perth": [-31.9505, 115.8605], "Sydney": [-33.8688, 151.2093],
    "Amazon_Region": [-3.4653, -62.2159], "Brasilia": [-15.7975, -47.8919], "Rio_de_Janeiro": [-22.9068, -43.1729], "Sao_Paulo": [-23.5505, -46.6333],
    "Montreal": [45.5017, -73.5673], "Ottawa": [45.4215, -75.6972], "Toronto": [43.6532, -79.3832], "Vancouver": [49.2827, -123.1207],
    "Bordeaux": [44.8378, -0.5792], "Lyon": [45.764, 4.8357], "Marseille": [43.2965, 5.3698], "Paris_District": [48.8566, 2.3522],
    "Berlin": [52.52, 13.405], "Frankfurt": [50.1109, 8.6821], "Hamburg": [53.5511, 9.9937], "Munich": [48.1351, 11.582],
    "Akita_Pref": [39.7198, 140.1025], "Hokkaido": [43.0642, 141.3469], "Kyoto": [35.0116, 135.7681], "Okinawa": [26.2124, 127.6809], "Osaka": [34.6937, 135.5023], "Tokyo": [35.6895, 139.6917],
    "Moscow": [55.7558, 37.6173], "Saint_Petersburg": [59.9311, 30.3609], "Siberia_Zone": [60.0, 105.0], "Vladivostok": [43.1155, 131.8853],
    "Hualien_County": [23.9771, 121.6044], "Kaohsiung_City": [22.6273, 120.3014], "Taichung_City": [24.1477, 120.6736], "Tainan_City": [22.9997, 120.227], "Taipei_City": [25.033, 121.5654],
    "Birmingham": [52.4862, -1.8904], "Edinburgh": [55.9533, -3.1883], "London_City": [51.5074, -0.1278], "Manchester": [53.4808, -2.2426],
    "Arklay_County": [38.8333, -97.5333], "California": [36.7783, -119.4179], "Florida": [27.6648, -81.5158], "Illinois": [40.6331, -89.3985], "New_York": [40.7128, -74.006], "Raccoon_City": [38.8333, -97.5333], "Texas": [31.9686, -99.9018]
}

# 2. Data Loading & Processing
@st.cache_data
def load_data():
    df = pd.read_csv('t_virus_global_outbreak_30k_cleaned.csv')
    df['date'] = pd.to_datetime(df['date'])
    df['month_year'] = df['date'].dt.strftime('%Y-%m')
    
    # Force alignment with correct coordinates
    df['latitude'] = df['admin_region'].map(lambda x: GEO_LOOKUP.get(x, [0.0, 0.0])[0])
    df['longitude'] = df['admin_region'].map(lambda x: GEO_LOOKUP.get(x, [0.0, 0.0])[1])
    return df

df = load_data()

# 3. Main Interface (No Sidebar)
st.title(f"T-Virus Global Outbreak Monitoring Center")

# Timeline selection in the main area
month_options = sorted(df['month_year'].unique())
selected_month = st.select_slider("Timeline", options=month_options)

# 4. Data Aggregation
filtered_df = df[df['month_year'] == selected_month]
agg_data = filtered_df.groupby(['admin_region', 'country', 'latitude', 'longitude']).agg({
    'infected': 'sum',
    'zombified': 'sum',
    'deaths': 'sum'
}).reset_index()

points_json = agg_data.to_json(orient='records')

# 5. Globe.gl Visualization
globe_html = f"""
<div id="globeViz"></div>
<script src="//unpkg.com/globe.gl"></script>
<script>
    const gData = {points_json};
    
    // Scale factor for Bar height
    const maxVal = Math.max(...gData.map(d => d.infected));
    
    const world = Globe()
      (document.getElementById('globeViz'))
      .globeImageUrl('//unpkg.com/three-globe/example/img/earth-night.jpg')
      .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
      .pointsData(gData)
      .pointLat('latitude')
      .pointLng('longitude')
      .pointColor(() => '#ff0000')
      .pointAltitude(d => (d.infected / maxVal) * 0.5 + 0.01) // Ensure Bars are visible
      .pointRadius(0.8)
      .pointsTransitionDuration(500)
      .pointLabel(d => `
        <div style="background: rgba(0,0,0,0.9); color: white; padding: 10px; border-radius: 5px; font-family: sans-serif;">
          <b>${{d.admin_region}}, ${{d.country}}</b><br/>
          Infected: ${{d.infected.toLocaleString()}}<br/>
          Zombified: ${{d.zombified.toLocaleString()}}<br/>
          Deaths: ${{d.deaths.toLocaleString()}}
        </div>
      `);

    world.controls().autoRotate = true;
    world.controls().autoRotateSpeed = 0.5;
</script>
<style> body {{ margin: 0; background-color: #0e1117; }} </style>
"""

# Layout with two columns
col1, col2 = st.columns([2, 1])

with col1:
    components.html(globe_html, height=700)

with col2:
    st.subheader("Regional Outbreak Details")
    st.dataframe(
        agg_data[['admin_region', 'infected', 'zombified', 'deaths']],
        hide_index=True,
        use_container_width=True
    )
