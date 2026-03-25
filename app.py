import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import folium_static
from streamlit_js_eval import get_geolocation
from streamlit_mic_recorder import speech_to_text
from datetime import datetime
import urllib.parse
import pandas as pd
import json

# --- 1. FIREBASE INITIALIZATION ---
if not firebase_admin._apps:
    try:
        if "firebase" in st.secrets:
            # Load from Streamlit Cloud Secrets
            key_dict = json.loads(st.secrets["firebase"]["text"])
            cred = credentials.Certificate(key_dict)
            firebase_admin.initialize_app(cred)
        else:
            # Local Testing Only
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"⚠️ Configuration Error: {e}")

db = firestore.client()

# --- 2. APP CONFIG & STYLING ---
st.set_page_config(page_title="Voice Controlled Women Safety App", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; font-weight: bold; }
    h1 { color: #ff4b4b !important; text-align: center; }
    .stSidebar { background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION LOGIC ---
st.sidebar.title("🔐 Secure Access")
email = st.sidebar.text_input("Email")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login / Sign Up"):
    try:
        # Check if user exists
        user = auth.get_user_by_email(email)
        st.session_state['user_email'] = email
        st.session_state['logged_in'] = True
        st.sidebar.success(f"Welcome, {email}")
    except:
        # If not, create them
        try:
            auth.create_user(email=email, password=password)
            st.sidebar.info("Account created! Click Login again.")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

# --- 4. MAIN SAFETY DASHBOARD ---
if st.session_state.get('logged_in'):
    st.title("🛡️ Voice Controlled Women Safety App")
    
    # --- FETCH SAVED DATA FROM CLOUD ---
    user_ref = db.collection("users").document(st.session_state['user_email'])
    user_doc = user_ref.get()
    saved_contact = user_doc.to_dict().get("contact", "") if user_doc.exists else ""

    tab1, tab2 = st.tabs(["🏠 Safety Dashboard", "💬 Community Alerts"])

    with tab1:
        loc = get_geolocation()
        
        if loc:
            lat, lng = loc['coords']['latitude'], loc['coords']['longitude']
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("Emergency Setup")
                # Pre-fill the contact from Firebase
                contact_input = st.text_input("Saved Emergency Contact", value=saved_contact, max_chars=10)
                
                if st.button("💾 Update Contact in Cloud"):
                    user_ref.set({"contact": contact_input}, merge=True)
                    st.toast("Cloud Database Updated!", icon="☁️")

                st.markdown("---")
                
                # --- SOS TRIGGER FUNCTION ---
                def trigger_sos(target_num, latitude, longitude):
                    maps_url = f"https://www.google.com/maps?q={latitude},{longitude}"
                    msg = urllib.parse.quote(f"🚨 SOS! I am in danger. My live location: {maps_url}")
                    sms_link = f"sms:+91{target_num}?body={msg}"
                    
                    st.error("🚨 EMERGENCY MODE")
                    st.markdown(f'<a href="{sms_link}"><button style="width:100%; background-color:#ff4b4b; color:white; padding:15px; border:none; border-radius:10px; font-weight:bold; font-size:18px;">TAP TO SEND SOS SMS</button></a>', unsafe_allow_html=True)

                # --- VOICE SOS ---
                st.subheader("🎙️ Voice SOS")
                st.info("Say 'HELP' to trigger SOS.")
                voice_text = speech_to_text(language='en', start_prompt="⏺️ Mic On", key='v_sos')

                if voice_text:
                    st.write(f"Heard: *{voice_text}*")
                    if any(word in voice_text.upper() for word in ["HELP", "SOS", "EMERGENCY"]):
                        trigger_sos(contact_input, lat, lng)

                if st.button("🚨 MANUAL SOS BUTTON"):
                    trigger_sos(contact_input, lat, lng)

            with col2:
                st.subheader("Real-Time Location")
                m = folium.Map(location=[lat, lng], zoom_start=15)
                folium.Marker([lat, lng], popup="Your Location", icon=folium.Icon(color='red')).add_to(m)
                folium_static(m)
        else:
            st.warning("📡 Acquiring GPS... Please enable location.")

    with tab2:
        st.subheader("🗣️ Incident Reporting")
        # You could also save forum posts to Firebase Firestore here!
        st.write("Community updates are live.")
        # [Existing Forum Code here...]

else:
    st.info("👈 Please Login or Sign Up in the sidebar to activate the safety portal.")
