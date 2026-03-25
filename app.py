import streamlit as st
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import folium_static
from streamlit_js_eval import get_geolocation
from streamlit_mic_recorder import speech_to_text
from datetime import datetime
import urllib.parse
import pandas as pd
import pickle

# --- APP CONFIG ---
# Updated Title in the Browser Tab
st.set_page_config(page_title="Voice Controlled Women Safety App", layout="wide", page_icon="🛡️")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; font-weight: bold; }
    .stHeader { color: #ff4b4b; }
    h1 { color: #ff4b4b !important; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- GEOLOCATION SETUP ---
geolocator = Nominatim(user_agent="ThunAI_Voice_Safety_v5")

# --- DIRECT SMS LOGIC ---
def trigger_sos_protocol(emergency_contact, lat, lng):
    maps_link = f"https://www.google.com/maps?q={lat},{lng}"
    message_body = f"🚨 SOS! EMERGENCY! I need help. My location: {maps_link}"
    encoded_msg = urllib.parse.quote(message_body)
    
    sms_url = f"sms:+91{emergency_contact}?body={encoded_msg}"
    
    st.error("🚨 EMERGENCY PROTOCOL ACTIVATED")
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
                CLICK TO SEND DIRECT SMS NOW
            </button>
        </a>
    """, unsafe_allow_html=True)

# --- LOCATION HELPER ---
def get_address(lat, lng):
    try:
        location = geolocator.reverse((lat, lng), timeout=5)
        return location.address if location else "Location detected"
    except:
        return f"Coordinates: {lat}, {lng}"

# --- MAIN APP UI ---
# Updated Main Heading
st.title("🛡️ Voice Controlled Women Safety App")

tab1, tab2 = st.tabs(["🏠 Safety Dashboard", "💬 Community Forum"])

with tab1:
    loc = get_geolocation()
    
    if loc:
        lat = loc['coords']['latitude']
        lng = loc['coords']['longitude']
        address = get_address(lat, lng)
        
        st.success(f"📍 **Current Location:** {address}")

        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Emergency Actions")
            contact_input = st.text_input("Emergency Contact (10 digits)", placeholder="8639227063", max_chars=10)
            st.session_state['sos_contact'] = contact_input.strip()
            
            if st.button("🚨 TRIGGER SOS MANUALLY", type="primary"):
                if len(st.session_state['sos_contact']) == 10:
                    trigger_sos_protocol(st.session_state['sos_contact'], lat, lng)
                else:
                    st.warning("Please enter a valid 10-digit number.")

            st.markdown("---")
            
            st.subheader("🎙️ Voice SOS Activation")
            st.info("Say **'HELP'** or **'SOS'** to trigger the alert hands-free.")
            
            text = speech_to_text(language='en', start_prompt="⏺️ Start Listening", stop_prompt="⏹️ Stop", key='voice_sos')

            if text:
                st.write(f"Voice Detected: *{text}*")
                if any(word in text.upper() for word in ["HELP", "SOS", "EMERGENCY"]):
                    st.toast("🚨 VOICE TRIGGER DETECTED!", icon="🔥")
                    if len(st.session_state['sos_contact']) == 10:
                        trigger_sos_protocol(st.session_state['sos_contact'], lat, lng)
                    else:
                        st.error("Voice recognized, but no valid contact number is set.")

        with col2:
            st.subheader("Live Safety Map")
            m = folium.Map(location=[lat, lng], zoom_start=15, tiles="OpenStreetMap")
            folium.Marker([lat, lng], popup="You are here", icon=folium.Icon(color='red', icon='info-sign')).add_to(m)
            folium_static(m)

    else:
        st.warning("📡 Waiting for GPS signal... Please click 'Allow' in your browser.")

with tab2:
    st.subheader("🗣️ Community Safety Updates")
    if 'forum_msgs' not in st.session_state:
        st.session_state.forum_msgs = pd.DataFrame({
            'User': ["Anjali", "Admin"],
            'Message': ["Streetlights fixed near the station.", "Police patrol increased in Zone 4."],
            'Time': ["08:30 PM", "09:15 PM"]
        })
    
    st.table(st.session_state.forum_msgs)
    
    with st.expander("Post an Update"):
        u_name = st.text_input("Name")
        u_post = st.text_input("Message")
        if st.button("Post"):
            new_entry = pd.DataFrame({'User': [u_name], 'Message': [u_post], 'Time': [datetime.now().strftime("%I:%M %p")]})
            st.session_state.forum_msgs = pd.concat([st.session_state.forum_msgs, new_entry], ignore_index=True)
            st.rerun()
