import requests
import streamlit as st
import time
import openai
import google.generativeai as genai
import textwrap
import asyncio
import httpx

# Set page title and icon
st.set_page_config(page_title="ClickUp Workspace Analysis", page_icon="🚀", layout="wide")

# Retrieve API keys from Streamlit secrets
openai_api_key = st.secrets.get("OPENAI_API_KEY")
gemini_api_key = st.secrets.get("GEMINI_API_KEY")

# Configure Gemini if API key is available
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

def get_company_info(company_name):
    """
    Generates a short company profile for the given company name using Gemini (or OpenAI if available).
    """
    if not company_name:
        return "No company information provided."
    
    prompt = textwrap.dedent(f"""
        Please build a short company profile for {company_name}. The profile should include the following sections in markdown:
        - **Mission:** A brief mission statement.
        - **Key Features:** List 3-5 key features of the company.
        - **Values:** Describe the core values of the company.
        - **Target Audience:** Describe who the company primarily serves.
        - **Overall Summary:** Provide an overall summary of what the company does.
    """)
    
    try:
        if gemini_api_key:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            return response.text
        elif openai_api_key:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response["choices"][0]["message"]["content"]
        else:
            return "No AI service available for generating company profile."
    except Exception as e:
        return f"Error fetching company details: {str(e)}"

async def fetch_clickup_data(api_key, url, client):
    """
    Asynchronously fetch data from the ClickUp API using an existing client.
    """
    headers = {"Authorization": api_key}
    response = await client.get(url, headers=headers)
    return response.json() if response.status_code == 200 else {"error": response.text}

async def get_clickup_workspace_data(api_key):
    """
    Fetches real workspace data from the ClickUp API asynchronously.
    """
    if not api_key:
        return None
    async with httpx.AsyncClient() as client:
        teams_response = await fetch_clickup_data(api_key, "https://api.clickup.com/api/v2/team", client)
        teams = teams_response.get("teams", [])
        if not teams:
            return {"error": "No teams found in ClickUp workspace."}
        team_id = teams[0]["id"]
        return await fetch_workspace_details(api_key, team_id, client)

def get_ai_recommendations(use_case, company_profile, workspace_details):
    """
    Generates AI-powered recommendations based on workspace data, company profile, and use case.
    """
    workspace_summary = textwrap.dedent(f"""
        **📁 Spaces:** {workspace_details.get('spaces', 'N/A')}
        **📂 Folders:** {workspace_details.get('folders', 'N/A')}
        **🗂️ Lists:** {workspace_details.get('lists', 'N/A')}
        **📝 Total Tasks:** {workspace_details.get('total_tasks', 'N/A')}
        **✅ Completed Tasks:** {workspace_details.get('completed_tasks', 'N/A')}
        **📈 Task Completion Rate:** {workspace_details.get('completion_rate', 'N/A')}%
        **⚠️ Overdue Tasks:** {workspace_details.get('overdue_tasks', 'N/A')}
        **🔥 High Priority Tasks:** {workspace_details.get('high_priority_tasks', 'N/A')}
    """)
    
    prompt = textwrap.dedent(f"""
        Based on the following workspace data:
        {workspace_summary if workspace_summary else "(No workspace data available)"}
        
        Considering the company's use case: "{use_case}"
        And the following company profile:
        {company_profile}
        
        Please provide a detailed analysis.
        
        <h3>📈 Productivity Analysis</h3>
        Evaluate the current workspace structure and workflow. Provide insights on how to optimize productivity by leveraging the workspace metrics above and tailoring strategies to the specified use case.
        
        <h3>✅ Actionable Recommendations</h3>
        Suggest practical steps to improve efficiency and organization, addressing specific challenges highlighted by the workspace data and the unique requirements of the use case, along with considerations from the company profile.
        
        <h3>🏆 Best Practices & Tips</h3>
        Share industry-specific best practices and tips that can help maximize workflow efficiency for a company with this use case.
        
        <h3>🛠️ Useful ClickUp Templates & Resources</h3>
        Recommend relevant ClickUp templates and resources. Provide hyperlinks to useful resources on clickup.com, university.clickup.com, or help.clickup.com. Provide 5-8 links.
    """)
    
    try:
        if openai_api_key:
            client = openai.OpenAI(api_key=openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        elif gemini_api_key:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            return response.text
        else:
            return "No AI service available for generating recommendations."
    except Exception as e:
        return f"AI recommendation generation failed: {str(e)}"

st.title("🚀 ClickUp Workspace Analysis")

api_key = st.text_input("🔑 Enter ClickUp API Key (Optional):", type="password")
company_name = st.text_input("🏢 Enter Company Name (Optional):")
use_case = st.text_area("🏢 Describe your company's use case:")

if st.button("🚀 Let's Go!"):
    with st.spinner("Generating AI recommendations..."):
        recommendations = get_ai_recommendations(use_case, get_company_info(company_name), {})
    st.subheader("📌 AI Recommendations")
    st.markdown(recommendations, unsafe_allow_html=True)

st.markdown("<div style='position: fixed; bottom: 10px; left: 7px;'>A little tool made by: Yul 😊</div>", unsafe_allow_html=True)
