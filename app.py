import google.generativeai as genai
import streamlit as st
import os
from dotenv import load_dotenv
import speech_recognition as sr
import PyPDF2
from PIL import Image
import pytesseract
from io import StringIO
from db.connection import get_db_connection  # Import database connection

load_dotenv()

# API key for Google Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    raise ValueError("Gemini API key not found. Please set it in the .env file.")

# Function to interact with Gemini model
def get_gemini_response(prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"

# Function to capture speech input
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

# Function to process uploaded file and extract content
def process_uploaded_file(uploaded_file):
    file_content = ""
    if uploaded_file.type == "text/plain":
        file_content = uploaded_file.read().decode("utf-8")
    elif uploaded_file.type == "application/pdf":
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            file_content += page.extract_text()
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        from docx import Document
        doc = Document(uploaded_file)
        for para in doc.paragraphs:
            file_content += para.text + "\n"
    elif uploaded_file.type in ["image/jpeg", "image/png", "image/jpg"]:
        img = Image.open(uploaded_file)
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Path to Tesseract
        text_from_image = pytesseract.image_to_string(img)
        file_content = text_from_image
        st.image(img, caption="Uploaded Image", use_container_width=True)
        image_details = {
            "Image Type": uploaded_file.type,
            "Image Size (bytes)": len(uploaded_file.getvalue()),
            "Image Dimensions": f"{img.width}x{img.height}",
            "Extracted Text (if any)": text_from_image if text_from_image else "No text found"
        }
        st.write("**Image Details**:")
        for key, value in image_details.items():
            st.write(f"{key}: {value}")
    return file_content

# Function to log interaction in the database
def log_interaction(user_input, response):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO interactions (user_input, response) VALUES (%s, %s)",
                (user_input, response)
            )
            conn.commit()
        except Exception as e:
            print(f"Error while inserting data: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        print("Database connection failed")

# Streamlit app interface
st.set_page_config(page_title="Talk-n-Ease", page_icon="🤖")
st.title("🤖 Talk-n-Ease")

uploaded_file = st.file_uploader("Upload a file (PDF, Text, JPG, PNG, etc.):", type=["pdf", "txt", "docx", "jpg", "png", "jpeg"])
file_content = ""

if uploaded_file is not None:
    file_content = process_uploaded_file(uploaded_file)

input_container = st.container()
with input_container:
    user_input = st.text_area("Ask your question (you can also upload a file above):", height=100, placeholder="Type your question here...")

mic_button = st.button("Start Speech Recognition", key="mic_button", use_container_width=True)

if mic_button:
    user_input = capture_speech()

submit = st.button("Submit")

if submit or user_input:
    if user_input.strip() or file_content:
        with st.spinner("Generating response..."):
            st.subheader("Response:")
            prompt = user_input if user_input.strip() else file_content
            response = get_gemini_response(prompt)

            # Log interaction in the database
            log_interaction(user_input, response)

            if response:
                st.markdown(f"<div class='response-text'>{response}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='response-error'>Sorry, something went wrong. Please try again later.</div>", unsafe_allow_html=True)
    else:
        st.error("Please enter a question or upload a file to get a response.")
