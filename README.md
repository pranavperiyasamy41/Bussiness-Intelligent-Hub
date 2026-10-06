# 🚀 Business Intelligence Hub 🚀

[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Gemini AI](https://img.shields.io/badge/Gemini%20AI-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://aistudio.google.com/)
[![Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com/)

An intelligent, full-stack web application that transforms raw data files into interactive dashboards and conversational insights using Generative AI. This project turns a user into a data analyst by providing a suite of AI-powered tools.

<div align="center">

<!-- Simple Direct Link -->

<!-- The Friendly Warning Message -->

</div>


## ✨ Core Features

This application is divided into two main BI "engines," both powered by a hybrid AI architecture.

### 1. Customer Feedback Analyzer

* **File Upload:** Accepts `.pdf`, `.csv`, or `.xlsx` files containing raw customer feedback.
* **AI Summary:** Uses the Gemini AI to read the text and generate a concise summary of:
    * Overall Sentiment
    * Key Positive Themes
    * Areas for Improvement
* **Data Visualization:** Automatically generates a chart showing the distribution of positive, negative, and neutral feedback.

### 2. Retail Insight Engine

This is a multi-featured engine for analyzing structured (tabular) sales data.

* **💬 "Chat with Data" (RAG):**
    * A powerful, conversational chatbot that answers natural-language questions about your data.
    * **Multilingual:** Can understand and respond in mixed languages, including **Tanglish** (e.g., "Coimbatore-la sales evlo?").
    * **Safe & Hallucination-Proof:** Uses a "JSON-based RAG" architecture. The AI's job is to *only* translate a user's question into a safe JSON query, which is then executed by Python. This prevents AI hallucinations (like "39,975 customers") and code-injection attacks.
    * **User-Friendly:** The user does *not* need to know the exact column names. The AI is smart enough to find the correct columns or ask for clarification.

* **📊 "AI-Generated Dashboard"**
    * Acts as a "Senior Data Analyst" in a box.
    * The AI analyzes the file's schema and generates a JSON "plan" for 4-6 of the most insightful charts (e.g., "Sales by City," "Revenue by Category").
    * The frontend dynamically renders this plan into a full-page, PowerBI-style dashboard with a 2x2 grid of `line`, `bar`, and `pie` charts.

* **📈 "Sales Forecast Simulation"**
    * A true data science forecasting feature.
    * The AI intelligently identifies the date (`OrderMonth`, `OrderYear`) and sales (`Total Price`) columns from the user's file.
    * It pre-processes and resamples the data into monthly totals.
    * It trains a **SARIMA time-series model** to generate a 12-month sales forecast.
    * Displays the result in a beautiful chart showing "Historical vs. Forecasted" data, complete with a "cone of uncertainty."

### 3. Full-Stack Essentials

* **Full User Authentication:** Secure sign-up, login, and logout system.
* **File Management:** Users can only see and delete their own files.
* **Responsive Design:** A custom, professional "Deep Dive" dark theme built with Bootstrap 5.

---

## 🛠️ Tech Stack

* **Backend:** **Python**, **Django**
* **Database:** **PostgreSQL** (for production), **SQLite3** (for development)
* **AI:** **Google Gemini AI API** (`gemini-2.5-flash-lite`)
* **AI Architecture:** **RAG (Retrieval-Augmented Generation)**, specifically a JSON-based "Agent" for safe, structured data querying.
* **Data Science:** **Pandas** (for data manipulation), **Statsmodels (SARIMA)** (for forecasting), **PyMuPDF** (for PDF parsing)
* **Frontend:** **HTML5**, **Bootstrap 5**, **JavaScript**, **Chart.js**
* **Deployment:** **Render** (Web Service + PostgreSQL), **Gunicorn** (Web Server)
* **Version Control:** **Git** & **GitHub**

---

## 🏃 How to Run Locally

1.  **Clone the repository:**
    ```sh
    git clone [https://github.com/YourUsername/bi-hub-project.git](https://github.com/YourUsername/bi-hub-project.git)
    cd bi-hub-project
    ```

2.  **Create and activate a virtual environment:**
    ```sh
    python -m venv venv
    .\venv\Scripts\activate  # Windows
    source venv/bin/activate  # Mac/Linux
    ```

3.  **Install all required packages:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Create your secret `.env` file:**
    * Make a copy of `.env.example` and name it `.env`.
    * Open the `.env` file and add your `SECRET_KEY` and `GOOGLE_AI_API_KEY`.
    ```text
    # This is a template. Create a new file named .env
    # and paste your real keys inside the quotes.
    
    SECRET_KEY="YOUR_DJANGO_SECRET_KEY_HERE"
    GOOGLE_AI_API_KEY="YOUR_GOOGLE_AI_KEY_HERE"
    ENVIRONMENT="development"
    ```

5.  **Run database migrations:**
    ```sh
    python manage.py migrate
    ```

6.  **Create a superuser** (to access the `/admin` panel):
    ```sh
    python manage.py createsuperuser
    ```

7.  **Run the app!**
    ```sh
    python manage.py runserver
    ```
    Your app will be running at `http://127.0.0.1:8000/`.

---

## 👤 Author

* **Harinee S**
* [GitHub: @Harinee-3010](https://github.com/Harinee-3010)
