import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import hashlib
import sqlite3
from datetime import datetime, timedelta
import secrets

# Database setup
def init_db():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, 
                  password_hash TEXT, 
                  email TEXT,
                  created_date TEXT,
                  last_login TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (session_id TEXT PRIMARY KEY,
                  username TEXT,
                  expiry TEXT)''')
    conn.commit()
    return conn

# Security functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, provided_password):
    return stored_hash == hash_password(provided_password)

def create_session(username):
    session_id = secrets.token_hex(16)
    expiry = (datetime.now() + timedelta(days=1)).isoformat()
    conn = init_db()
    c = conn.cursor()
    c.execute("INSERT INTO sessions VALUES (?, ?, ?)", (session_id, username, expiry))
    conn.commit()
    return session_id

def verify_session(session_id):
    if not session_id:
        return False
    conn = init_db()
    c = conn.cursor()
    c.execute("SELECT username, expiry FROM sessions WHERE session_id = ?", (session_id,))
    result = c.fetchone()
    if result:
        username, expiry = result
        if datetime.fromisoformat(expiry) > datetime.now():
            return username
    return False

# Authentication pages
def show_login_page():
    st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h2>🔐 Login to YouTube AI Summarizer</h2>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                conn = init_db()
                c = conn.cursor()
                c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
                result = c.fetchone()
                
                if result and verify_password(result[0], password):
                    session_id = create_session(username)
                    st.session_state['session_id'] = session_id
                    st.session_state['username'] = username
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.markdown("---")
        if st.button("Create New Account"):
            st.session_state['show_signup'] = True
            st.rerun()

def show_signup_page():
    st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h2>📝 Create New Account</h2>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("signup_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            email = st.text_input("Email")
            submit = st.form_submit_button("Sign Up")
            
            if submit:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                    return
                
                conn = init_db()
                c = conn.cursor()
                c.execute("SELECT username FROM users WHERE username = ?", (new_username,))
                if c.fetchone():
                    st.error("Username already exists")
                    return
                
                password_hash = hash_password(new_password)
                created_date = datetime.now().isoformat()
                
                try:
                    c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                             (new_username, password_hash, email, created_date, created_date))
                    conn.commit()
                    st.success("Account created successfully! Please login.")
                    st.session_state['show_signup'] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating account: {e}")
        
        st.markdown("---")
        if st.button("Back to Login"):
            st.session_state['show_signup'] = False
            st.rerun()

# Main app with authentication
def main():
    # Initialize session state
    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = None
    if 'show_signup' not in st.session_state:
        st.session_state['show_signup'] = False
    
    # Initialize database
    init_db()
    
    # Check authentication
    username = verify_session(st.session_state.get('session_id'))
    
    if not username:
        if st.session_state.get('show_signup', False):
            show_signup_page()
        else:
            show_login_page()
        return

    # Add logout button to sidebar
    with st.sidebar:
        if st.button("Logout"):
            st.session_state['session_id'] = None
            st.rerun()

    # Your existing app code goes here
    st.title(f"Welcome, {username}! 👋")
    # ... rest of your YouTube AI Summarizer code ...

if __name__ == "__main__":
    main()