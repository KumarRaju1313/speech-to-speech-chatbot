import streamlit as st
import os
from dotenv import load_dotenv
import speech_recognition as sr
import pyttsx3
import torch
from huggingface_hub import login
from transformers import WhisperProcessor, WhisperForConditionalGeneration, AutoTokenizer, AutoModelForCausalLM

# Load environment variables
load_dotenv()

# Get the Hugging Face token from the environment variable
hugging_face_token_id = os.getenv('HUGGING_FACE_TOKEN')

# Login to Hugging Face Hub if the token is present
if hugging_face_token_id:
    login(hugging_face_token_id)
else:
    st.error("Hugging Face token is not set. Please set it in the .env file or as a secret in the Streamlit Cloud.")

# Load models
whisper_processor = WhisperProcessor.from_pretrained("openai/whisper-base")
whisper_model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-base")

llama_tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-chat-hf")
llama_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-chat-hf")

# Initialize the speech recognition and text-to-speech engine
tts_engine = pyttsx3.init()
recognizer = sr.Recognizer()

# Initialize conversation history
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# Recognize speech from microphone
def recognize_speech_microphone():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        st.info("Listening...")
        audio = recognizer.listen(source, timeout=5)
        audio_data = audio.get_wav_data()
        inputs = whisper_processor(audio_data, return_tensors="pt", sampling_rate=16000)
        outputs = whisper_model.generate(inputs["input_ids"])
        text = whisper_processor.decode(outputs[0], skip_special_tokens=True)
        st.success(f"Recognized Text: {text}")
        return text

# Text input option
def recognize_speech_text_input():
    text = st.text_input("Enter your text:")
    return text

# Generate response using Llama 2 with conversation history
def generate_response(input_text):
    # Combine conversation history into a single context string
    conversation_context = " ".join(st.session_state.conversation_history)
    combined_input = f"{conversation_context} {input_text}"
    
    inputs = llama_tokenizer(combined_input, return_tensors="pt")
    outputs = llama_model.generate(inputs["input_ids"], max_new_tokens=50)
    response_text = llama_tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Store the new input and response in the history
    st.session_state.conversation_history.append(f"You: {input_text}")
    st.session_state.conversation_history.append(f"Bot: {response_text}")
    
    st.success(f"Generated Response: {response_text}")
    return response_text

# Speak the text using TTS engine
def speak_text(text):
    tts_engine.say(text)
    tts_engine.runAndWait()

# Streamlit app layout
st.title("Speech-to-Speech Chatbot Application")
st.write("Welcome to the Speech-to-Speech application! Select your input method below.")

# Input method selection
input_method = st.selectbox("Select input method:", ["Microphone", "Text Input"])

if st.button("Start"):
    if input_method == "Microphone":
        try:
            spoken_text = recognize_speech_microphone()
        except Exception as e:
            st.error(f"Error recognizing speech: {e}")
            spoken_text = ""
    else:
        spoken_text = recognize_speech_text_input()

    if spoken_text:
        response_text = generate_response(spoken_text)
        st.write("Response:")
        st.write(response_text)
        if st.button("Speak Response"):
            speak_text(response_text)
    else:
        st.warning("Please provide some input to generate a response.")

# Display the conversation history
st.subheader("Conversation History")
st.write("\n".join(st.session_state.conversation_history))
