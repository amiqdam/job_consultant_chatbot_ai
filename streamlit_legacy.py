import streamlit as st
import pandas as pd
from pdf_cv_extraction import pdf_summary

st.title("Job Consultant Chatbot")

try:
    upload_file = st.file_uploader("Upload your CV", type="pdf")
except Exception as e:
    st.error(f"Error: {e}")

if upload_file is not None:
    st.write("Processing your CV...")
    summary = pdf_summary(upload_file)
    st.write(summary)




