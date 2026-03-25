import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import folium_static
from streamlit_js_eval import get_geolocation
from streamlit_mic_recorder import speech_to_text
import urllib.parse
import json

# --- FIREBASE SETUP ---
# On Streamlit Cloud, we store the JSON key in "Secrets"
if not firebase_admin._apps:
    # This looks for your Firebase JSON data in Streamlit's Secret settings
    try:
        if "firebase" in st.secrets:
            key_dict = json.loads(st.secrets["firebase"]["text"])
            cred = credentials.Certificate(key_dict)
            firebase_admin.initialize_app(cred)
        else:
            # For local testing, put your JSON file path here
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Secret missing: {e}")

db = firestore.client()

# --- APP CONFIG ---
st.set_page_config(page_title="Voice Controlled Women Safety App", layout="wide")

# --- AUTHENTICATION UI ---
st.sidebar.title("🔐 User Access")
user_email = st.sidebar.text_input("Email")
user_password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login / Register"):
    try:
        # Simple Logic: Try to find user, if not, create them (Simplified for Demo)
        user = auth.get_user_by_email(user_email)
        st.sidebar.success(f"Welcome back, {user_email}")
        st.session_state['logged_in'] = True
    except:
        # Create user if they don't exist
        auth.create_user(email=user_email, password=user_password)
        st.sidebar.success("Account Created! Please login.")

# --- MAIN APP LOGIC ---
if st.session_state.get('logged_in'):
    st.title("🛡️ Voice Controlled Women Safety App")
    
    # Load Saved Contact from Firebase
    user_ref = db.collection("users").document(user_email)
    user_data = user_ref.get().to_dict()
    saved_contact = user_data.get("contact", "") if user_data else ""

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Settings")
        new_contact = st.text_input("Emergency Contact", value=saved_contact)
        if st.button("Save Contact to Cloud"):
            user_ref.set({"contact": new_contact}, merge=True)
            st.success("Contact Saved Safely!")

        # SOS Logic (Same as before)
        loc = get_geolocation()
        if loc:
            lat, lng = loc['coords']['latitude'], loc['coords']['longitude']
            
            st.markdown("---")
            st.subheader("🎙️ Voice SOS")
            text = speech_to_text(language='en', start_prompt="⏺️ Listen", key='v_sos')
            
            if text and any(word in text.upper() for word in ["HELP", "SOS"]):
                # Function to trigger SMS (same as previous script)
                st.error("🚨 VOICE TRIGGER ACTIVATED")
                # [Trigger SMS Logic Here]

    with col2:
        if loc:
            m = folium.Map(location=[lat, lng], zoom_start=15)
            folium.Marker([lat, lng], popup="Current Location").add_to(m)
            folium_static(m)
else:
    st.info("Please login via the sidebar to access safety features.")
