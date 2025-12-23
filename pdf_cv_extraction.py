# from google.colab import userdata # REMOVED
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from pypdf import PdfReader
import os
from dotenv import load_dotenv

load_dotenv()

def pdf_summary(PDF_FILE):
  # extract pdf

  reader = PdfReader(PDF_FILE)

  text = str() 
  for pages in reader.pages:
    page_text = pages.extract_text()
    if page_text:
      text += page_text

  # recursive
  text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", " ", ","]
  )
  texts = text_splitter.split_text(text)

  # map summarization
  map_prompt_template = PromptTemplate.from_template("""
  Summarize uploaded CV from {text} into this format:
  name: (full name)
  experience: (list of job experience, summarize into one sentence for each job position)
  skills: (list of technical skills)
  """)
  llm = ChatOpenAI(
    model_name = "gpt-4o-mini",
    temperature = 0
  )

  map_chain = map_prompt_template | llm
  summary = []

  for chunks in texts:
    respond = map_chain.invoke({"text":chunks})
    summary.append(respond.content)

  #reduce (combine semua summarized chunk)
  reduce_prompt_template = PromptTemplate.from_template("Combine the following chunk summaries into a single comprehensive summary:\n\n{summaries}")

  reduce_chain = reduce_prompt_template | llm
  reduced_summary = []

  respond = reduce_chain.invoke({"summaries":summary})
  reduced_summary.append(respond.content)
  return reduced_summary
