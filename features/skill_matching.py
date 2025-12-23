import streamlit as st
import time
from pdf_cv_extraction import pdf_summary
from linkedin_scrapper import scrape_linkedin_fast
from vector_db import aggregate_skills_from_json

def app():
    st.write("### Skill Matching Interface")

    # 1. Inputs
    uploaded_file = st.file_uploader("Upload your CV (PDF)", type="pdf")
    target_position = st.text_input("Target Position", placeholder="Please write your target job position")
    region = st.text_input("Region", placeholder="Please write your target job region")
    
    if st.button("Analyze"):
        if not uploaded_file or not target_position:
            st.error("Please provide both a CV and a Target Position.")
            return

        st.info(f"Analyzing Gap for '{target_position}' role...")
        
        # 1. Extract CV
        with st.spinner("Analyzing your CV..."):
            try:
                summary_list = pdf_summary(uploaded_file)
                cv_summary = summary_list[0] if summary_list else "No summary."
            except Exception as e:
                st.error(f"Error extracting CV: {e}")
                return
        
        # 2. Guard Rail: Aggregate Market Data
        with st.spinner("Aggregating Market Data (Guard Rail)..."):
            try:
                scrape_linkedin_fast(keywords=[target_position], location=region, max_jobs=100)
                
                market_summary_text = aggregate_skills_from_json("linkedin_jobs.json")
            except Exception as e:
                st.error(f"Error getting market data: {e}")
                return
            
        # 3. Agent Logic (LLM Analysis)
        with st.spinner("Generating Gap Analysis & Roadmap..."):
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import PromptTemplate
            
            llm = ChatOpenAI(model_name="gpt-4o", temperature=0.7)
            
            prompt = PromptTemplate.from_template("""
            You are a Career Consultant Supervisor.
            
            Human Candidate Profile:
            {cv_summary}
            
            Real-Time Market Data (Most Common Jobs & Requirements for '{target_position}'):
            {market_summary_text}
            
            Task:
            1. Analyze the "Most Common Job Responsibilities" and "Top Technical Skills" demanded by the market data above.
            2. Compare with the Human Candidate's profile.
            3. Identify the Skill Gap (skills needed but missing).
            4. Create a Step-by-Step Learning Roadmap to bridge this gap.
            5. propose 2-3 Project Ideas that directly address the "Most Common Job Responsibilities" found in the data.
            6. Suggest additional ideas of project that have relevance to Candidate's job experiences.
            
            Output in Markdown format.
            """)
            
            chain = prompt | llm
            response = chain.invoke({
                "cv_summary": cv_summary,
                "market_summary_text": market_summary_text,
                "target_position": target_position
            })
            
            analysis = response.content

        # Results
        st.markdown(analysis)
