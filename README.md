
# 📊 ClickUp Workspace Analyzer    

A Streamlit application that analyzes your ClickUp workspace, generates a company profile using AI, and provides tailored recommendations to improve productivity and organization based on your workspace data, your company's use case, and the generated company profile.

## ⭐ Features

- **Workspace Analysis:**  
  Fetches and displays metrics (e.g., Spaces, Folders, Lists, Total Tasks, Completed Tasks, Task Completion Rate, Overdue Tasks, High Priority Tasks) from your ClickUp workspace using the ClickUp API.

- **Company Profile Generation:**  
  Uses the Gemini model (specifically `gemini-2.0-flash`) to create a short, structured company profile based on a provided company name. If Gemini is not available, it falls back to OpenAI.

- **AI-Powered Recommendations:**  
  Combines workspace metrics, the company profile, and your described use case to generate actionable recommendations and best practices to optimize your workflow.

- **Useful ClickUp Resources:**  
  Provides direct links to ClickUp Templates, ClickUp University, and the ClickUp Help Center.

##🛠️ Requirements

- Python 3.7 or higher
- [Streamlit](https://streamlit.io/)
- [Requests](https://pypi.org/project/requests/)
- [OpenAI Python Client](https://pypi.org/project/openai/)
- [Google Generative AI Python Client](https://pypi.org/project/google-generativeai/) *(if using Gemini)*
- [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/)




##⚙️ Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/clickup-workspace-analyzer.git
   cd clickup-workspace-analyzer


Install the required packages:


**2. Install the required packages:**


```bash
 pip install streamlit requests openai google-generativeai beautifulsoup4
```
    

**3. Configure your API keys:**

Create a secrets.toml file in a folder named .streamlit in your project directory and add your API keys:

```bash
OPENAI_API_KEY = "your_openai_api_key"
OPENAI_ORG_ID = "your_openai_org_id"
GEMINI_API_KEY = "your_gemini_api_key"
```
##💡 Usage/Examples

**1. Run the Application**

```bash
streamlit run your_script.py

```

**2. Interact with the App:**

ClickUp API Key (Optional): Enter your `ClickUp API key` to fetch workspace data.

Company Use Case: Describe your company's use case (e.g., consulting, project management, customer service).

Company Name (Optional): Enter a company name to generate a short company profile using AI.

**3. Analyze Workspace:**

Click the `Analyze Workspace` button to:

Fetch and display workspace metrics.

Generate a company profile.

Generate tailored AI recommendations based on the provided data.

**4. View Resources:**

Useful ClickUp resources are linked at the bottom of the app.




##📝 Notes

**1. Workspace Analysis:**
If no ClickUp API key is provided, the workspace analysis is skipped, but AI recommendations will still be generated based on the provided use case and company profile.

**2. AI Services:**
The app uses the Gemini model `gemini-2.0-flash` for generating the company profile and AI recommendations. It falls back to OpenAI if Gemini is unavailable.

##🪪 License

This project is open source. Feel free to use, modify, and distribute it as needed.



##👤 Authors

Made by Yul <3<3<3

- [@sleverin](https://github.com/slever1n)

