import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from deep_translator import GoogleTranslator
import edge_tts
import asyncio
import re
import os

# Page setup
st.set_page_config(page_title="All-in-One Voice & Transcript Studio", layout="wide")
st.title("🎙️ YouTube Transcriber, Translator & Realistic TTS Studio")

# Initialize session state to store transcripts and translations across actions
if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""
if "translated_text" not in st.session_state:
    st.session_state["translated_text"] = ""

# Supported Languages and corresponding Realistic Neural Voices (Microsoft Edge TTS)
LANGUAGE_MAP = {
    "English (India)": {"code": "en", "voices": ["en-IN-NeerjaNeural", "en-IN-PrabhatNeural"]},
    "English (US)": {"code": "en", "voices": ["en-US-AriaNeural", "en-US-GuyNeural", "en-US-ChristopherNeural"]},
    "Hindi (हिन्दी)": {"code": "hi", "voices": ["hi-IN-SwaraNeural", "hi-IN-MadhurNeural"]},
    "Tamil (தமிழ்)": {"code": "ta", "voices": ["ta-IN-PallaviNeural", "ta-IN-ValluvarNeural"]},
    "Telugu (తెలుగు)": {"code": "te", "voices": ["te-IN-ShrutiNeural", "te-IN-MohanNeural"]},
    "Bengali (বাংলা)": {"code": "bn", "voices": ["bn-IN-TanishaaNeural", "bn-IN-BashkarNeural"]},
    "Marathi (मराठी)": {"code": "mr", "voices": ["mr-IN-AarohiNeural", "mr-IN-ManoharNeural"]},
    "Gujarati (ગુજરાતી)": {"code": "gu", "voices": ["gu-IN-DhwaniNeural", "gu-IN-NiranjanNeural"]},
    "Kannada (ಕನ್ನಡ)": {"code": "kn", "voices": ["kn-IN-SapnaNeural", "kn-IN-GaganNeural"]},
    "Malayalam (മലയാളം)": {"code": "ml", "voices": ["ml-IN-SobhanaNeural", "ml-IN-MidhunNeural"]},
    "Spanish (Español)": {"code": "es", "voices": ["es-ES-ElviraNeural", "es-ES-AlvaroNeural"]},
    "French (Français)": {"code": "fr", "voices": ["fr-FR-DeniseNeural", "fr-FR-HenriNeural"]},
    "German (Deutsch)": {"code": "de", "voices": ["de-DE-KatjaNeural", "de-DE-ConradNeural"]},
    "Japanese (日本語)": {"code": "ja", "voices": ["ja-JP-NanamiNeural", "ja-JP-KeitaNeural"]},
    "Arabic (العربية)": {"code": "ar", "voices": ["ar-SA-ZariyahNeural", "ar-SA-HamedNeural"]},
}

# Helper function to extract YouTube Video ID
def extract_video_id(url):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    return match.group(1) if match else None

# Helper function to chunk long text for translation (Google Translate has a 5000 char limit per call)
def translate_long_text(text, target_lang_code):
    translator = GoogleTranslator(source="auto", target=target_lang_code)
    chunks = [text[i:i + 4000] for i in range(0, len(text), 4000)]
    translated_chunks = [translator.translate(chunk) for chunk in chunks]
    return " ".join(translated_chunks)

# Helper function to generate realistic speech via edge-tts
async def generate_speech(text, voice, output_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def run_tts(text, voice, output_file):
    asyncio.run(generate_speech(text, voice, output_file))

# Create Tabs for the 3 Core Features
tab1, tab2, tab3 = st.tabs([
    "📺 1. YouTube Transcriber", 
    "🌐 2. Script Translator & Voice", 
    "🗣️ 3. Realistic Text-to-Speech"
])

# ==================== TAB 1: YOUTUBE TRANSCRIBER ====================
with tab1:
    st.subheader("Extract Transcript from YouTube Video")
    yt_url = st.text_input("Paste YouTube Video Link:", placeholder="https://www.youtube.com/watch?v=...")
    
    if st.button("Fetch Transcript"):
        video_id = extract_video_id(yt_url)
        if not video_id:
            st.error("Invalid YouTube URL. Please check the link and try again.")
        else:
            with st.spinner("Extracting transcript..."):
                try:
                    ytt_api = YouTubeTranscriptApi()
                    # Attempt to fetch standard transcript; fallback to auto-listed languages if not English
                    transcript_list = ytt_api.list(video_id)
                    transcript_obj = next(iter(transcript_list))
                    fetched_data = transcript_obj.fetch()
                    
                    full_text = " ".join([snippet.text for snippet in fetched_data])
                    st.session_state["transcript"] = full_text
                    st.success("Transcript extracted successfully!")
                except Exception as e:
                    st.error(f"Could not retrieve transcript: {e}")

    if st.session_state["transcript"]:
        st.text_area("Extracted Transcript:", value=st.session_state["transcript"], height=250)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download Transcript (.txt)",
                data=st.session_state["transcript"],
                file_name="youtube_transcript.txt",
                mime="text/plain"
            )
        with col2:
            st.info("💡 Your transcript is automatically loaded into Tab 2 for translation!")

# ==================== TAB 2: SCRIPT TRANSLATOR & VOICE ====================
with tab2:
    st.subheader("Translate Script & Generate Translated Voice")
    
    source_script = st.text_area(
        "Script to Translate (Auto-filled from YouTube or paste your own):",
        value=st.session_state["transcript"],
        height=200
    )
    
    col_lang, col_voice = st.columns(2)
    with col_lang:
        selected_lang_label = st.selectbox("Select Target Language:", list(LANGUAGE_MAP.keys()))
        target_code = LANGUAGE_MAP[selected_lang_label]["code"]
    with col_voice:
        available_voices = LANGUAGE_MAP[selected_lang_label]["voices"]
        selected_trans_voice = st.selectbox("Select Voice for Translated Audio:", available_voices)

    if st.button("Translate Script"):
        if not source_script.strip():
            st.warning("Please enter a script or fetch a YouTube transcript first.")
        else:
            with st.spinner(f"Translating into {selected_lang_label}..."):
                try:
                    st.session_state["translated_text"] = translate_long_text(source_script, target_code)
                    st.success("Translation complete!")
                except Exception as e:
                    st.error(f"Translation error: {e}")

    if st.session_state["translated_text"]:
        st.text_area("Translated Script:", value=st.session_state["translated_text"], height=200)
        
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                label="📥 Download Translated Text (.txt)",
                data=st.session_state["translated_text"],
                file_name=f"translated_{target_code}.txt",
                mime="text/plain"
            )
            
        with dl_col2:
            if st.button("🔊 Generate Audio for Translated Script"):
                with st.spinner("Synthesizing realistic translated voice..."):
                    audio_path = "translated_voice.mp3"
                    run_tts(st.session_state["translated_text"], selected_trans_voice, audio_path)
                    
                    with open(audio_path, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format="audio/mp3")
                        st.download_button(
                            label="📥 Download Translated Voice (.mp3)",
                            data=audio_bytes,
                            file_name=f"translated_voice_{target_code}.mp3",
                            mime="audio/mp3"
                        )

# ==================== TAB 3: REALISTIC TEXT-TO-SPEECH ====================
with tab3:
    st.subheader("Standalone Realistic Text-to-Speech")
    
    custom_text = st.text_area(
        "Enter any text to convert into realistic speech:",
        placeholder="Type or paste your text here...",
        height=200
    )
    
    tts_col1, tts_col2 = st.columns(2)
    with tts_col1:
        tts_lang = st.selectbox("Select Accent / Language:", list(LANGUAGE_MAP.keys()), key="tts_lang")
    with tts_col2:
        tts_voice = st.selectbox("Select Neural Voice:", LANGUAGE_MAP[tts_lang]["voices"], key="tts_voice")
        
    if st.button("🎙️ Generate Realistic Speech"):
        if not custom_text.strip():
            st.warning("Please enter some text first.")
        else:
            with st.spinner("Generating neural audio..."):
                tts_output = "custom_tts_voice.mp3"
                run_tts(custom_text, tts_voice, tts_output)
                
                with open(tts_output, "rb") as f:
                    tts_bytes = f.read()
                    st.audio(tts_bytes, format="audio/mp3")
                    st.download_button(
                        label="📥 Download Realistic Voice (.mp3)",
                        data=tts_bytes,
                        file_name="realistic_speech.mp3",
                        mime="audio/mp3"
                    )
