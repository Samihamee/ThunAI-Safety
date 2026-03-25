import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation
from streamlit_mic_recorder import speech_to_text
from datetime import datetime
import urllib.parse
import json

# --- 1. FIREBASE INITIALIZATION ---
if not firebase_admin._apps:
    try:
        if "firebase" in st.secrets:
            # Load from Streamlit Cloud Secrets (Production)
            key_dict = json.loads(st.secrets["firebase"]["text"])
            cred = credentials.Certificate(key_dict)
            firebase_admin.initialize_app(cred)
        else:
            # Load from Local File (Development)
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error("❌ Firebase Configuration Error. Please check your Secrets or JSON file.")
        st.stop()

db = firestore.client()

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Voice Controlled Women Safety App", layout="wide", page_icon="🛡️")

# Custom Red Theme Styling
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; font-weight: bold; }
    h1 { color: #ff4b4b !important; text-align: center; font-weight: 800; }
    .stSidebar { background-color: #f8f9fa; }
    .css-10trblm { color: #ff4b4b; } 
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION SYSTEM ---
st.sidebar.title("🔐 Secure Access")
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

email = st.sidebar.text_input("Email", placeholder="user@example.com")
password = st.sidebar.text_input("Password", type="password")

col_a, col_b = st.sidebar.columns(2)

# Login Logic
if col_a.button("Login"):
    try:
        user = auth.get_user_by_email(email)
        st.session_state['logged_in'] = True
        st.session_state['user_email'] = email
        st.sidebar.success(f"Logged in as {email}")
        st.rerun()
    except Exception as e:
        st.sidebar.error("User not found. Please Sign Up.")

# Sign Up Logic
if col_b.button("Sign Up"):
    try:
        auth.create_user(email=email, password=password)
        st.sidebar.success("Account created! Now click Login.")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

# Logout Logic
if st.session_state['logged_in']:
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

# --- 4. MAIN DASHBOARD ---
if st.session_state['logged_in']:
    st.title("🛡️ Voice Controlled Women Safety App")
    
    # Fetch User Preferences from Firestore
    user_ref = db.collection("users").document(st.session_state['user_email'])
    user_doc = user_ref.get()
    saved_contact = user_doc.to_dict().get("contact", "") if user_doc.exists else ""

    tab1, tab2 = st.tabs(["🏠 Safety Dashboard", "📢 Community Forum"])

    with tab1:
        # GEOLOCATION
        loc = get_geolocation()
        
        if loc:
            lat = loc['coords']['latitude']
            lng = loc['coords']['longitude']
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("Emergency Setup")
                contact_num = st.text_input("Emergency Contact Number", value=saved_contact, max_chars=10)
                
                if st.button("💾 Save Contact to Cloud"):
                    user_ref.set({"contact": contact_num}, merge=True)
                    st.toast("Contact saved to Firebase!", icon="✅")

                st.markdown("---")
                
                # SMS PROTOCOL
                def trigger_sos(target, latitude, longitude):
                    google_maps = f"https://www.google.com/maps?q={latitude},{longitude}"
                    message = urllib.parse.quote(f"🚨 SOS! EMERGENCY! I need help. My Location: {google_maps}")
                    sms_url = f"sms:+91{target}?body={message}"
                    
                    st.error("🚨 EMERGENCY TRIGGERED")
                    st.markdown(f"""
                        <a href="{sms_url}">
                            <button style="width:100%; background-color:#ff4b4b; color:white; padding:20px; border:none; border-radius:12px; font-size:20px; cursor:pointer;">
                                CLICK TO SEND DIRECT SMS
                            </button>
                        </a>
                    """, unsafe_allow_html=True)

                # VOICE RECOGNITION
                st.subheader("🎙️ Voice Command")
                st.info("Say **'HELP'** or **'SOS'** to activate.")
                v_text = speech_to_text(language='en', start_prompt="⏺️ Start Voice Monitor", key='v_sos')

                if v_text:
                    st.write(f"Detected: *{v_text}*")
                    if any(word in v_text.upper() for word in ["HELP", "SOS", "EMERGENCY"]):
                        trigger_sos(contact_num, lat, lng)

                if st.button("🚨 MANUAL PANIC BUTTON", type="primary"):
                    trigger_sos(contact_num, lat, lng)

            with col2:
                st.subheader("Live Tracking Map")
                m = folium.Map(location=[lat, lng], zoom_start=15)
                folium.Marker([lat, lng], popup="You Are Here", icon=folium.Icon(color='red', icon='info-sign')).add_to(m)
                st_folium(m, height=400, width=700)
        else:
            st.warning("📡 Acquiring GPS Signal... Please allow location access in your browser.")

    with tab2:
        st.subheader("🗣️ Community Incident Reports")
        st.write("Report unsafe areas to help other women in your community.")
        # Future Scope: Connect this to a 'reports' collection in Firestore
        st.info("This module allows users to pin 'Unsafe Zones' on the shared community map.")

else:
    st.info("👈 Please Login or Sign Up via the sidebar to access the Safety Dashboard.")
    st.image("https://img.freepik.com/free-vector/women-protection-concept-illustration_114360-1002.jpg", width=500)
