import streamlit as st
import openai
import requests
import time
import google.generativeai as genai

# Set page title and icon
@@ -8,23 +10,103 @@
# Retrieve API keys from Streamlit secrets
openai_api_key = st.secrets.get("OPENAI_API_KEY")
gemini_api_key = st.secrets.get("GEMINI_API_KEY")
clickup_api_key = st.text_input("🔑 ClickUp API Key (Optional)", type="password")

# Configure OpenAI and Gemini
if openai_api_key:
openai.api_key = openai_api_key
if gemini_api_key:
genai.configure(api_key=gemini_api_key)

def get_clickup_workspace_data(api_key):
    """Fetches real workspace data from ClickUp API, including spaces, folders, lists, and tasks."""
    if not api_key:
        return None

    url = "https://api.clickup.com/api/v2/team"
    headers = {"Authorization": api_key}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            teams = response.json().get("teams", [])
            if teams:
                team_id = teams[0]["id"]
                return fetch_workspace_details(api_key, team_id)
            else:
                return {"error": "No teams found in ClickUp workspace."}
        else:
            return {"error": f"Error: {response.status_code} - {response.json()}"}
    except Exception as e:
        return {"error": f"Exception: {str(e)}"}

def fetch_workspace_details(api_key, team_id):
    """Fetches workspace details including spaces, folders, lists, and tasks."""
    headers = {"Authorization": api_key}
    
    try:
        spaces_url = f"https://api.clickup.com/api/v2/team/{team_id}/space"
        spaces_response = requests.get(spaces_url, headers=headers).json()
        spaces = spaces_response.get("spaces", [])

        space_count, folder_count, list_count, task_count, completed_tasks, overdue_tasks, high_priority_tasks = 0, 0, 0, 0, 0, 0, 0
        
        for space in spaces:
            space_id = space["id"]
            
            folders_url = f"https://api.clickup.com/api/v2/space/{space_id}/folder"
            folders_response = requests.get(folders_url, headers=headers).json()
            folders = folders_response.get("folders", [])
            folder_count += len(folders)
            
            for folder in folders:
                folder_id = folder["id"]
                
                lists_url = f"https://api.clickup.com/api/v2/folder/{folder_id}/list"
                lists_response = requests.get(lists_url, headers=headers).json()
                lists = lists_response.get("lists", [])
                list_count += len(lists)
                
                for lst in lists:
                    list_id = lst["id"]
                    
                    tasks_url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
                    tasks_response = requests.get(tasks_url, headers=headers).json()
                    tasks = tasks_response.get("tasks", [])
                    
                    task_count += len(tasks)
                    completed_tasks += sum(1 for task in tasks if task.get("status", "") == "complete")
                    overdue_tasks += sum(1 for task in tasks if task.get("due_date") and int(task["due_date"]) < int(time.time() * 1000))
                    high_priority_tasks += sum(1 for task in tasks if task.get("priority", "") in ["urgent", "high"])
        
        task_completion_rate = (completed_tasks / task_count * 100) if task_count > 0 else 0
        
        return {
            "📁 Spaces": space_count,
            "📂 Folders": folder_count,
            "🗂️ Lists": list_count,
            "📝 Total Tasks": task_count,
            "✅ Completed Tasks": completed_tasks,
            "📈 Task Completion Rate": round(task_completion_rate, 2),
            "⚠️ Overdue Tasks": overdue_tasks,
            "🔥 High Priority Tasks": high_priority_tasks
        }
    except Exception as e:
        return {"error": f"Exception: {str(e)}"}

def generate_company_profile(company_name):
"""Uses AI to generate a company profile based on the name."""
    if not company_name:
        return "No company information provided."

prompt = f"""
    Provide a brief company profile for **{company_name}** including:
    Provide a company profile for **{company_name}**, including:
   - Industry and key business areas
   - Market position and competitors
   - Challenges and opportunities
    - Any notable recent trends or company initiatives
    - Notable recent trends or initiatives

    If the company is not well-known, generate a realistic profile based on similar businesses in that industry.
    If the company is not well-known, generate a realistic profile based on similar businesses.
   """

try:
@@ -42,16 +124,17 @@ def generate_company_profile(company_name):
except Exception as e:
return f"⚠️ AI could not generate company information: {str(e)}"

    return "⚠️ No company information available."

def get_ai_recommendations(use_case, company_profile):
def get_ai_recommendations(use_case, company_profile, workspace_details):
"""Generates AI-powered recommendations using OpenAI or Gemini."""
prompt = f"""
   **📌 Use Case:** {use_case}

   **🏢 Company Profile:**
   {company_profile}

    **📊 ClickUp Workspace Details:**
    {workspace_details if workspace_details else "No ClickUp data available."}

   ### 📈 Productivity Analysis:
   Provide insights on optimizing productivity for this company and use case.

@@ -93,12 +176,22 @@ def get_ai_recommendations(use_case, company_profile):
with st.spinner("🤖 Generating company profile..."):
company_profile = generate_company_profile(company_name) if company_name else "No company info provided."

        with st.spinner("📊 Fetching ClickUp Workspace Data..."):
            workspace_details = get_clickup_workspace_data(clickup_api_key)

# Display Company Info
st.subheader("🏢 Company Information:")
st.markdown(company_profile)

        # Display ClickUp Data
        if workspace_details and "error" in workspace_details:
            st.error(f"❌ {workspace_details['error']}")
        else:
            st.subheader("📊 ClickUp Workspace Analysis:")
            st.json(workspace_details)

with st.spinner("🤖 Generating AI recommendations..."):
            ai_recommendations = get_ai_recommendations(use_case, company_profile)
            ai_recommendations = get_ai_recommendations(use_case, company_profile, workspace_details)

st.markdown(ai_recommendations, unsafe_allow_html=True)
