import requests
import streamlit as st
import time
import openai
import google.generativeai as genai
from bs4 import BeautifulSoup

# Set page title and icon
st.set_page_config(page_title="ClickUp Workspace Analyzer", page_icon="🚀", layout="wide")

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
    """Fetches basic company information from the web by searching about the company."""
    if not company_name:
        return "No company information provided."
    search_url = f"https://www.google.com/search?q={company_name.replace(' ', '+')}+company+profile"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        description = ""
        # Attempt to extract a descriptive snippet from the search results.
        for tag in soup.find_all("span"):
            text = tag.get_text()
            if "is a" in text or "provides" in text or "specializes in" in text:
                description = text
                break
        return description if description else "No detailed company info found."
    except Exception as e:
        return f"Error fetching company details: {str(e)}"

def get_clickup_workspace_data(api_key):
    """Fetches real workspace data from ClickUp API."""
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
        
        space_count = len(spaces)
        folder_count, list_count, task_count = 0, 0, 0
        completed_tasks, overdue_tasks, high_priority_tasks = 0, 0, 0
        
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
            "📈 Task Completion Rate": f"{round(task_completion_rate, 2)}%",
            "⚠️ Overdue Tasks": overdue_tasks,
            "🔥 High Priority Tasks": high_priority_tasks
        }
    except Exception as e:
        return {"error": f"Exception: {str(e)}"}

def get_ai_recommendations(use_case, company_profile, workspace_details):
    """Generates AI-powered recommendations using OpenAI or Gemini."""
    prompt = f"""
Based on the following workspace data:
{workspace_details if workspace_details else "(No workspace data available)"}

Considering the company's use case: "{use_case}"
And the following company profile:
"{company_profile}"

Please provide a detailed analysis.

### 📈 Productivity Analysis:
Evaluate the current workspace structure and workflow. Provide insights on how to optimize productivity by leveraging the workspace metrics above and tailoring strategies to the specified use case.

### ✅ Actionable Recommendations:
Suggest practical steps to improve efficiency and organization, addressing specific challenges highlighted by the workspace data and the unique requirements of the use case, along with considerations from the company profile.

### 🏆 Best Practices & Tips:
Share industry-specific best practices and tips that can help maximize workflow efficiency for a company with this use case.

### 🛠️ Useful ClickUp Templates & Resources:
Recommend relevant ClickUp templates and resources. Provide hyperlinks to useful resources on clickup.com, university.clickup.com, or help.clickup.com.
    """

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
    except Exception as e:
        if gemini_api_key:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(prompt)
            return response.text
    return "⚠️ AI recommendations are not available because both OpenAI and Gemini failed."

# Streamlit UI
st.title("🚀 ClickUp Workspace Analyzer")

# Input fields available immediately
api_key = st.text_input("🔑 Enter ClickUp API Key (Optional):", type="password")
use_case = st.text_area("🏢 Describe your company's use case:")
company_name = st.text_input("🏢 Enter Company Name (Optional):")

if st.button("Analyze Workspace"):
    workspace_data = None
    if api_key:
        with st.spinner("Fetching workspace data..."):
            workspace_data = get_clickup_workspace_data(api_key)
        if workspace_data is None:
            st.error("Invalid API Key provided.")
        elif "error" in workspace_data:
            st.error(workspace_data["error"])
        else:
            st.subheader("📊 Workspace Summary")
            # Display workspace data as tiles
            cols = st.columns(4)
            for idx, (key, value) in enumerate(workspace_data.items()):
                with cols[idx % 4]:
                    st.metric(label=key, value=value)
    else:
        st.info("ClickUp API Key not provided. Skipping workspace data analysis.")

    # Build company profile if company name is provided
    if company_name:
        with st.spinner("Fetching company profile..."):
            company_profile = get_company_info(company_name)
    else:
        company_profile = "No company information provided."

    with st.spinner("Generating AI recommendations..."):
        recommendations = get_ai_recommendations(use_case, company_profile, workspace_data)
        st.markdown(recommendations, unsafe_allow_html=True)

# Section with useful hyperlinks to ClickUp resources and templates
st.markdown("### 🛠️ Useful ClickUp Templates & Resources:")
st.markdown("- [ClickUp Templates](https://clickup.com/templates)")
st.markdown("- [ClickUp University](https://university.clickup.com)")
st.markdown("- [ClickUp Help Center](https://help.clickup.com)")

st.markdown("<div style='position: fixed; bottom: 10px; right: 10px;'>Made by: Yul</div>", unsafe_allow_html=True)
