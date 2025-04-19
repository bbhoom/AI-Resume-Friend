# AI Resume Builder

A sleek and intelligent AI-powered Resume Builder app built using **Streamlit**, **Python**, and **Cohere AI**. This app helps users generate clean, professional resumes by simply answering a few questions. It also enhances your input with AI to craft compelling resume content!

##  Features

- 🧠 **AI Enhancement** using [Cohere](https://cohere.com/) to rewrite and polish user inputs
- 🧾 Structured form-based entry for Education, Experience, Skills, and more
- 🎨 Beautiful HTML resume preview with option to **download as PDF**
- 🧲 Smart section arrangement and drag-and-drop reordering (optional extension)
- 🌈 Clean UI with Streamlit and CSS customization

---

##  Tech Stack

- **Frontend/UI:** Streamlit + Custom CSS
- **Backend:** Python
- **AI Text Enhancement:** [Cohere Generate API](https://docs.cohere.com/)
- **Template Rendering:** Jinja2
- **Export:** PDF and HTML using `pdfkit` 

---

##  Demo
![image](https://github.com/user-attachments/assets/bf28b6a4-874f-4107-b093-a90b0cf36857)


![image](https://github.com/user-attachments/assets/57ed2d67-8839-426d-88f2-5ac3ac0dc6f1)


![image](https://github.com/user-attachments/assets/92c8d116-e356-4d9f-a416-5e30b62aa2ec)



---

##  How to Run Locally

### 1. Clone the repo

```bash
git clone https://github.com/your-username/ai-resume-builder.git
cd ai-resume-builder
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Cohere API key

Create a `.env` file and add:

```
COHERE_API_KEY=your_cohere_api_key
```

### 5. Run the app

```bash
streamlit run app.py
```

---


##  Requirements

- Python 3.8+
- Streamlit
- Cohere
- pdfkit / weasyprint

---


## 🌐 Live Demo

```
