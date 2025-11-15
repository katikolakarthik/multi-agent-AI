"""
Streamlit Frontend for Lyzr PR Review Agent
"""
import streamlit as st
import httpx
import json
from typing import List, Dict
import time

# Page configuration
st.set_page_config(
    page_title="Lyzr PR Review Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .review-comment {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
        border-left: 4px solid;
    }
    .critical { 
        border-left-color: #d32f2f; 
        background-color: #ffebee; 
        color: #000000;
    }
    .major { 
        border-left-color: #f57c00; 
        background-color: #fff3e0; 
        color: #000000;
    }
    .minor { 
        border-left-color: #fbc02d; 
        background-color: #fffde7; 
        color: #000000;
    }
    .suggestion { 
        border-left-color: #388e3c; 
        background-color: #e8f5e9; 
        color: #000000;
    }
    
    .review-comment {
        color: #000000 !important;
    }
    
    .review-comment h4 {
        color: #000000 !important;
    }
    
    .review-comment p {
        color: #000000 !important;
    }
    
    .review-comment code {
        background-color: #f5f5f5;
        color: #000000;
        padding: 2px 6px;
        border-radius: 3px;
    }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8000"

def check_api_health():
    """Check if the API server is running"""
    try:
        response = httpx.get(f"{API_BASE_URL}/health", timeout=5.0)
        if response.status_code == 200:
            return True, response.json()
        return False, None
    except httpx.ConnectError:
        return False, None
    except Exception:
        return False, None

def review_pr(repo_owner: str, repo_name: str, pr_number: int, github_token: str = None, quick_review: bool = True):
    """Call the PR review API"""
    # Validate inputs
    repo_owner = repo_owner.strip() if repo_owner else ""
    repo_name = repo_name.strip() if repo_name else ""
    
    if not repo_owner or not repo_name:
        st.error("Please provide both repository owner and name")
        return None
    
    try:
        payload = {
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "pr_number": pr_number,
            "quick_review": quick_review
        }
        if github_token:
            payload["github_token"] = github_token
        
        with httpx.Client(timeout=600.0) as client:  # Increased to 10 minutes
            response = client.post(
                f"{API_BASE_URL}/api/review/pr",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        error_text = e.response.text
        try:
            error_json = e.response.json()
            error_detail = error_json.get("detail", error_text)
        except:
            error_detail = error_text
        
        # Provide user-friendly error messages
        if "404" in error_detail or "not found" in error_detail.lower():
            st.error(f"❌ **Repository or PR not found**\n\n"
                    f"Could not find PR #{pr_number} in `{repo_owner}/{repo_name}`.\n\n"
                    f"**Possible reasons:**\n"
                    f"- The repository doesn't exist\n"
                    f"- The PR number is incorrect\n"
                    f"- The repository is private (try adding a GitHub token)")
        elif "403" in error_detail or "access denied" in error_detail.lower():
            st.error(f"🔒 **Access Denied**\n\n"
                    f"Could not access repository `{repo_owner}/{repo_name}`.\n\n"
                    f"**Solution:** Add a GitHub Personal Access Token in the sidebar to access private repositories.")
        else:
            st.error(f"❌ **API Error ({e.response.status_code})**\n\n{error_detail}")
        return None
    except Exception as e:
        st.error(f"❌ **Error:** {str(e)}")
        return None

def review_diff(diff_text: str, file_path: str = None):
    """Call the diff review API"""
    try:
        payload = {"diff_text": diff_text}
        if file_path:
            payload["file_path"] = file_path
        
        with httpx.Client(timeout=600.0) as client:  # Increased to 10 minutes
            response = client.post(
                f"{API_BASE_URL}/api/review/diff",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"API Error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def display_review_results(review_data: Dict):
    """Display review results in a nice format"""
    if not review_data:
        return
    
    # Summary Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Comments", review_data.get("total_comments", 0))
    
    with col2:
        st.metric("Files Changed", review_data.get("total_files_changed", 0))
    
    # Count by severity
    comments = review_data.get("comments", [])
    critical_count = sum(1 for c in comments if c.get("severity") == "critical")
    major_count = sum(1 for c in comments if c.get("severity") == "major")
    
    with col3:
        st.metric("Critical Issues", critical_count, delta=None, delta_color="inverse")
    
    with col4:
        st.metric("Major Issues", major_count, delta=None, delta_color="inverse")
    
    # Summary
    st.markdown("### 📋 Review Summary")
    st.info(review_data.get("summary", "No summary available"))
    
    # Comments
    if comments:
        st.markdown("### 💬 Review Comments")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            severity_filter = st.multiselect(
                "Filter by Severity",
                ["critical", "major", "minor", "suggestion"],
                default=["critical", "major", "minor", "suggestion"]
            )
        with col2:
            category_filter = st.multiselect(
                "Filter by Category",
                ["logic", "readability", "performance", "security", "best_practices", "testing"],
                default=["logic", "readability", "performance", "security", "best_practices", "testing"]
            )
        
        # Filter comments
        filtered_comments = [
            c for c in comments
            if c.get("severity") in severity_filter
            and c.get("category") in category_filter
        ]
        
        if not filtered_comments:
            st.warning("No comments match the selected filters.")
        else:
            for comment in filtered_comments:
                severity = comment.get("severity", "suggestion")
                category = comment.get("category", "general")
                
                # Severity badge color
                severity_colors = {
                    "critical": "🔴",
                    "major": "🟠",
                    "minor": "🟡",
                    "suggestion": "🟢"
                }
                
                # Category emoji
                category_emojis = {
                    "logic": "🧠",
                    "readability": "📖",
                    "performance": "⚡",
                    "security": "🔒",
                    "best_practices": "✨",
                    "testing": "🧪"
                }
                
                emoji = severity_colors.get(severity, "🟢")
                cat_emoji = category_emojis.get(category, "📝")
                
                with st.container():
                    # Use Streamlit's native components for better visibility
                    severity_emoji = severity_colors.get(severity, "🟢")
                    cat_emoji = category_emojis.get(category, "📝")
                    
                    # Create expandable section for each comment
                    with st.expander(f"{severity_emoji} {cat_emoji} **{comment.get('title', 'Review Comment')}** - {severity.upper()}", expanded=(severity in ["critical", "major"])):
                        st.markdown(f"""
                        **File:** `{comment.get('file_path', 'N/A')}` | 
                        **Line:** {comment.get('line_number', 'N/A')} | 
                        **Category:** {category.title()} | 
                        **Severity:** {severity.title()}
                        """)
                        
                        st.markdown("**Description:**")
                        st.markdown(comment.get('description', 'No description'))
                        
                        if comment.get('code_snippet'):
                            st.markdown("**Code Snippet:**")
                            st.code(comment.get('code_snippet'), language='python')
                        
                        if comment.get('suggestion'):
                            st.info(f"💡 **Suggestion:** {comment.get('suggestion')}")
                    
                    st.divider()
    else:
        st.success("✅ No issues found! Code looks good.")

def main():
    """Main Streamlit app"""
    # Header
    st.markdown('<h1 class="main-header">🤖 Lyzr PR Review Agent</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Health Check
        st.subheader("API Status")
        api_healthy, health_data = check_api_health()
        
        if api_healthy:
            st.success("✅ API Connected")
            if health_data:
                provider = health_data.get('llm_provider', 'N/A')
                model = health_data.get('model', 'N/A')
                watsonx_configured = health_data.get('watsonx_configured', None)
                
                st.info(f"**Provider:** {provider}\n**Model:** {model}")
                
                if provider == "watsonx" and watsonx_configured is False:
                    st.warning("⚠️ Watsonx credentials not configured")
        else:
            st.error("❌ API Not Connected")
            st.warning("Make sure the FastAPI server is running on http://localhost:8000")
            st.code("python run.py\n# or\nuvicorn main:app --reload", language="bash")
        
        st.markdown("---")
        
        # GitHub Token (optional)
        github_token = st.text_input(
            "GitHub Token (Optional)",
            type="password",
            help="Optional: Provide a GitHub token for private repos"
        )
        
        st.markdown("---")
        st.markdown("### 📚 About")
        st.info("""
        This tool uses a multi-agent AI system to review code changes:
        
        - 🧠 **Logic Agent**: Finds bugs and logic errors
        - 📖 **Readability Agent**: Checks code clarity
        - ⚡ **Performance Agent**: Identifies bottlenecks
        - 🔒 **Security Agent**: Detects vulnerabilities
        """)
    
    # Main content
    tab1, tab2 = st.tabs(["🔍 Review GitHub PR", "📝 Review Manual Diff"])
    
    with tab1:
        st.header("Review GitHub Pull Request")
        st.markdown("Enter the details of the GitHub PR you want to review.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            repo_owner = st.text_input(
                "Repository Owner", 
                placeholder="octocat",
                help="GitHub username or organization name"
            ).strip()
        
        with col2:
            repo_name = st.text_input(
                "Repository Name", 
                placeholder="Hello-World",
                help="Name of the repository (without spaces)"
            ).strip()
        
        with col3:
            pr_number = st.number_input(
                "PR Number", 
                min_value=1, 
                value=1, 
                step=1,
                help="Pull request number"
            )
        
        # Quick review option
        quick_review = st.checkbox(
            "⚡ Quick Review Mode",
            value=True,
            help="Faster review by analyzing fewer files and using only Logic & Security agents"
        )
        
        # Show example
        with st.expander("💡 Example"):
            st.code("""
Repository Owner: octocat
Repository Name: Hello-World
PR Number: 1
            """, language="text")
        
        if st.button("🚀 Start Review", type="primary", use_container_width=True):
            if not repo_owner or not repo_name:
                st.error("⚠️ Please provide both repository owner and name")
            elif " " in repo_owner or " " in repo_name:
                st.warning("⚠️ Repository owner and name should not contain spaces. Use hyphens (-) or underscores (_) instead.")
            else:
                # Create progress container
                progress_container = st.container()
                with progress_container:
                    status_text = st.empty()
                    progress_bar = st.progress(0)
                    status_text.info("🔄 Fetching PR from GitHub...")
                    progress_bar.progress(10)
                
                try:
                    review_data = review_pr(repo_owner, repo_name, int(pr_number), github_token, quick_review)
                    
                    if review_data:
                        progress_bar.progress(100)
                        status_text.success("✅ Review completed!")
                        st.success("✅ Review completed!")
                        display_review_results(review_data)
                except Exception as e:
                    progress_bar.progress(0)
                    status_text.error(f"❌ Error: {str(e)}")
                    raise
    
    with tab2:
        st.header("Review Manual Diff")
        st.markdown("Paste a Git diff to review code changes directly.")
        
        file_path = st.text_input("File Path (Optional)", placeholder="src/main.py")
        
        diff_text = st.text_area(
            "Diff Text",
            height=300,
            placeholder="""diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,5 +1,5 @@
 def calculate_total(items):
-    total = 0
-    for item in items:
-        total += item.price
-    return total
+    return sum(item.price for item in items)
+
+def get_user_data(user_id):
+    query = f"SELECT * FROM users WHERE id = {user_id}"
+    return execute_query(query)
"""
        )
        
        if st.button("🚀 Review Diff", type="primary", use_container_width=True):
            if not diff_text.strip():
                st.error("Please provide a diff to review")
            else:
                # Create progress container
                progress_container = st.container()
                with progress_container:
                    status_text = st.empty()
                    progress_bar = st.progress(0)
                    status_text.info("🔄 Analyzing code changes with AI agents...")
                    progress_bar.progress(20)
                
                try:
                    review_data = review_diff(diff_text, file_path if file_path else None)
                    
                    if review_data:
                        progress_bar.progress(100)
                        status_text.success("✅ Review completed!")
                        st.success("✅ Review completed!")
                        display_review_results(review_data)
                except Exception as e:
                    progress_bar.progress(0)
                    status_text.error(f"❌ Error: {str(e)}")
                    raise
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; padding: 1rem;'>"
        "Built with ❤️ for Lyzr AI Backend Engineering Challenge"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()

