import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from auth import init_db, verify_session, show_login_page, show_signup_page

# Page Configuration
st.set_page_config(
    page_title="YouTube AI Summarizer",
    page_icon="📹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #FF0000;
        color: white;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #CC0000;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .stTextInput > div > div > input {
        border-radius: 10px;
    }
    .summary-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        margin: 20px 0;
    }
    .app-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #FF0000 0%, #FF5C5C 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Load environment variables and configure API
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Improved prompt
PROMPT = """As an advanced YouTube video summarizer, please provide:
1. A concise main summary (max 3 sentences)
2. Key points (4-5 bullets)
3. Notable quotes or timestamps (if any)
4. Main takeaways

Please analyze and summarize the following transcript: """

def extract_transcript_details(youtube_video_url):
    try:
        video_id = youtube_video_url.split("=")[1]
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([entry["text"] for entry in transcript_text])
        return transcript
    except Exception as e:
        return f"Error: {e}"

def generate_gemini_content(transcript_text, prompt):
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt + transcript_text)
        return response.text
    except Exception as e:
        return f"Error: {e}"

def main_app():
    # App Header
    st.markdown("""
        <div class="app-header">
            <h1>📹 YouTube AI Summarizer</h1>
            <p>Transform long videos into concise, actionable summaries</p>
        </div>
    """, unsafe_allow_html=True)

    # Main Content
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        youtube_link = st.text_input(
            "🔗 Paste YouTube Video Link",
            placeholder="https://www.youtube.com/watch?v=example",
            help="Enter the full YouTube video URL"
        )

    # Display thumbnail and process video
    if youtube_link:
        try:
            video_id = youtube_link.split("=")[1]
            st.markdown("""
                <div style="
                    background-color: white;
                    padding: 1rem;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    margin: 1rem 0;
                ">
            """, unsafe_allow_html=True)
            st.image(
                f"http://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                use_container_width=True
            )
            st.markdown("</div>", unsafe_allow_html=True)

            # Generate Summary Button
            if st.button("🚀 Generate AI Summary", key="generate"):
                with st.spinner("🔄 Processing your video..."):
                    # Progress bar for better UX
                    progress_bar = st.progress(0)
                    for i in range(100):
                        progress_bar.progress(i + 1)
                    
                    transcript_text = extract_transcript_details(youtube_link)
                    if "Error" not in transcript_text:
                        summary = generate_gemini_content(transcript_text, PROMPT)
                        if "Error" not in summary:
                            st.markdown("""
                                <div class="summary-container">
                                    <h2>🎯 AI-Generated Summary</h2>
                                </div>
                            """, unsafe_allow_html=True)
                            st.write(summary)
                            
                            # Add sharing options
                            st.markdown("---")
                            st.markdown("📥 **Share this summary:**")
                            cols = st.columns(4)
                            with cols[0]:
                                st.button("📋 Copy")
                            with cols[1]:
                                st.button("📱 Share")
                            with cols[2]:
                                st.button("💾 Save")
                            with cols[3]:
                                st.button("📤 Export")
                        else:
                            st.error(f"⚠️ {summary}")
                    else:
                        st.error(f"⚠️ {transcript_text}")
        except IndexError:
            st.error("⚠️ Invalid YouTube URL format. Please check the URL and try again.")

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
    
    # Show login/signup or main app based on authentication
    if not username:
        if st.session_state.get('show_signup', False):
            show_signup_page()
        else:
            show_login_page()
        return
    
    # Add logout button to sidebar
    with st.sidebar:
        st.write(f"👤 Logged in as: {username}")
        if st.button("Logout"):
            st.session_state['session_id'] = None
            st.rerun()
        
        # Sidebar content
        st.markdown("### ⚙️ Settings")
        st.selectbox("Language", ["English", "Spanish", "French", "German"])
        st.slider("Summary Length", 100, 500, 250)
        st.checkbox("Include Timestamps")
        st.checkbox("Include Key Points")
        
        st.markdown("### 📊 Statistics")
        st.markdown("Videos Summarized: 1,234")
        st.markdown("Time Saved: 567 hours")
        
        st.markdown("### 💡 Tips")
        st.info("For best results, use videos with good quality captions!")

    # Run the main application
    main_app()

if __name__ == "__main__":
    main()