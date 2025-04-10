import streamlit as st
import os
import json
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
import pdfkit
import base64
from streamlit import components
import re
from PIL import Image
import io
import streamlit.components.v1 as components
import cohere

# Load environment variables
load_dotenv()
co = cohere.Client(os.getenv("COHERE_API_KEY"))

# Configure wkhtmltopdf path
pdf_config = pdfkit.configuration(
    wkhtmltopdf=r'E:\resume-generator\wkhtmltopdf\bin\wkhtmltopdf.exe')

# Custom CSS for a better looking app
st.set_page_config(page_title="AI Resume Generator",
                   layout="wide", initial_sidebar_state="expanded")

# Apply custom CSS
st.markdown("""
<style>
    .main {
        background-color: black;
        padding: 2rem;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #45a049;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .step-container {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 1.5rem;
    }
    h1, h2, h3 {
        color: #2C3E50;
    }
    .highlight {
        background-color: #e3f2fd;
        padding: 1rem;
        border-left: 4px solid #1976d2;
        margin: 1rem 0;
    }
    .stProgress > div > div > div {
        background-color: #4CAF50;
    }
    .download-btn {
        background-color: #1976d2 !important;
    }
    .form-header {
        background-color: #f1f8e9;
        padding: 0.5rem;
        border-radius: 5px;
        margin-bottom: 1rem;
        border-left: 4px solid #7cb342;
    }
    .preview-container {
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 1rem;
    }
    .sidebar .sidebar-content {
        background-color: #f1f8e9;
    }
    .small-input {
        max-width: 300px !important;
    }
    .entry-card {
        background-color: #f9f9f9;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 10px;
        border-left: 3px solid #4CAF50;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 6px 6px 0 0;
        padding: 10px 16px;
        border: 1px solid #e0e0e0;
        border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e8f5e9 !important;
        border-bottom: 2px solid #4CAF50 !important;
    }
</style>
""", unsafe_allow_html=True)

# Resume template rendering

def render_resume(data, template="minimal.html"):
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template(template)
    return template.render(data=data)

# Email validation function

def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None

# Phone validation function

def is_valid_phone(phone):
    pattern = r"^[\d\+\-\(\) ]{6,20}$"
    return re.match(pattern, phone) is not None

# Function to enhance resume with AI assistance

def enhance_with_ai(field, content, context=None):
    try:
        prompt = f"Improve this {field} for a resume: '{content}'"
        if context:
            prompt += f"\nContext: {context}"

        response = co.chat(
            message=prompt,
            model="command-r",
            temperature=0.7,
            preamble="You are a professional resume writer helping improve resume content. Provide concise, impactful improvements."
        )
        return response.text.strip()
    except Exception as e:
        return f"Error enhancing content: {str(e)}"


# Session state setup
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chat_step" not in st.session_state:
    st.session_state.chat_step = 0
if "resume_data" not in st.session_state:
    st.session_state.resume_data = {
        "name": "", "role": "", "summary": "",
        "location": "", "email": "", "phone": "", "website": "",
        "experience": [], "education": [],
        "skills": [], "certifications": [],
        "projects": [], "languages": [], "hobbies": [], "socials": [], "image_base64": None
    }
if "current_page" not in st.session_state:
    st.session_state.current_page = "Basic Info"

# App Header
col1, col2 = st.columns([1, 5])
with col1:
    st.image("https://img.icons8.com/color/96/000000/resume.png", width=80)
with col2:
    st.title("AI Resume Builder")
    st.markdown("Create a professional resume in minutes with AI assistance ✨")

# Navigation sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/resume.png", width=50)
    st.header("Navigation")

    # Calculate progress
    sections = ["Basic Info", "Education", "Experience", "Projects",
                "Additional Info", "Styling", "Preview & Download"]

    section_choice = st.radio("Go to section:", sections, index=sections.index(
        st.session_state.current_page))
    if section_choice != st.session_state.current_page:
        st.session_state.current_page = section_choice
        st.rerun()

    # Progress indicator
    progress_percentage = (sections.index(
        st.session_state.current_page) + 1) / len(sections)
    st.progress(progress_percentage)
    st.caption(
        f"Step {sections.index(st.session_state.current_page) + 1} of {len(sections)}")

    st.markdown("---")
    st.markdown("### Quick Tips")
    st.info("💡 Keep your resume concise - 1-2 pages is ideal")
    st.info("💡 Quantify achievements when possible")
    st.info("💡 Tailor your resume to the job you're applying for")

    # AI Assistant in sidebar
    st.markdown("---")
    st.markdown("### AI Resume Assistant")
    ai_help = st.text_area("Ask for resume writing tips", height=100,
                           placeholder="E.g., How do I write a great summary?")

    if st.button("Get AI Advice"):
        if ai_help:
            with st.spinner("Getting expert advice..."):
                try:
                    response = co.chat(
                        message=ai_help,
                        model="command-r",
                        temperature=0.7,
                        preamble="You are a professional resume expert. Provide brief, actionable resume advice."
                    )
                    st.success(response.text)
                except Exception as e:
                    st.error(f"Could not get AI advice: {str(e)}")
        else:
            st.warning("Please enter a question first")

# Basic Info Page
if st.session_state.current_page == "Basic Info":
    with st.container():
        st.markdown("## 📝 Basic Information")
        st.markdown("Let's start with your personal details.")

        col1, col2 = st.columns(2)
        with col1:
            st.session_state.resume_data["name"] = st.text_input(
                "Full Name", value=st.session_state.resume_data["name"])
            st.session_state.resume_data["role"] = st.text_input("Target Job Title",
                                                                 value=st.session_state.resume_data["role"],
                                                                 help="What position are you applying for?")
            st.session_state.resume_data["location"] = st.text_input(
                "Location", value=st.session_state.resume_data["location"])

        with col2:
            email = st.text_input(
                "Email Address", value=st.session_state.resume_data["email"])
            if email and not is_valid_email(email):
                st.warning("Please enter a valid email address")
            else:
                st.session_state.resume_data["email"] = email

            phone = st.text_input(
                "Phone Number", value=st.session_state.resume_data["phone"])
            if phone and not is_valid_phone(phone):
                st.warning("Please enter a valid phone number")
            else:
                st.session_state.resume_data["phone"] = phone

            st.session_state.resume_data["website"] = st.text_input("Website/Portfolio URL (optional)",
                                                                    value=st.session_state.resume_data["website"])

        st.session_state.resume_data["summary"] = st.text_area("Professional Summary (2-3 sentences)",
                                                               value=st.session_state.resume_data["summary"],
                                                               height=150,
                                                               help="A brief overview of your professional background and goals")

        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("✨ Enhance Summary with AI"):
                if st.session_state.resume_data["summary"]:
                    with st.spinner("Enhancing your summary..."):
                        context = f"Job target: {st.session_state.resume_data['role']}" if st.session_state.resume_data[
                            "role"] else None
                        enhanced_summary = enhance_with_ai(
                            "professional summary", st.session_state.resume_data["summary"], context)
                        st.session_state.resume_data["summary"] = enhanced_summary
                        st.rerun()
                else:
                    st.warning("Please write a summary first")

        # Photo upload with preview
        st.markdown("### 🖼️ Profile Photo (optional)")
        col1, col2 = st.columns([1, 2])
        with col1:
            uploaded_image = st.file_uploader(
                "Upload your photo", type=["png", "jpg", "jpeg"])
            if uploaded_image:
                image = Image.open(uploaded_image)
                # Resize image if too large
                max_size = (300, 300)
                image.thumbnail(max_size)
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                st.session_state.resume_data["image_base64"] = base64.b64encode(
                    buffered.getvalue()).decode("utf-8")

        with col2:
            if st.session_state.resume_data["image_base64"]:
                st.image(
                    f"data:image/png;base64,{st.session_state.resume_data['image_base64']}", width=150)
                if st.button("Remove Photo"):
                    st.session_state.resume_data["image_base64"] = None
                    st.experimental_rerun()

        if st.button("Continue to Education →", key="to_education"):
            st.session_state.current_page = "Education"
            st.experimental_rerun()

# Education Page
elif st.session_state.current_page == "Education":
    st.markdown("## 🎓 Education")
    st.markdown("Add your academic qualifications")

    if "education_entries" not in st.session_state:
        if st.session_state.resume_data["education"]:
            st.session_state.education_entries = st.session_state.resume_data["education"]
        else:
            st.session_state.education_entries = [{}]

    for i, edu in enumerate(st.session_state.education_entries):
        with st.expander(f"Education #{i+1}", expanded=True if i == 0 else False):
            col1, col2 = st.columns(2)
            with col1:
                degree = st.text_input(f"Degree/Certificate", key=f"degree_{i}",
                                       value=edu.get("degree", ""))
                year = st.text_input(f"Year", key=f"year_{i}",
                                     value=edu.get("year", ""))
            with col2:
                school = st.text_input(f"Institution Name", key=f"school_{i}",
                                       value=edu.get("school", ""))
                location = st.text_input(f"Location (Optional)", key=f"edu_loc_{i}",
                                         value=edu.get("location", ""))

            gpa = st.text_input(f"GPA (Optional)", key=f"gpa_{i}",
                                value=edu.get("gpa", ""))

            st.session_state.education_entries[i] = {
                "degree": degree, "school": school,
                "year": year, "location": location, "gpa": gpa
            }

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("➕ Add Education"):
            st.session_state.education_entries.append({})
            st.experimental_rerun()

    with col2:
        if len(st.session_state.education_entries) > 1:
            if st.button("➖ Remove Last Entry"):
                st.session_state.education_entries.pop()
                st.experimental_rerun()

    st.session_state.resume_data["education"] = [
        edu for edu in st.session_state.education_entries
        if edu.get("degree") or edu.get("school")
    ]

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Basic Info", key="back_basic_info"):
            st.session_state.current_page = "Basic Info"
            st.experimental_rerun()
    with col2:
        if st.button("Continue to Experience →", key="to_experience"):
            st.session_state.current_page = "Experience"
            st.experimental_rerun()


# Experience Page
elif st.session_state.current_page == "Experience":
    st.markdown("## 💼 Work Experience")
    st.markdown("Add your relevant work experience")

    if "experience_entries" not in st.session_state:
        if st.session_state.resume_data["experience"]:
            st.session_state.experience_entries = st.session_state.resume_data["experience"]
        else:
            st.session_state.experience_entries = [{}]

    for i, job in enumerate(st.session_state.experience_entries):
        with st.expander(f"Job #{i+1}", expanded=True if i == 0 else False):
            col1, col2 = st.columns(2)
            with col1:
                role = st.text_input(f"Job Title", key=f"role_{i}",
                                     value=job.get("role", ""))
                dates = st.text_input(f"Dates (e.g., Jan 2020 - Present)", key=f"dates_{i}",
                                      value=job.get("dates", ""))
            with col2:
                company = st.text_input(f"Company/Organization", key=f"company_{i}",
                                        value=job.get("company", ""))
                location = st.text_input(f"Location (Optional)", key=f"job_loc_{i}",
                                         value=job.get("location", ""))

            bullets_default = "\n".join(
                job.get("bullet_points", [])) if job.get("bullet_points") else ""
            bullets = st.text_area(
                f"Responsibilities & Achievements (one per line)", key=f"bullets_{i}",
                value=bullets_default,
                help="Focus on achievements with measurable results when possible"
            )

            ai_col1, ai_col2 = st.columns([3, 1])
            with ai_col2:
                if st.button("✨ Enhance Bullets with AI", key=f"enhance_btn_{i}"):
                    if bullets.strip():
                        with st.spinner("Enhancing bullet points..."):
                            context = f"Job role: {role}, Company: {company}" if role or company else None
                            enhanced_bullets = enhance_with_ai(
                                "bullet points", bullets, context)
                            bullets = enhanced_bullets
                            st.experimental_rerun()

            st.session_state.experience_entries[i] = {
                "role": role, "company": company,
                "dates": dates, "location": location,
                "bullet_points": bullets.strip().split("\n") if bullets.strip() else []
            }

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("➕ Add Job"):
            st.session_state.experience_entries.append({})
            st.experimental_rerun()

    with col2:
        if len(st.session_state.experience_entries) > 1:
            if st.button("➖ Remove Last Job"):
                st.session_state.experience_entries.pop()
                st.experimental_rerun()

    st.session_state.resume_data["experience"] = [
        job for job in st.session_state.experience_entries
        if job.get("role") or job.get("company")
    ]

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Education", key="edu_back"):
            st.session_state.current_page = "Education"
            st.experimental_rerun()
    with col2:
        if st.button("Continue to Projects →"):
            st.session_state.current_page = "Projects"
            st.experimental_rerun()

# Projects Page
elif st.session_state.current_page == "Projects":
    st.markdown("## 📌 Projects")
    st.markdown("Showcase your relevant projects")

    if "project_entries" not in st.session_state:
        if st.session_state.resume_data.get("projects_data"):
            st.session_state.project_entries = st.session_state.resume_data["projects_data"]
        else:
            st.session_state.project_entries = [{}]

    for i, proj in enumerate(st.session_state.project_entries):
        with st.expander(f"Project #{i+1}", expanded=True if i == 0 else False):
            title = st.text_input(f"Project Title", key=f"title_{i}",
                                  value=proj.get("title", ""))

            col1, col2 = st.columns(2)
            with col1:
                dates = st.text_input(f"Dates (Optional)", key=f"proj_dates_{i}",
                                      value=proj.get("dates", ""))
            with col2:
                link = st.text_input(f"Project Link (Optional)", key=f"link_{i}",
                                     value=proj.get("link", ""))

            desc = st.text_area(f"Description", key=f"desc_{i}",
                                value=proj.get("description", ""))

            # Get tech stack or skills used
            tech_stack = st.text_input(f"Technologies Used (comma-separated)", key=f"tech_{i}",
                                       value=proj.get("tech_stack", ""))

            ai_col1, ai_col2 = st.columns([3, 1])
            with ai_col2:
                if st.button("✨ Enhance Description with AI", key=f"enhance_proj_{i}"):
                    if desc.strip():
                        with st.spinner("Enhancing project description..."):
                            context = f"Project title: {title}, Technologies: {tech_stack}" if title or tech_stack else None
                            enhanced_desc = enhance_with_ai(
                                "project description", desc, context)
                            st.session_state.project_entries[i]["description"] = enhanced_desc
                            st.experimental_rerun()

            st.session_state.project_entries[i] = {
                "title": title, "description": desc,
                "link": link, "dates": dates,
                "tech_stack": tech_stack
            }

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("➕ Add Project"):
            st.session_state.project_entries.append({})
            st.experimental_rerun()

    with col2:
        if len(st.session_state.project_entries) > 1:
            if st.button("➖ Remove Last Project"):
                st.session_state.project_entries.pop()
                st.experimental_rerun()

    # Store formatted projects and raw data for later use
    st.session_state.resume_data["projects_data"] = [
        proj for proj in st.session_state.project_entries
        if proj.get("title")
    ]

    # Format projects for the template
    formatted_projects = []
    for p in st.session_state.project_entries:
        if p.get("title"):
            project_str = f"{p['title']}"
            if p.get("dates"):
                project_str += f" ({p['dates']})"
            if p.get("description"):
                project_str += f" - {p['description']}"
            if p.get("link"):
                project_str += f" [{p['link']}]"
            if p.get("tech_stack"):
                project_str += f" | Technologies: {p['tech_stack']}"
            formatted_projects.append(project_str)

    st.session_state.resume_data["projects"] = formatted_projects

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Experience"):
            st.session_state.current_page = "Experience"
            st.experimental_rerun()
    with col2:
        if st.button("Continue to Additional Info →"):
            st.session_state.current_page = "Additional Info"
            st.experimental_rerun()

# Additional Info Page
elif st.session_state.current_page == "Additional Info":
    st.markdown("## 🌟 Additional Information")

    # Create tabs for different sections
    tabs = st.tabs(["Skills", "Certifications", "Languages",
                   "Interests", "Social Profiles"])

    # Skills Tab
    with tabs[0]:
        st.markdown("### 🛠️ Skills")
        st.markdown("List your technical, soft, and other relevant skills")

        # Check if we should display existing skills
        existing_skills = ", ".join(
            st.session_state.resume_data["skills"]) if st.session_state.resume_data["skills"] else ""

        skills_input = st.text_area(
            "Enter your skills (comma-separated)",
            value=existing_skills,
            height=100,
            help="Example: Python, Data Analysis, Project Management, Communication"
        )

        ai_col1, ai_col2 = st.columns([3, 1])
        with ai_col2:
            if st.button("✨ Enhance Skills with AI"):
                if skills_input.strip():
                    with st.spinner("Optimizing skills..."):
                        context = f"Target job: {st.session_state.resume_data['role']}" if st.session_state.resume_data[
                            "role"] else None
                        enhanced_skills = enhance_with_ai(
                            "skills list", skills_input, context)
                        skills_input = enhanced_skills
                        st.experimental_rerun()

        if skills_input:
            skill_list = [s.strip()
                          for s in skills_input.split(",") if s.strip()]
            st.session_state.resume_data["skills"] = skill_list

            # Display skills as tags
            if skill_list:
                st.markdown("#### Your Skills:")
                skills_html = ""
                for skill in skill_list:
                    skills_html += f'<span style="background-color: #e3f2fd; padding: 5px 10px; border-radius: 15px; margin-right: 5px; margin-bottom: 5px; display: inline-block; font-size: 0.85rem;">{skill}</span>'
                st.markdown(skills_html, unsafe_allow_html=True)

    # Certifications Tab
    with tabs[1]:
        st.markdown("### 📚 Certifications & Courses")

        existing_certs = "\n".join(
            st.session_state.resume_data["certifications"]) if st.session_state.resume_data["certifications"] else ""

        certs_input = st.text_area(
            "Add certifications or courses (one per line)",
            value=existing_certs,
            height=100,
            help="Include certification name, issuing organization, and date (if relevant)"
        )

        if certs_input:
            cert_list = [c.strip()
                         for c in certs_input.strip().split("\n") if c.strip()]
            st.session_state.resume_data["certifications"] = cert_list

    # Languages Tab
    with tabs[2]:
        st.markdown("### 🌐 Languages")

        existing_langs = ", ".join(
            st.session_state.resume_data["languages"]) if st.session_state.resume_data["languages"] else ""

        languages_input = st.text_input(
            "Languages you speak (comma-separated)",
            value=existing_langs,
            help="Example: English (Native), Spanish (Fluent), French (Basic)"
        )

        if languages_input:
            lang_list = [lang.strip()
                         for lang in languages_input.split(",") if lang.strip()]
            st.session_state.resume_data["languages"] = lang_list

    # Interests Tab
    with tabs[3]:
        st.markdown("### 🎯 Interests & Hobbies")

        existing_hobbies = ", ".join(
            st.session_state.resume_data["hobbies"]) if st.session_state.resume_data["hobbies"] else ""

        hobbies_input = st.text_input(
            "Your interests and hobbies (comma-separated)",
            value=existing_hobbies,
            help="Example: Photography, Basketball, Chess, Reading"
        )

        if hobbies_input:
            hobby_list = [h.strip()
                          for h in hobbies_input.split(",") if h.strip()]
            st.session_state.resume_data["hobbies"] = hobby_list

    # Social Profiles Tab
    with tabs[4]:
        st.markdown("### 🔗 Social & Professional Profiles")

        existing_socials = "\n".join(
            st.session_state.resume_data["socials"]) if st.session_state.resume_data["socials"] else ""

        social_input = st.text_area(
            "Add social and professional profile links (one per line)",
            value=existing_socials,
            height=100,
            help="Example: LinkedIn: linkedin.com/in/yourname, GitHub: github.com/username"
        )

        if social_input:
            social_list = [s.strip()
                           for s in social_input.strip().split("\n") if s.strip()]
            st.session_state.resume_data["socials"] = social_list

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Projects"):
            st.session_state.current_page = "Projects"
            st.experimental_rerun()
    with col2:
        if st.button("Continue to Styling →"):
            st.session_state.current_page = "Styling"
            st.experimental_rerun()

# Styling Page
if st.session_state.get("current_page") == "Styling":
    st.markdown("## 🎨 Resume Styling")
    st.markdown("Preview templates and customize your style.")

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("### 🖼️ Template Previews")

        if "selected_template" not in st.session_state:
            st.session_state.selected_template = "minimal.html"

        preview_data = {
            "name": "John Doe",
            "role": "Software Engineer",
            "summary": "Passionate developer with 5+ years of experience in Python and web development.",
            "location": "San Francisco, CA",
            "email": "john.doe@example.com",
            "phone": "(123) 456-7890",
            "experience": [{"role": "Developer", "company": "Tech Co", "dates": "2020 - Present", "bullet_points": ["Developed cool features"]}],
            "education": [{"degree": "BSc Computer Science", "school": "ABC University", "year": "2018"}],
            "skills": ["Python", "React", "SQL"]
        }

        templates = [
            ("minimal.html", "Minimal"),
            ("creative.html", "Creative"),
            ("professional.html", "Professional"),
            ("modern.html", "Modern")
        ]

        preview_cols = st.columns(2)
        for i, (tpl, name) in enumerate(templates):
            with preview_cols[i % 2]:
                try:
                    html = render_resume(preview_data, tpl)
                    st.components.v1.html(f"<div style='border:1px solid #ccc; border-radius:5px; padding:10px;'>{html}</div>", height=300)
                except Exception as e:
                    st.error(f"Error loading {tpl}: {e}")
                if st.button(f"Use {name} Template", key=f"select_{tpl}"):
                    st.session_state.selected_template = tpl
                if st.session_state.selected_template == tpl:
                    st.markdown(f"✅ *Currently selected: {name}*")

    with col_right:
        st.markdown("### 🎨 Style Options")

        color_options = {
            "blue": "#1976d2",
            "green": "#388e3c",
            "purple": "#7b1fa2",
            "red": "#d32f2f",
            "gray": "#455a64"
        }
        if "color_scheme" not in st.session_state:
            st.session_state.color_scheme = "blue"
        st.session_state.color_scheme = st.radio("Primary Color", list(color_options.keys()),
                                                 index=list(color_options.keys()).index(st.session_state.color_scheme))
        st.markdown(f"<div style='background-color: {color_options[st.session_state.color_scheme]}; height: 30px; border-radius: 5px;'></div>", unsafe_allow_html=True)

        font_options = ["Arial", "Georgia", "Roboto", "Lato", "Open Sans", "Montserrat"]
        if "selected_font" not in st.session_state:
            st.session_state.selected_font = "Open Sans"
        st.session_state.selected_font = st.selectbox("Font Family", font_options,
                                                      index=font_options.index(st.session_state.selected_font))
        st.markdown(f"<p style='font-family:{st.session_state.selected_font}, sans-serif;'>Sample text in {st.session_state.selected_font}</p>", unsafe_allow_html=True)

        if "layout_compact" not in st.session_state:
            st.session_state.layout_compact = False
        st.session_state.layout_compact = st.checkbox("Use Compact Layout", value=st.session_state.layout_compact)

        if "include_photo" not in st.session_state:
            st.session_state.include_photo = True
        st.session_state.include_photo = st.checkbox("Include Profile Photo", value=st.session_state.include_photo)

    st.session_state.resume_data["styling"] = {
        "template": st.session_state.selected_template,
        "color": st.session_state.color_scheme,
        "font": st.session_state.selected_font,
        "compact": st.session_state.layout_compact,
        "include_photo": st.session_state.include_photo
    }

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Additional Info"):
            st.session_state.current_page = "Additional Info"
            st.rerun()
    with col2:
        if st.button("Continue to Preview & Download →"):
            st.session_state.current_page = "Preview & Download"
            st.rerun()

# Preview & Download Page
elif st.session_state.current_page == "Preview & Download":
    st.markdown("## 📄 Preview & Download Your Resume")
    
    # Prepare resume data for rendering
    resume_data = st.session_state.resume_data
    
    # Get selected template
    selected_template = st.session_state.selected_template if "selected_template" in st.session_state else "minimal.html"
    
    # Render the resume HTML
    try:
        resume_html = render_resume(resume_data, template=selected_template)
        
        # Show a preview of the resume
        st.markdown("### Resume Preview")
        
        # Create HTML component
        st.components.v1.html(
            f"""
            <div style="border:1px solid #ddd; padding:10px; border-radius:5px; max-width:800px; margin:0 auto;">
                {resume_html}
            </div>
            """,
            height=600,
            scrolling=True
        )
        
        # Generate PDF
        st.markdown("### Download Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🖨️ Generate PDF", key="gen_pdf"):
                with st.spinner("Generating PDF..."):
                    try:
                        # Save HTML to temporary file
                        with open("temp_resume.html", "w", encoding="utf-8") as f:
                            f.write(resume_html)
                        
                        # Convert to PDF
                        pdf_options = {
                            'page-size': 'Letter',
                            'margin-top': '0.5in',
                            'margin-right': '0.5in',
                            'margin-bottom': '0.5in',
                            'margin-left': '0.5in',
                            'encoding': "UTF-8",
                            'no-outline': None
                        }
                        
                        pdfkit.from_file("temp_resume.html", "resume.pdf", options=pdf_options, configuration=pdf_config)
                        
                        # Show download link
                        with open("resume.pdf", "rb") as pdf_file:
                            PDFbyte = pdf_file.read()
                            
                        st.download_button(
                            label="📥 Download PDF Resume",
                            data=PDFbyte,
                            file_name=f"{resume_data['name'].replace(' ', '_')}_Resume.pdf" if resume_data['name'] else "Your_Resume.pdf",
                            mime="application/pdf",
                            key="pdf_download"
                        )
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
                        st.info("If you're having trouble with PDF generation, you can save the HTML version instead.")
        
        with col2:
            # Add HTML download option
            if st.button("💾 Generate HTML", key="gen_html"):
                html_data = resume_html.encode()
                
                st.download_button(
                    label="📥 Download HTML Resume",
                    data=html_data,
                    file_name=f"{resume_data['name'].replace(' ', '_')}_Resume.html" if resume_data['name'] else "Your_Resume.html",
                    mime="text/html",
                    key="html_download"
                )
        
        # AI Enhancement for entire resume
        st.markdown("### 🔍 AI Resume Review")
        st.markdown("Get professional feedback on your resume")
        
        if st.button("✨ Get AI Resume Review"):
            with st.spinner("Analyzing your resume..."):
                try:
                    job_target = resume_data["role"] if resume_data["role"] else "the job you're applying for"
                    
                    # Create a simplified resume text for the AI to analyze
                    resume_text = f"""
                    Name: {resume_data["name"]}
                    Target Role: {resume_data["role"]}
                    Summary: {resume_data["summary"]}
                    
                    Experience:
                    {" ".join([f"{job.get('role')} at {job.get('company')} ({job.get('dates')})" for job in resume_data["experience"] if job.get('role')])}
                    
                    Education:
                    {" ".join([f"{edu.get('degree')} from {edu.get('school')} ({edu.get('year')})" for edu in resume_data["education"] if edu.get('degree')])}
                    
                    Skills:
                    {", ".join(resume_data["skills"])}
                    """
                    
                    response = co.chat(
                        message=f"Please review this resume for a {job_target} position and provide actionable feedback to improve it. Focus on content, formatting, and impact. Highlight 3 strengths and 3 areas for improvement. Keep your response concise and specific.\n\nResume:\n{resume_text}",
                        model="command-r",
                        temperature=0.7,
                        preamble="You are an expert resume consultant with years of experience in HR and recruiting. Provide valuable, constructive feedback for this resume."
                    )
                    
                    # Display the AI feedback
                    st.markdown("#### AI Resume Feedback")
                    st.markdown(response.text, unsafe_allow_html=True)
                    
                    # Add ATS compatibility score
                    ats_prompt = f"Based on this resume for a {job_target} position, give an ATS compatibility score from 1-10 and explain briefly why. Resume:\n{resume_text}"
                    ats_response = co.chat(
                        message=ats_prompt,
                        model="command-r",
                        temperature=0.5,
                        preamble="You are an ATS (Applicant Tracking System) expert. Provide a realistic compatibility score and brief explanation."
                    )
                    
                    st.markdown("#### ATS Compatibility")
                    st.markdown(ats_response.text, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Could not get AI feedback: {str(e)}")
                    st.info("AI review service is currently unavailable. Please try again later.")
    
    except Exception as e:
        st.error(f"Error rendering resume: {str(e)}")
        st.info("Please ensure you've completed all required fields in previous sections.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Styling"):
            st.session_state.current_page = "Styling"
            st.experimental_rerun()
    with col2:
        if st.button("✨ Start New Resume"):
            # Reset session state to create a new resume
            st.session_state.resume_data = {
                "name": "", "role": "", "summary": "",
                "location": "", "email": "", "phone": "", "website": "",
                "experience": [], "education": [],
                "skills": [], "certifications": [],
                "projects": [], "languages": [], "hobbies": [], "socials": [], "image_base64": None
            }
            if "education_entries" in st.session_state:
                del st.session_state.education_entries
            if "experience_entries" in st.session_state:
                del st.session_state.experience_entries
            if "project_entries" in st.session_state:
                del st.session_state.project_entries
                
            st.session_state.current_page = "Basic Info"
            st.experimental_rerun()

# Add footer
st.markdown("---")
st.markdown("### 💡 Resume Writing Tips")

# Use Cohere to get resume tips
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_resume_tips():
    try:
        if not os.getenv("COHERE_API_KEY"):
            return ["Customize your resume for each job application", 
                    "Quantify your achievements when possible",
                    "Keep your resume to 1-2 pages maximum"]
        
        response = co.chat(
            message="Provide 5 concise, effective resume writing tips that most job seekers don't know. Each tip should be one sentence.",
            model="command-r",
            temperature=0.7,
            preamble="You are a professional resume coach providing expert advice to job seekers."
        )
        
        # Extract tips as a list
        tips = response.text.strip().split("\n")
        tips = [tip.replace("- ", "").strip() for tip in tips if tip.strip()]
        
        # Ensure we have at least 3 tips
        if len(tips) < 3:
            tips.extend(["Customize your resume for each job application", 
                        "Quantify your achievements when possible",
                        "Keep your resume to 1-2 pages maximum"][:3-len(tips)])
        
        return tips[:5]  # Return max 5 tips
    except Exception:
        return ["Customize your resume for each job application", 
                "Quantify your achievements when possible",
                "Keep your resume to 1-2 pages maximum"]

# Display tips
tips = get_resume_tips()
tip_cols = st.columns(len(tips))

for i, tip in enumerate(tips):
    with tip_cols[i]:
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; height: 100%;">
            <div style="font-weight: bold; color: #4CAF50;">Tip #{i+1}</div>
            <div>{tip}</div>
        </div>
        """, unsafe_allow_html=True)

# Final footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666;">
        Created with ❤️ and AI | AI Resume Generator
    </div>
    """, 
    unsafe_allow_html=True
)