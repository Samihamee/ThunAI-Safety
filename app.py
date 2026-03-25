import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
import json
import os
import urllib.parse
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation
from streamlit_mic_recorder import speech_to_text

# --- 1. FIREBASE INITIALIZATION (AUTH ONLY) ---
if not firebase_admin._apps:
    try:
        if "firebase" in st.secrets:
            # For Streamlit Cloud
            key_dict = json.loads(st.secrets["firebase"]["text"])
            cred = credentials.Certificate(key_dict)
            firebase_admin.initialize_app(cred)
        else:
            # For Local PC Testing
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error("⚠️ Firebase Auth Error. Check your Secrets or JSON file.")
        st.stop()

# --- 2. LOCAL DATABASE LOGIC ---
# This replaces Firestore to avoid billing issues
DB_FILE = "safety_db.json"

def load_local_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_local_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# --- 3. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="Voice Controlled Women Safety", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #ff4b4b; color: white; }
    h1 { color: #ff4b4b !important; text-align: center; }
    .stSidebar { background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. AUTHENTICATION SIDEBAR ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

st.sidebar.title("🔐 Secure Access")
email = st.sidebar.text_input("Email", placeholder="user@example.com")
password = st.sidebar.text_input("Password", type="password")

col_a, col_b = st.sidebar.columns(2)

if col_a.button("Login"):
    try:
        user = auth.get_user_by_email(email)
        st.session_state['logged_in'] = True
        st.session_state['user_email'] = email
        st.sidebar.success(f"Welcome, {email}")
        st.rerun()
    except:
        st.sidebar.error("User not found. Please Sign Up.")

if col_b.button("Sign Up"):
    try:
        auth.create_user(email=email, password=password)
        st.sidebar.success("Account Created! Now click Login.")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

if st.session_state['logged_in']:
    if st.sidebar.button("Log Out"):
        st.session_state['logged_in'] = False
        st.rerun()

# --- 5. MAIN APPLICATION ---
if st.session_state['logged_in']:
    st.title("🛡️ Voice Controlled Women Safety App")
    
    # Load user data from local JSON
    local_data = load_local_db()
    current_user = st.session_state['user_email']
    saved_contact = local_data.get(current_user, "")

    tab1, tab2 = st.tabs(["🏠 Safety Dashboard", "📢 Community Forum"])

    with tab1:
        loc = get_geolocation()
        
        if loc:
            lat, lng = loc['coords']['latitude'], loc['coords']['longitude']
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("Emergency Setup")
                contact_input = st.text_input("Emergency Contact Number", value=saved_contact, max_chars=10)
                
                if st.button("💾 Save Contact to Database"):
                    local_data[current_user] = contact_input
                    save_local_db(local_data)
                    st.toast("Contact saved successfully!", icon="✅")

                st.markdown("---")
                
                # SOS FUNCTION
                def trigger_sos(target, latitude, longitude):
                    maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
                    msg = urllib.parse.quote(f"🚨 SOS! I am in danger. My location: {maps_link}")
                    sms_url = f"sms:+91{target}?body={msg}"
                    
                    st.error("🚨 EMERGENCY TRIGGERED")
                    st.markdown(f"""
                        <a href="{sms_url}">
                            <button style="width:100%; background-color:#ff4b4b; color:white; padding:20px; border:none; border-radius:12px; font-size:18px; cursor:pointer;">
                                CLICK TO SEND SOS SMS
                            </button>
                        </a>
                    """, unsafe_allow_html=True)

                # VOICE CONTROL
                st.subheader("🎙️ Voice SOS")
                st.info("Say 'HELP' to trigger emergency mode.")
                v_text = speech_to_text(language='en', start_prompt="⏺️ Mic On", key='v_sos')

                if v_text:
                    st.write(f"Heard: *{v_text}*")
                    if any(word in v_text.upper() for word in ["HELP", "SOS", "EMERGENCY"]):
                        trigger_sos(contact_input, lat, lng)

                if st.button("🚨 MANUAL PANIC BUTTON"):
                    trigger_sos(contact_input, lat, lng)

            with col2:
                st.subheader("Live Tracking Map")
                m = folium.Map(location=[lat, lng], zoom_start=15)
                folium.Marker([lat, lng], popup="Current Location", icon=folium.Icon(color='red')).add_to(m)
                st_folium(m, height=400, width=600)
        else:
            st.warning("📡 Finding GPS... Please allow location access in your browser.")

    with tab2:
        st.subheader("🗣️ Community Incident Reports")
        st.write("Post alerts for other women in your area.")
        # Local Forum Logic
        forum_name = st.text_input("Your Name", value="Anonymous")
        forum_msg = st.text_area("What's happening?")
        if st.button("Post Alert"):
            st.success(f"Alert posted by {forum_name}!")
            st.info(f"Report: {forum_msg}")

else:
    st.info("👈 Please Sign Up or Login in the sidebar to access the safety features.")
    st.image("https://img.freepik.com/free-vector/women-protection-concept-illustration_114360-1002.jpg", width=400)
