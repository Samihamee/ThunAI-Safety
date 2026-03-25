import streamlit as st
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import folium_static
from streamlit_js_eval import get_geolocation
from datetime import datetime
import urllib.parse
import pandas as pd
import pickle

# --- APP CONFIG ---
st.set_page_config(page_title="ThunAI - Women's Safety", layout="wide", page_icon="🛡️")

# --- CUSTOM CSS FOR BETTER LOOKS ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; font-weight: bold; }
    .main { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# --- ML MODEL LOADING (OPTIONAL) ---
try:
    model = pickle.load(open("location_risk_model.pkl", "rb"))
except Exception:
    model = None

# --- GEOLOCATION SETUP (FREE) ---
# Nominatim is the free OpenStreetMap geocoder
geolocator = Nominatim(user_agent="ThunAI_Safety_System_v3")

# --- DIRECT SMS PROTOCOL ---
def trigger_sos_protocol(emergency_contact, lat, lng):
    # Standard Google Maps URL that works on all Android/iOS/PC devices
    maps_link = f"https://www.google.com/maps?q={lat},{lng}"
    
    # The message that will be sent
    message_body = f"🚨 SOS! EMERGENCY! I need help immediately. My real-time location: {maps_link}"
    
    # URL Encoding ensures symbols like ! and : don't break the link
    encoded_msg = urllib.parse.quote(message_body)
    
    # Standard 'sms:' protocol to open the native messaging app
    sms_url = f"sms:+91{emergency_contact}?body={encoded_msg}"
    
    st.error("🚨 EMERGENCY ACTION READY")
    st.markdown(f"""
        <a href="{sms_url}">
            <button style="
                width: 100%;
                background-color: #ff4b4b;
                color: white;
                padding: 20px;
                border: none;
                border-radius: 10px;
                font-size: 20px;
                font-weight: bold;
                cursor: pointer;
                box-shadow: 0px 4px 15px rgba(255, 75, 75, 0.4);">
                SEND DIRECT SMS NOW
            </button>
        </a>
    """, unsafe_allow_html=True)
    st.info("Tap the button above. Your SMS app will open with the location link already typed in.")

# --- LOCATION HELPER ---
def get_location_details(lat, lng):
    try:
        location = geolocator.reverse((lat, lng), timeout=5)
        return location.address if location else "Location detected"
    except:
        return f"Lat: {lat}, Lng: {lng}"

# --- APP UI ---
st.title("🛡️ ThunAI: Women's Safety Portal")

tab1, tab2 = st.tabs(["🏠 Safety Dashboard", "💬 Community Forum"])

with tab1:
    # This captures the browser's high-accuracy GPS coordinates
    loc = get_geolocation()
    
    if loc:
        lat = loc['coords']['latitude']
        lng = loc['coords']['longitude']
        address = get_location_details(lat, lng)
        
        st.success(f"📍 **Current Location:** {address}")

        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Emergency Actions")
            # Using a key to prevent refresh issues
            contact_raw = st.text_input("Emergency Contact Number", placeholder="e.g. 8639227063", max_chars=10, key="sos_contact")
            contact = contact_raw.strip()
            
            if st.button("🚨 TRIGGER SOS", type="primary"):
                # Strict 10-digit validation
                if contact.isdigit() and len(contact) == 10:
                    trigger_sos_protocol(contact, lat, lng)
                else:
                    st.warning("⚠️ Please enter a valid 10-digit mobile number first.")

            st.markdown("---")
            st.subheader("Quick Report")
            incident = st.selectbox("Report Concern", ["Dark Alley", "Suspicious Activity", "Harassment", "Safe Zone"])
            if st.button("Log to Safety Map"):
                st.toast(f"Reported {incident} at this location.", icon="✅")

        with col2:
            st.subheader("Live Safety Map")
            # Using OpenStreetMap (100% Free)
            m = folium.Map(location=[lat, lng], zoom_start=15, tiles="OpenStreetMap")
            folium.Marker(
                [lat, lng], 
                popup="You are here",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
            
            folium_static(m)
    else:
        st.warning("📡 Waiting for GPS signal... Please click 'Allow' in your browser pop-up.")

with tab2:
    st.subheader("🗣️ Community Safety Updates")
    if 'forum_msgs' not in st.session_state:
        st.session_state.forum_msgs = pd.DataFrame({
            'User': ["Anjali", "Admin", "Meera"],
            'Message': ["Police patrol spotted near the mall.", "CCTV installed in Lane 4.", "Streetlights are dim near the park."],
            'Time': ["08:30 PM", "09:15 PM", "10:00 PM"]
        })
    
    st.table(st.session_state.forum_msgs)
    
    with st.expander("Post a Safety Alert"):
        u_name = st.text_input("Name")
        u_post = st.text_input("What's the update?")
        if st.button("Post to Forum"):
            if u_name and u_post:
                new_entry = pd.DataFrame({'User': [u_name], 'Message': [u_post], 'Time': [datetime.now().strftime("%I:%M %p")]})
                st.session_state.forum_msgs = pd.concat([st.session_state.forum_msgs, new_entry], ignore_index=True)
                st.rerun()
            else:
                st.error("Please fill in both fields.")