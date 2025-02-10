import requests
import streamlit as st
import time
import openai
import google.generativeai as genai

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

def get_clickup_workspace_data(api_key):
    """Fetches real workspace data from ClickUp API."""
    if not api_key:
        return None  # Skip API call if no key is provided
    
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
        folder_count, list_count, task_count, completed_tasks, overdue_tasks, high_priority_tasks = 0, 0, 0, 0, 0, 0
        
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

def get_ai_recommendations(use_case, workspace_details):
    """Generates AI-powered recommendations using OpenAI or Gemini."""
    prompt = f"""
    **📌 Use Case:** {use_case}
    
    ### 🔍 Workspace Overview:
    {workspace_details if workspace_details else "(No workspace details available)"}
    
    ### 📈 Productivity Analysis:
    Provide insights on how to optimize productivity for this use case. Provide up to 8 bullets.
    
    ### ✅ Actionable Recommendations:
    Suggest practical steps to improve efficiency and organization. Provide up to 8 bullets.
    
    ### 🏆 Best Practices & Tips:
    Share industry-specific best practices to maximize workflow efficiency. Provide up to 8 bullets.
    
    ### 🛠️ Useful ClickUp Templates & Resources:
    List relevant ClickUp templates and best practices for this use case.
    Provide hyperlinks to useful resources on clickup.com, university.clickup.com, or help.clickup.com. and Provide up to 8 links.
    """
    
    try:
        if openai_api_key:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "You are a helpful assistant."},
                          {"role": "user", "content": prompt}]
            )
            return response["choices"][0]["message"]["content"]
    except Exception as e:
        if gemini_api_key:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(prompt)
            return response.text
    return "⚠️ AI recommendations are not available because both OpenAI and Gemini failed."

# UI Setup
st.title("📊 ClickUp Workspace Analyzer")

clickup_api_key = st.text_input("🔑 ClickUp API Key (Optional)", type="password")
use_case = st.text_input("📌 Use Case (e.g., Consulting, Sales)")

if st.button("🚀 Analyze Workspace"):
    if not use_case:
        st.error("Please enter a use case.")
    else:
        with st.spinner("🔄 Fetching ClickUp Workspace Data..."):
            if clickup_api_key:
                workspace_details = get_clickup_workspace_data(clickup_api_key)
            else:
                workspace_details = None
                st.warning("⚠️ ClickUp API key is blank. AI recommendations will be based only on the use case.")

        if workspace_details and "error" in workspace_details:
            st.error(f"❌ {workspace_details['error']}")
        elif workspace_details:
            st.subheader("📝 Workspace Analysis:")
            cols = st.columns(4)
            keys = list(workspace_details.keys())
            for i, key in enumerate(keys):
                with cols[i % 4]:
                    st.metric(label=key, value=workspace_details[key])

        with st.spinner("🤖 Generating AI recommendations..."):
            ai_recommendations = get_ai_recommendations(use_case, workspace_details)
        
        st.markdown(ai_recommendations, unsafe_allow_html=True)

st.markdown("<div style='position: fixed; bottom: 6px; right: 10px;'>Made by: Yul</div>", unsafe_allow_html=True)
