import requests
import streamlit as st
import time
import openai
import google.generativeai as genai
import textwrap
import concurrent.futures
import logging
from st_copy_to_clipboard import st_copy_to_clipboard

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set page title and icon
st.set_page_config(
    page_title="ClickUp Company Profile & Insights Generator",
    page_icon="./files/clickup.png",
    layout="centered",
    initial_sidebar_state="expanded",
)

# CSS
with open('./files/bg.css') as f:
    css = f.read()

st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# Logo
st.logo("./files/clickup.png", size="large", link="https://clickup.com")

# Hidden div with anchor
st.markdown("<div id='linkto_top'></div>", unsafe_allow_html=True)

# Sidebar content
with st.sidebar:
    st.title("ClickUp Company Profile & Insights Generator")
    st.markdown("""
    :blue-background[***ClickUp API Key (Optional):***]
    - Enter your ClickUp API key to fetch Workspace data. You can get this from your ClickUp settings and going to Apps to generate an API Key. **Once you enter your API, wait for a few seconds for th[...]

    :blue-background[***Company Name (Optional):***] 
    - Enter a company name or website to generate a short company profile. You can get this from the invite or the email of the user.

    :blue-background[***Company Use Case:***] 
    - Describe your company's use case (e.g., consulting, project management, customer service) or the agenda mentioned by the user in the email.

    :blue-background[***5 Minute Script:***] 
    - Use this when you want to create a video script for No-shows. Tick the checkbox and watch the magic happen. Both Use Case and Company Name have to be present.

    **Click the :green-background[*🚀 Let's Go!*] button to:**

    1. Fetch and display Workspace metrics (If API Key is entered and based on the Workspace selected).
    2. Generate a company profile.
    3. Generate tailored recommendations based on the provided data.
    4. Generate a 5-minute video script for No-shows.

    *ℹ️ This tool uses Gemini AI to provide AI recommendations and company profile*
    """)

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

@st.cache_data
def fetch_workspaces(api_key):
    """Fetches the list of workspaces from the ClickUp API."""
    if not api_key:
        return None

    url = "https://api.clickup.com/api/v2/team"
    headers = {"Authorization": api_key}

    try:
        start_time = time.time()
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises HTTPError for bad responses
        logging.info(f"API call to {url} took {time.time() - start_time:.2f} seconds")
        teams = response.json().get("teams", [])
        return {team["id"]: team["name"] for team in teams}
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        st.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"Other error occurred: {err}")
        st.error(f"An error occurred: {err}")
    return None

@st.cache_data
def fetch_workspace_details(api_key, team_id):
    """Fetches workspace details including spaces, folders, lists, and tasks. Also returns unassigned tasks and custom fields used."""
    headers = {"Authorization": api_key}
    
    try:
        spaces_url = f"https://api.clickup.com/api/v2/team/{team_id}/space"
        start_time = time.time()
        spaces_response = requests.get(spaces_url, headers=headers).json()
        logging.info(f"API call to {spaces_url} took {time.time() - start_time:.2f} seconds")
        spaces = spaces_response.get("spaces", [])
        
        space_count = len(spaces)
        folder_count, list_count, task_count = 0, 0, 0
        completed_tasks, overdue_tasks, high_priority_tasks = 0, 0, 0
        unassigned_tasks = 0
        custom_fields_set = set()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_space = {executor.submit(fetch_space_details, api_key, space["id"]): space for space in spaces}
            for future in concurrent.futures.as_completed(future_to_space):
                space_result = future.result()
                folder_count += space_result['folder_count']
                list_count += space_result['list_count']
                task_count += space_result['task_count']
                completed_tasks += space_result['completed_tasks']
                overdue_tasks += space_result['overdue_tasks']
                high_priority_tasks += space_result['high_priority_tasks']
                unassigned_tasks += space_result.get('unassigned_tasks', 0)
                custom_fields_set.update(space_result.get('custom_fields_set', set()))

        task_completion_rate = (completed_tasks / task_count * 100) if task_count > 0 else 0
        
        return {
            "🪐 Spaces": space_count,
            "📂 Folders": folder_count,
            "🗂️ Lists": list_count,
            "📝 Total Tasks": task_count,
            "⚠️ Overdue Tasks": overdue_tasks,
            "🔥 High Priority Tasks": high_priority_tasks,
            "📝 Unassigned Tasks": unassigned_tasks,
            "🛠️ Custom Fields Used": len(custom_fields_set)
        }
    except Exception as e:
        logging.error(f"Exception: {str(e)}")
        st.error(f"Exception: {str(e)}")
        return {"error": f"Exception: {str(e)}"}

def fetch_space_details(api_key, space_id):
    """Fetches details for a specific space including folders, lists, and tasks."""
    headers = {"Authorization": api_key}
    folder_count, list_count, task_count = 0, 0, 0
    completed_tasks, overdue_tasks, high_priority_tasks = 0, 0, 0
    unassigned_tasks = 0
    custom_fields_set = set()

    folders_url = f"https://api.clickup.com/api/v2/space/{space_id}/folder"
    start_time = time.time()
    folders_response = requests.get(folders_url, headers=headers).json()
    logging.info(f"API call to {folders_url} took {time.time() - start_time:.2f} seconds")
    folders = folders_response.get("folders", [])
    folder_count += len(folders)
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_folder = {executor.submit(fetch_folder_details, api_key, folder["id"]): folder for folder in folders}
        for future in concurrent.futures.as_completed(future_to_folder):
            folder_result = future.result()
            list_count += folder_result['list_count']
            task_count += folder_result['task_count']
            completed_tasks += folder_result['completed_tasks']
            overdue_tasks += folder_result['overdue_tasks']
            high_priority_tasks += folder_result['high_priority_tasks']
            unassigned_tasks += folder_result.get('unassigned_tasks', 0)
            custom_fields_set.update(folder_result.get('custom_fields_set', set()))
    
    return {
        'folder_count': folder_count,
        'list_count': list_count,
        'task_count': task_count,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'high_priority_tasks': high_priority_tasks,
        'unassigned_tasks': unassigned_tasks,
        'custom_fields_set': custom_fields_set
    }

def fetch_folder_details(api_key, folder_id):
    """Fetches details for a specific folder including lists and tasks."""
    headers = {"Authorization": api_key}
    list_count, task_count = 0, 0
    completed_tasks, overdue_tasks, high_priority_tasks = 0, 0, 0
    unassigned_tasks = 0
    custom_fields_set = set()

    lists_url = f"https://api.clickup.com/api/v2/folder/{folder_id}/list"
    start_time = time.time()
    lists_response = requests.get(lists_url, headers=headers).json()
    logging.info(f"API call to {lists_url} took {time.time() - start_time:.2f} seconds")
    lists = lists_response.get("lists", [])
    list_count += len(lists)
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_list = {executor.submit(fetch_list_details, api_key, lst["id"]): lst for lst in lists}
        for future in concurrent.futures.as_completed(future_to_list):
            list_result = future.result()
            task_count += list_result['task_count']
            completed_tasks += list_result['completed_tasks']
            overdue_tasks += list_result['overdue_tasks']
            high_priority_tasks += list_result['high_priority_tasks']
            unassigned_tasks += list_result.get('unassigned_tasks', 0)
            custom_fields_set.update(list_result.get('custom_fields_set', set()))
    
    return {
        'list_count': list_count,
        'task_count': task_count,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'high_priority_tasks': high_priority_tasks,
        'unassigned_tasks': unassigned_tasks,
        'custom_fields_set': custom_fields_set
    }

def fetch_list_details(api_key, list_id):
    """Fetches details for a specific list including tasks, unassigned tasks, and custom fields used."""
    headers = {"Authorization": api_key}
    task_count = 0
    completed_tasks, overdue_tasks, high_priority_tasks = 0, 0, 0
    unassigned_tasks = 0
    custom_fields_set = set()

    tasks_url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
    start_time = time.time()
    params = {
        "archived": "false",
        "subtasks": "true"
    }
    tasks_response = requests.get(tasks_url, headers=headers, params=params).json()
    logging.info(f"API call to {tasks_url} took {time.time() - start_time:.2f} seconds")
    tasks = tasks_response.get("tasks", [])
    task_count += len(tasks)
    
    for task in tasks:
        status = task.get("status", {}).get("type", "").lower()
        logging.info(f"Task ID: {task['id']} - Status: {status}")
        completed_tasks += 1 if status in ["closed", "done", "completed"] else 0
        overdue_tasks += 1 if task.get("due_date") and int(task["due_date"]) < int(time.time() * 1000) else 0
        high_priority_tasks += 1 if task.get("priority", "") in ["urgent", "high"] else 0

        # Count unassigned tasks
        if not task.get("assignees"):
            unassigned_tasks += 1

        # Gather custom fields
        for cf in task.get("custom_fields", []):
            custom_fields_set.add(cf.get("name", cf.get("id", "Unknown")))

    logging.info(f"Total tasks: {task_count}, Completed tasks: {completed_tasks}, Unassigned: {unassigned_tasks}")

    return {
        'task_count': task_count,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'high_priority_tasks': high_priority_tasks,
        'unassigned_tasks': unassigned_tasks,
        'custom_fields_set': custom_fields_set
    }

def get_company_info(company_name):
    """Generates a short company profile for the given company name using Gemini (or OpenAI if Gemini is unavailable)."""
    if not company_name:
        return "No company information provided."
    
    prompt = textwrap.dedent(f"""
        Please build a short company profile for {company_name}. Go straight to the point and skip usual AI introductions. The profile should include the following sections:
        - **Company Size:** Provide an estimate of the company’s size (e.g., number of employees) based on public information or platforms like LinkedIn. Do not make assumptions, if its unavailable,[...]
        - **Net Worth:** Include the company’s net worth or valuation if publicly available. Do not make assumptions, if its unavailable, skip it.
        - **Mission:** A brief mission statement.
        - **Key Features:** List 3-5 key features of the company.
        - **Vision:** State the long-term vision of the company, highlighting its aspirations and the impact it aims to create.
        - **Their Product:** Describe the company’s main product or service in detail.
        - **Target Audience:** Identify the primary groups of people or industries the company caters to.
        - **Overall Summary:** Summarize the company’s identity, vision, and value proposition in a few sentences.
    """)
    
    try:
        if gemini_api_key:
            model = genai.GenerativeModel("gemini-2.5-pro")
            response = model.generate_content(prompt)
            return response.text
        elif openai_api_key:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages = [
    {
        "role": "system",
        "content": (
            "You are a ClickUp implementation specialist. Give clear, detailed, expert-level guidance. Analyze the provided data to determine how to use ClickUp better. When presented with the data, provide recommendations and analysis that reflect a deep understanding of ClickUp's capabilities and workflow best practices, guaranteeing their correctness."
        )
    },
    {
        "role": "user",
        "content": prompt
    }
]
            )
            return response["choices"][0]["message"]["content"]
        else:
            return "No AI service available for generating company profile."
    except Exception as e:
        logging.error(f"Error fetching company details: {str(e)}")
        return f"Error fetching company details: {str(e)}"

def get_ai_recommendations(use_case, company_profile, workspace_details):
    """Generates AI-powered recommendations based on workspace data, company profile, and use case."""
    prompt = textwrap.dedent(f"""
        Based on the following workspace data:
        {workspace_details if workspace_details else "(No workspace data available)"}
        
        Considering the company's use case: "{use_case}"
        And the following company profile:
        {company_profile}
        
        Please provide a detailed analysis. Go straight to the point and skip usual AI introductions
        
        <h3>📈 Productivity Analysis</h3>
        Evaluate the current workspace structure and workflow. Provide insights on how to optimize productivity by leveraging the workspace metrics above, if no workspace metric is found, provide tailored recommendations based on the use case. Be as detailed as you can.

        <h3>✅ Actionable Recommendations</h3>
        Suggest practical steps to improve efficiency and organization, addressing specific challenges highlighted by the workspace data and the unique requirements of the use case, along with consideration of industry best practices.

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
    except Exception as e:
        if gemini_api_key:
            model = genai.GenerativeModel("gemini-2.5-pro")
            response = model.generate_content(prompt)
            return response.text
    return "⚠️ AI recommendations are not available because both AI services failed."

def generate_script(use_case, company_info):
    """Generates a 5-minute script for a video demo using Gemini."""
    prompt = textwrap.dedent(f"""
        - You are a ClickUp Digital adoption specialist. Create a 5-minute script for a video demo on how to use ClickUp based on {use_case} for this {company_info}. 
        - Keep it low key and informative, kind of a professional client onboarding type of video wherein its suited for 1:1 calls. 
        - To add context this is for clients who missed the call, and this video is for them to get an overview of how to use ClickUp based on the use case.
        - Rules: 
            - Go straight to the point and skip usual AI introductions.
            - important: make sure that the steps you provide in the demo is based on ClickUp and ClickUp's UI.
            - do not mention the word onboarding.
            - greeting should be something like: "Hey! I noticed you missed our call, but not to worry, I still want to make sure you get the most value from ClickUp.
            I’ve recorded a personalized demo for you, highlighting key features that teams like yours have found useful. 
            I’ve also included insights based on the agenda you mentioned in your email."
            - keep it simple and straightforward and don't add music cues. no need for that.
            - try to make the script more readable by adding line breaks or dividers.
    """)
    
    try:
        if gemini_api_key:
            model = genai.GenerativeModel("gemini-2.5-pro")
            response = model.generate_content(prompt)
            return response.text
        elif openai_api_key:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                 messages = [
    {
        "role": "system",
        "content": (
             "You are a ClickUp implementation specialist. Give clear, detailed, expert-level guidance. Analyze the provided data to determine how to use ClickUp better. When presented with the data, provide recommendations and analysis that reflect a deep understanding of ClickUp's capabilities and workflow best practices, guaranteeing their correctness."
        )
    },
    {
        "role": "user",
        "content": prompt
    }
]
            )
            return response["choices"][0]["message"]["content"]
        else:
            return "No AI service available for generating the script."
    except Exception as e:
        logging.error(f"Error generating script: {str(e)}")
        return f"Error generating script: {str(e)}"

# Input fields available immediately
with st.expander("🔑 ClickUp API Key: (Optional)"):
    api_key = st.text_input("", type="password")
    
    if api_key:
        workspaces = fetch_workspaces(api_key)
        
        if workspaces:
            workspace_id = st.selectbox(
                "💼 Select Workspace:", 
                options=list(workspaces.keys()), 
                format_func=lambda x: workspaces[x]
            )
        else:
            st.error("Failed to fetch workspaces. Please check your API key.")
    else:
        workspace_id = None

company_name = st.text_input("🏢 Enter company name or website (Optional):")
use_case = st.text_area("🧑‍💻 Describe your company's use case or agenda:")

# Add checkbox for script generation
st.write("")
genscript = st.checkbox("🎬 Generate a 5-minute script for a video demo? (For No-shows)", value=False, on_change=None)
st.write("")

if st.button("🚀 Let's Go!"):
    if genscript:
        if use_case and company_name:
            with st.spinner("Generating script..."):
                script = generate_script(use_case, company_name)
                st.subheader("🎬 Generated Script")
                st.write(script)
                st_copy_to_clipboard(script, before_copy_label='📋 Copy', after_copy_label='✅ Recommendations copied!')
                st.markdown("<a href='#linkto_top'>Back to top</a>", unsafe_allow_html=True)
        else:
            st.error("Please provide both use case and company info.")
    else:
        if api_key and workspace_id:
            workspace_data = None
            with st.spinner("Fetching workspace data, may take longer for larger Workspaces..."):
                workspace_data = fetch_workspace_details(api_key, workspace_id)
            if workspace_data is None:
                st.error("Failed to fetch workspace data.")
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
            workspace_data = None

        # Build and display company profile if a company name is provided
        if company_name:
            with st.spinner("Generating company profile..."):
                company_profile = get_company_info(company_name)
            st.subheader("🏢 Company Profile")
            st.markdown(company_profile, unsafe_allow_html=True)
            st_copy_to_clipboard(company_profile, before_copy_label='📋 Copy', after_copy_label='✅ Company Profile copied!')
        else:
            company_profile = "No company information provided."
        
        with st.spinner("Generating AI recommendations..."):
            recommendations = get_ai_recommendations(use_case, company_profile, workspace_data)
            st.subheader("💡 Recommendations")
            st.markdown(recommendations, unsafe_allow_html=True)
            st.divider()
            st_copy_to_clipboard(recommendations, before_copy_label='📋 Copy', after_copy_label='✅ Recommendations copied!')
            st.markdown("<a href='#linkto_top'>Back to top</a>", unsafe_allow_html=True)

st.markdown("<div style='position: fixed; bottom: 10px; left: 10px; font-size: 12px; color: #c7c6c6; '>A little tool made with ❤️ by: Yul</div>", unsafe_allow_html=True)
