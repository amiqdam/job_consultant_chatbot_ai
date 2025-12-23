System Design Framework
Product Requirement Document


1. Problem Definition
- Problem: 
> Jobseekers dont know which skills set that they have will fit in which job markets
> Jobseekers need to sharpshoot their improvement plan so they will have skills that relevant to job market that keep expanding
> Jobseekers having hard time to matchmaking their skills to current job opening
- User:
> Jobseekers
> People who want to improve new skillset to match current job market
- Succes Metrics:
> Jobseekers satisfied with AI consultancies 
> AI can give optimized plan to jobseekers
> AI can give which job are currently fit to their current skillset

2. Data Design
- Data Source:
> Jobstreet/Linkedin : Web Scrapping through Job section
- Labeling:
> Job name
> Position (Worldwide)
> Job description (Job desc("Role overview,What you'll do"), Qualification/Requirements, Skills, 'Pertanyaan dari Perusahaan')
- Data Constraints:
> Noise: Unfitted Job position recommended
> Limitation: Size (Unlimited option of Job portal opening)

3. Modelling Approach

4. System/Workflow Architecture
Web scraping through Job portal and save it as one file - File Embeddings - VectorDB and RAG implementation (Context Engineering) - AI Model Creation - Multi-agent Creation - Publish Prototype via Streamlit

5. Risk & Trade-off

6. Success Matrix & Validation Plan