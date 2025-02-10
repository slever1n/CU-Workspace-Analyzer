import asyncio
import requests
import streamlit as st
import threading
import queue
import time

# Set page title and icon
st.set_page_config(page_title="ClickUp Workspace Analysis", page_icon="🚀", layout="wide")

# Retrieve API keys from Streamlit secrets (replace with your actual secrets)
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
    """Generates a short company profile."""
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
                model="gpt-4",  # or gpt-3.5-turbo
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



async def fetch_workspace_details(api_key, team_id):
    headers = {"Authorization": api_key}
    try:
        spaces_url = f"https://api.clickup.com/api/v2/team/{team_id}/space"
        spaces_response = await asyncio.to_thread(requests.get, spaces_url, headers=headers)
        spaces_response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        spaces = spaces_response.json().get("spaces", [])

        space_count = len(spaces)
        folder_count, list_count, task_count = 0, 0, 0
        completed_tasks, overdue_tasks, high_priority_tasks = 0, 0, 0

        for space in spaces:
            space_id = space["id"]
            folders_url = f"https://api.clickup.com/api/v2/space/{space_id}/folder"
            folders_response = await asyncio.to_thread(requests.get, folders_url, headers=headers)
            folders_response.raise_for_status()
            folders = folders_response.json().get("folders", [])
            folder_count += len(folders)

            for folder in folders:
                folder_id = folder["id"]
                lists_url = f"https://api.clickup.com/api/v2/folder/{folder_id}/list"
                lists_response = await asyncio.to_thread(requests.get, lists_url, headers=headers)
                lists_response.raise_for_status()
                lists = lists_response.json().get("lists", [])
                list_count += len(lists)

                for lst in lists:
                    list_id = lst["id"]
                    tasks_url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
                    tasks_response = await asyncio.to_thread(requests.get, tasks_url, headers=headers)
                    tasks_response.raise_for_status()
                    tasks = tasks_response.json().get("tasks", [])

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
    except requests.exceptions.RequestException as e:
        return {"error": f"ClickUp API Error: {str(e)}"}
    except Exception as e:
        return {"error": f"Exception: {str(e)}"}

async def get_clickup_workspace_data(api_key):
    if not api_key:
        return None

    url = "https://api.clickup.com/api/v2/team"
    headers = {"Authorization": api_key}

    try:
        response = await asyncio.to_thread(requests.get, url, headers=headers)
        response.raise_for_status()
        teams = response.json().get("teams", [])
        if teams:
            team_id = teams[0]["id"]
            return await fetch_workspace_details(api_key, team_id)
        else:
            return {"error": "No teams found in ClickUp workspace."}
    except requests.exceptions.RequestException as e:
        return {"error": f"ClickUp API Error: {str(e)}"}
    except Exception as e:
        return {"error": f"Exception: {str(e)}"}

def get_ai_recommendations(use_case, company_profile, workspace_details):
    # ... (Your get_ai_recommendations function - remains unchanged)
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
                model="gpt-4",  # or gpt-3.5-turbo
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
            return "⚠️ AI recommendations are not available because both AI services failed."
    except Exception as e:
        return f"Error generating recommendations: {str(e)}"



def run
