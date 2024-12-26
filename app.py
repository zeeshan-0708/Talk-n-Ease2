import google.generativeai as genai
import streamlit as st
import os
from dotenv import load_dotenv
import speech_recognition as sr
import PyPDF2
from docx import Document
from PIL import Image
import pytesseract

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    raise ValueError("Gemini API key not found. Please set it in the .env file.")

# Configure Streamlit
st.set_page_config(page_title="Talk-n-Ease", page_icon="🤖")

# Initialize session state for local storage
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Define Gemini API interaction
def get_gemini_response(prompt, context=None):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        if context:
            prompt = f"{context}\n\nQuestion: {prompt}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"

# Define speech recognition
def capture_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Listening for your question...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        question = recognizer.recognize_google(audio)
        st.write(f"Question recognized: {question}")
        return question
    except sr.UnknownValueError:
        st.error("Sorry, I could not understand the audio.")
        return None
    except sr.RequestError:
        st.error("Could not request results from Google Speech Recognition service.")
        return None

# Functions to extract text from uploaded files
def extract_text_from_pdf(uploaded_file):
    text = ""
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(uploaded_file):
    text = ""
    doc = Document(uploaded_file)
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def extract_text_from_image(uploaded_file):
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    img = Image.open(uploaded_file)
    text = pytesseract.image_to_string(img)
    return text

def process_uploaded_file(uploaded_file):
    file_content = ""
    if uploaded_file.type == "application/pdf":
        file_content = extract_text_from_pdf(uploaded_file)
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        file_content = extract_text_from_docx(uploaded_file)
    elif uploaded_file.type in ["image/jpeg", "image/png", "image/jpg"]:
        file_content = extract_text_from_image(uploaded_file)
    elif uploaded_file.type == "text/plain":
        file_content = uploaded_file.read().decode("utf-8")
    return file_content

# App Header
st.title("🤖 Talk-n-Ease")

# File Upload Section
uploaded_file = st.file_uploader("Upload a file (PDF, Text, DOCX, Image):", type=["pdf", "txt", "docx", "jpg", "png", "jpeg"])
file_content = ""

if uploaded_file:
    st.write("Processing the uploaded document...")
    file_content = process_uploaded_file(uploaded_file)
    if file_content.strip():
        st.success("Document processed successfully!")
        st.write("**Extracted Content Preview:**")
        st.text_area("Document Content", value=file_content[:1000], height=300, disabled=True)
    else:
        st.error("Unable to extract content from the file. Please try a different file.")

# User Input Section
user_input = st.text_area("Ask your question based on the uploaded document:", height=100, placeholder="Type your question here...")

# Speech Recognition Button
mic_button = st.button("Start Speech Recognition")
if mic_button:
    user_input = capture_speech()

# Submit Button
submit = st.button("Submit")

# Response Generation
if submit or user_input:
    if user_input.strip() or file_content:
        with st.spinner("Generating response..."):
            st.subheader("Response:")
            prompt = user_input if user_input.strip() else file_content
            response = get_gemini_response(prompt, context=file_content)
            if response:
                # Save query and response to local storage
                st.session_state.chat_history.append({"question": prompt, "response": response})

                st.markdown(f"<div class='response-text'>{response}</div>", unsafe_allow_html=True)
            else:
                st.error("Sorry, something went wrong. Please try again later.")
    else:
        st.error("Please enter a question or upload a file to get a response.")

# Display Chat History
if st.session_state.chat_history:
    st.markdown("### Chat History")
    for chat in st.session_state.chat_history:
        st.markdown(f"**You:** {chat['question']}")
        st.markdown(f"**Gemini:** {chat['response']}")
