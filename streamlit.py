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
openai_org_id = st.secrets.get("OPENAI_ORG_ID")
gemini_api_key = st.secrets.get("GEMINI_API_KEY")

# Configure OpenAI and Gemini if API keys are available
if openai_api_key:
    openai.organization = openai_org_id
    openai.api_key = openai_api_key

if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

def get_company_info(company_name):
    """
    Generates a short company profile for the given company name using Gemini (or OpenAI if Gemini is unavailable).
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

async def fetch_paginated_data(api_key, url, client):
    """
    Fetch data from ClickUp API with pagination support.
    """
    all_data = []
    page = 0
    while True:
        response = await fetch_clickup_data(api_key, f"{url}?page={page}", client)
        if "error" in response:
            break
        items = response.get("items", response.get("tasks", response.get("spaces", [])))
        if not items:
            break
        all_data.extend(items)
        page += 1
    return all_data

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

async def fetch_workspace_details(api_key, team_id, client):
    """
    Fetches workspace details including spaces, folders, lists, and tasks asynchronously using parallel requests.
    """
    # Fetch spaces
    spaces = await fetch_paginated_data(api_key, f"https://api.clickup.com/api/v2/team/{team_id}/space", client)
    
    # Fetch folders from all spaces in parallel
    folder_tasks = [fetch_paginated_data(api_key, f"https://api.clickup.com/api/v2/space/{space['id']}/folder", client) for space in spaces]
    folders = await asyncio.gather(*folder_tasks)
    folders = [folder for sublist in folders for folder in sublist]
    
    # Fetch lists from all folders in parallel
    list_tasks = [fetch_paginated_data(api_key, f"https://api.clickup.com/api/v2/folder/{folder['id']}/list", client) for folder in folders]
    lists = await asyncio.gather(*list_tasks)
    lists = [lst for sublist in lists for lst in sublist]
    
    # Fetch tasks from all lists in parallel
    task_tasks = [fetch_paginated_data(api_key, f"https://api.clickup.com/api/v2/list/{lst['id']}/task", client) for lst in lists]
    tasks = await asyncio.gather(*task_tasks)
    tasks = [task for sublist in tasks for task in sublist]
    
    # Calculate additional metrics
    completed_tasks = sum(1 for task in tasks if task.get("status", "") == "complete")
    overdue_tasks = sum(1 for task in tasks if task.get("due_date") and int(task["due_date"]) < int(time.time() * 1000))
    high_priority_tasks = sum(1 for task in tasks if task.get("priority", "") in ["urgent", "high"])
    task_completion_rate = (completed_tasks / len(tasks) * 100) if tasks else 0
    
    return {
        "📁 Spaces": len(spaces),
        "📂 Folders": len(folders),
        "🗂️ Lists": len(lists),
        "📝 Total Tasks": len(tasks),
        "✅ Completed Tasks": completed_tasks,
        "📈 Task Completion Rate": f"{round(task_completion_rate, 2)}%",
        "⚠️ Overdue Tasks": overdue_tasks,
        "🔥 High Priority Tasks": high_priority_tasks
    }

def get_ai_recommendations(use_case, company_profile, workspace_details):
    """
    Generates AI-powered recommendations based on workspace data, company profile, and use case.
    """
    prompt = textwrap.dedent(f"""
        Based on the following workspace data:
        {workspace_details if workspace_details else "(No workspace data available)"}
        
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
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response["choices"][0]["message"]["content"]
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
    workspace_data = None
    if api_key:
        with st.spinner("Fetching workspace data..."):
            workspace_data = asyncio.run(get_clickup_workspace_data(api_key))
        if workspace_data and "error" not in workspace_data:
            st.subheader("📊 Workspace Summary")
            cols = st.columns(4)
            for idx, (key, value) in enumerate(workspace_data.items()):
                with cols[idx % 4]:
                    st.metric(label=key, value=value)
        else:
            st.error(workspace_data.get("error", "Failed to retrieve data."))
    else:
        st.info("ClickUp API Key not provided. Skipping workspace data analysis.")
    
    if company_name:
        with st.spinner("Generating company profile..."):
            company_profile = get_company_info(company_name)
    else:
        company_profile = "No company information provided."
    
    with st.spinner("Generating AI recommendations..."):
        recommendations = get_ai_recommendations(use_case, company_profile, workspace_data)
    st.subheader("📌 AI Recommendations")
    st.markdown(recommendations, unsafe_allow_html=True)

st.markdown("<div style='position: fixed; bottom: 10px; left: 7px;'>A little tool made by: Yul 😊</div>", unsafe_allow_html=True)
