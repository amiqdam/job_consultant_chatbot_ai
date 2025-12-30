import streamlit as st
import time
from dotenv import load_dotenv

load_dotenv()

from pdf_cv_extraction import pdf_summary
from linkedin_scrapper import scrape_linkedin_fast
from vector_db import ingest_jobs_from_file, retrieve_qdrant
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

# Page config
st.set_page_config(page_title="Job Consultant AI", layout="wide")

# Initialize session state
if "cv_analyzed" not in st.session_state:
    st.session_state.cv_analyzed = False
if "cv_summary" not in st.session_state:
    st.session_state.cv_summary = ""
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "target_position" not in st.session_state:
    st.session_state.target_position = ""
if "market_summary" not in st.session_state:
    st.session_state.market_summary = ""

# Header
st.markdown("""
<div style="border: 2px solid #4a90e2; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 20px;">
<h3 style="color: #000; margin: 0;">Job Consultation AI</h3>
</div>
""", unsafe_allow_html=True)

# Main content
st.write("### CV Analysis & Career Consultation")

# Step 1: CV Upload and Analysis
st.write("#### Step 1: Upload and Analyze Your CV")

uploaded_file = st.file_uploader("Upload your CV (PDF)", type="pdf", key="cv_uploader")
target_position = st.text_input("Target Position", placeholder="e.g., Data Scientist, Software Engineer", key="position_input")
region = st.text_input("Region", placeholder="e.g., Indonesia, Singapore", value="Indonesia", key="region_input")

if st.button("Analyze CV", type="primary"):
    if not uploaded_file or not target_position:
        st.error("Please provide both a CV and a Target Position.")
    else:
        st.session_state.target_position = target_position
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 1. Extract CV
        status_text.text("📖 Analyzing your CV...")
        progress_bar.progress(25)
        try:
            summary_list = pdf_summary(uploaded_file)
            st.session_state.cv_summary = summary_list[0] if summary_list else "No summary."
        except Exception as e:
            st.error(f"❌ Error extracting CV: {e}")
            st.stop()
        
        # 2. Scrape Market Data
        status_text.text("🌐 Gathering market data from LinkedIn...")
        progress_bar.progress(50)
        try:
            scrape_linkedin_fast(keywords=[target_position], location=region, max_jobs=100)
            
            # RAG Ingestion
            status_text.text("💾 Updating Knowledge Base...")
            ingest_jobs_from_file("linkedin_jobs.json")
            
            # RAG Retrieval
            status_text.text("🔍 Retrieving relevant insights...")
            retrieved_docs = retrieve_qdrant(target_position, k=5)
            
            # Format for LLM
            market_summary = ""
            if retrieved_docs:
                for doc in retrieved_docs:
                    market_summary += f"Job Title: {doc.metadata['title']}\n"
                    market_summary += f"Company: {doc.metadata['company']}\n"
                    industry = doc.metadata.get('industry', 'Unknown')
                    if industry and industry != 'Unknown':
                        market_summary += f"Industry: {industry}\n"
                    market_summary += f"Content: {doc.page_content}\n\n"
            else:
                market_summary = "No relevant market data found."
            
            st.session_state.market_summary = market_summary
        except Exception as e:
            st.error(f"❌ Error getting market data: {e}")
            st.stop()
        
        # 3. Generate Analysis
        status_text.text("🤖 Generating gap analysis & roadmap...")
        progress_bar.progress(75)
        
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
        5. Propose 2-3 Project Ideas that directly address the "Most Common Job Responsibilities" found in the data.
        6. Suggest additional ideas of project that have relevance to Candidate's job experiences.
        
        Output in Markdown format with clear sections.
        """)
        
        chain = prompt | llm
        response = chain.invoke({
            "cv_summary": st.session_state.cv_summary,
            "market_summary_text": st.session_state.market_summary,
            "target_position": target_position
        })
        
        st.session_state.analysis_result = response.content
        st.session_state.cv_analyzed = True
        
        progress_bar.progress(100)
        status_text.text("✅ Analysis complete!")
        time.sleep(1)
        status_text.empty()
        progress_bar.empty()

# Display Analysis Results
if st.session_state.cv_analyzed:
    st.write("---")
    st.write("#### Analysis Results")
    
    with st.expander("Your CV Summary", expanded=False):
        st.write(st.session_state.cv_summary)
    
    with st.expander("Gap Analysis & Learning Roadmap", expanded=True):
        st.markdown(st.session_state.analysis_result)
    
    # Step 2: Interactive Chatbot
    st.write("---")
    st.write("#### Continue Discussion with AI Career Consultant")
    st.write("Ask questions about your career path, skill development, or get personalized advice!")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if isinstance(message, HumanMessage):
                with st.chat_message("user"):
                    st.write(message.content)
            elif isinstance(message, AIMessage):
                with st.chat_message("assistant"):
                    st.write(message.content)
    
    # Chat input
    user_question = st.chat_input("Ask me anything about your career development...")
    
    if user_question:
        # Add user message to history
        st.session_state.chat_history.append(HumanMessage(content=user_question))
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_question)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                llm = ChatOpenAI(model_name="gpt-4o", temperature=0.1)
                
                # Create context-aware prompt
                chat_prompt = PromptTemplate.from_template("""
                You are an expert Career Consultant AI. You have already analyzed the candidate's CV and provided a gap analysis.
                
                Context:
                - Candidate's CV Summary: {cv_summary}
                - Target Position: {target_position}
                - Previous Analysis: {analysis_result}
                - Market Data Summary: {market_summary}
                
                Chat History:
                {chat_history}
                
                User Question: {user_question}
                
                Provide a helpful, personalized response based on the candidate's profile and the analysis you've already done.
                Be conversational, supportive, and actionable in your advice.
                """)
                
                # Format chat history
                chat_history_text = "\n".join([
                    f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}"
                    for msg in st.session_state.chat_history[:-1]  # Exclude the current question
                ])
                
                chain = chat_prompt | llm
                response = chain.invoke({
                    "cv_summary": st.session_state.cv_summary,
                    "target_position": st.session_state.target_position,
                    "analysis_result": st.session_state.analysis_result,
                    "market_summary": st.session_state.market_summary,
                    "chat_history": chat_history_text if chat_history_text else "No previous conversation",
                    "user_question": user_question
                })
                
                ai_response = response.content
                st.write(ai_response)
                
                # Add AI response to history
                st.session_state.chat_history.append(AIMessage(content=ai_response))
    
    # Reset button
    st.write("---")
    if st.button("Start New Analysis"):
        st.session_state.cv_analyzed = False
        st.session_state.cv_summary = ""
        st.session_state.analysis_result = ""
        st.session_state.chat_history = []
        st.session_state.target_position = ""
        st.session_state.market_summary = ""
        st.rerun()

# Footer
st.write("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9em;">
    <p>Powered by OpenAI GPT-4 | Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)
