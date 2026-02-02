import streamlit as st
import pandas as pd
import folium
from folium.plugins import Geocoder
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("🚦 Traffic Accident Severity Map – Chicago")

st.markdown("""
This interactive dashboard visualizes traffic accidents in Chicago.
Crashes are categorized by **severity** and can be filtered by **time of day**.
""")

@st.cache_data
def load_data():
    df = pd.read_csv("data/chicago_crashes.csv", low_memory=False)

    df = df.dropna(subset=["LATITUDE", "LONGITUDE"])
    df["LATITUDE"] = df["LATITUDE"].astype(float)
    df["LONGITUDE"] = df["LONGITUDE"].astype(float)
    df["CRASH_HOUR"] = df["CRASH_HOUR"].astype(int)

    return df

with st.spinner("Loading crash data and preparing map..."):
    df = load_data()

# Limit for performance
if len(df) > 20000:
    df = df.sample(20000, random_state=42)


st.sidebar.header("Filters")

time_option = st.sidebar.selectbox(
    "Select time of day:",
    ["All", "Morning (6–11 AM)", "Afternoon (12–5 PM)", "Night (6 PM–5 AM)"]
)

df_filtered = df.copy()

if time_option == "Morning (6–11 AM)":
    df_filtered = df_filtered[(df_filtered["CRASH_HOUR"] >= 6) & (df_filtered["CRASH_HOUR"] <= 11)]
elif time_option == "Afternoon (12–5 PM)":
    df_filtered = df_filtered[(df_filtered["CRASH_HOUR"] >= 12) & (df_filtered["CRASH_HOUR"] <= 17)]
elif time_option == "Night (6 PM–5 AM)":
    df_filtered = df_filtered[(df_filtered["CRASH_HOUR"] >= 18) | (df_filtered["CRASH_HOUR"] <= 5)]

# Severity classification   
def classify_severity(row):
    if row["INJURIES_FATAL"] > 0 or row["INJURIES_INCAPACITATING"] > 0:
        return "Severe"
    elif row["INJURIES_NON_INCAPACITATING"] > 0:
        return "Moderate"
    else:
        return "Minor"

df_filtered["severity"] = df_filtered.apply(classify_severity, axis=1)

minor_df = df_filtered[df_filtered["severity"] == "Minor"]
moderate_df = df_filtered[df_filtered["severity"] == "Moderate"]
severe_df = df_filtered[df_filtered["severity"] == "Severe"]

# Map initialization 
m = folium.Map(
    location=[df_filtered["LATITUDE"].mean(), df_filtered["LONGITUDE"].mean()],
    zoom_start=10,
    tiles="cartodbpositron",
    control_scale=True,
    prefer_canvas=True
)


def add_layer(data, color, radius, name):
    layer = folium.FeatureGroup(name=name, show=True)
    for _, row in data.iterrows():
        folium.CircleMarker(
            location=[row["LATITUDE"], row["LONGITUDE"]],
            radius=radius,
            color=color,
            fill=True,
            fill_opacity=0.6
        ).add_to(layer)
    layer.add_to(m)

add_layer(minor_df, "blue", 3, "Minor Crashes")
add_layer(moderate_df, "green", 4, "Moderate Crashes")
add_layer(severe_df, "red", 5, "Severe Crashes")

# Legend
legend_html = """
<div style="
position: fixed;
bottom: 40px;
left: 40px;
width: 220px;
background-color: #ffffff;
border: 2px solid #333;
border-radius: 6px;
z-index: 9999;
font-size: 14px;
padding: 12px;
color: black;
box-shadow: 2px 2px 8px rgba(0,0,0,0.3);
">
<b style="font-size:16px;">Crash Severity</b><br><br>
<span style="color:#1f77b4; font-size:18px;">●</span> Minor<br>
<span style="color:#2ca02c; font-size:18px;">●</span> Moderate<br>
<span style="color:#d62728; font-size:18px;">●</span> Severe
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))


# Controls

folium.LayerControl(collapsed=False).add_to(m)

Geocoder(
    collapsed=False,
    position="topright",
    add_marker=True
).add_to(m)

st.info("Rendering map — this may take a few seconds on first load.")
st_folium(m, width=950, height=650)

