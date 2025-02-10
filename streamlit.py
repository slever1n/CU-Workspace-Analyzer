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

def fetch_workspace_details(clickup_api_key, team_id):
    """Fetch detailed workspace data including spaces, tasks, and completion stats."""
    headers = {"Authorization": clickup_api_key}
    
    spaces_url = f"https://api.clickup.com/api/v2/team/{team_id}/space"
    try:
        response = requests.get(spaces_url, headers=headers)
        if response.status_code == 200:
            spaces = response.json().get("spaces", [])
            return {
                "📁 Spaces": len(spaces),
                "📂 Folders": sum(len(space.get("folders", [])) for space in spaces),
                "🗂️ Lists": sum(len(space.get("lists", [])) for space in spaces),
                "✅ Completed Tasks": sum(1 for space in spaces for folder in space.get("folders", []) for list_item in folder.get("lists", []) for task in list_item.get("tasks", []) if task.get("status", "") == "completed"),
                "⚠️ Overdue Tasks": sum(1 for space in spaces for folder in space.get("folders", []) for list_item in folder.get("lists", []) for task in list_item.get("tasks", []) if task.get("due_date", 0) and int(task["due_date"]) < int(time.time() * 1000)),
                "📝 Total Tasks": sum(len(list_item.get("tasks", [])) for space in spaces for folder in space.get("folders", []) for list_item in folder.get("lists", [])),
                "🔥 High Priority Tasks": sum(1 for space in spaces for folder in space.get("folders", []) for list_item in folder.get("lists", []) for task in list_item.get("tasks", []) if task.get("priority", "") == "urgent")
            }
        else:
            return {"error": f"Error fetching workspace details: {response.status_code}"}
    except Exception as e:
        return {"error": f"Exception fetching workspace details: {str(e)}"}

def get_ai_recommendations(use_case, company_info, workspace_details):
    """Generates AI-powered recommendations using OpenAI or Gemini."""
    prompt = f"""
    **📌 Use Case:** {use_case}
    
    **🏢 Company Profile:**
    - **Google Description:** {company_info['Google Description']}
    - **LinkedIn Profile:** {company_info['LinkedIn Profile']}
    - **Company Website:** {company_info['Company Website']}
    
    ### 📈 Productivity Analysis:
    - Identify workflow bottlenecks and inefficiencies.
    - Evaluate task completion rates and overdue tasks.
    - Assess workload distribution across teams.
    - Suggest automation opportunities to reduce manual work.
    - Highlight underutilized ClickUp features.
    - Compare team performance against industry benchmarks.
    - Identify redundant tasks and streamline processes.
    - Recommend task prioritization strategies.
    
    ### ✅ Actionable Recommendations:
    - Implement task automation for repetitive processes.
    - Optimize task dependencies to avoid bottlenecks.
    - Set clear OKRs and track progress in ClickUp.
    - Establish standardized naming conventions for clarity.
    - Use ClickUp dashboards for real-time analytics.
    - Encourage team collaboration with ClickUp Docs.
    - Leverage recurring tasks for ongoing workflows.
    - Assign priorities and deadlines effectively.
    
    ### 🏆 Best Practices & Tips:
    - Use templates for recurring project structures.
    - Regularly review completed tasks for insights.
    - Encourage time tracking for accurate estimations.
    - Integrate ClickUp with other productivity tools.
    - Set up notifications to stay informed.
    - Use custom statuses for better workflow tracking.
    - Conduct weekly stand-ups using ClickUp comments.
    - Train teams on advanced ClickUp features.
    
    ### 🛠️ Useful ClickUp Templates & Resources:
    - [Task Management Template](https://clickup.com/templates/task-management)
    - [OKR Tracking Template](https://clickup.com/templates/okr-tracking)
    - [Agile Scrum Template](https://clickup.com/templates/agile-scrum)
    - [Sales CRM Template](https://clickup.com/templates/sales-crm)
    - [Product Roadmap Template](https://clickup.com/templates/product-roadmap)
    - [Team Collaboration Guide](https://university.clickup.com/)
    - [ClickUp Help Center](https://help.clickup.com/)
    - [Productivity Webinars](https://clickup.com/webinars)
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
st.markdown("Analyze your ClickUp workspace efficiency and get AI-powered recommendations.")
