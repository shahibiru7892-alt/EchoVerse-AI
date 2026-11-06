# EchoVerse AI – Smart Entertainment Chatbot

## 1. Introduction

EchoVerse AI is an intelligent entertainment chatbot powered by Large Language Models (LLMs). It provides natural and interactive conversations using Groq AI.

The chatbot is designed to assist users with gaming, anime, movies, music, technology, storytelling, and general entertainment.

## 2. Features

* AI-powered conversational chatbot.
* Natural language interaction.
* Gaming and entertainment recommendations.
* Creative storytelling.
* Custom AI personality.
* Conversation history using SQLite.
* Reset conversation functionality.
* Input validation and basic guardrails.
* REST API using FastAPI.
* Docker containerization.

## 3. Technologies Used

| Technology  | Purpose                      |
| ----------- | ---------------------------- |
| Python      | Backend programming          |
| Groq API    | AI response generation       |
| Llama Model | Language model               |
| SQLite      | Conversation storage         |
| FastAPI     | REST API development         |
| Streamlit   | UI framework dependency      |
| Docker      | Application containerization |
| Uvicorn     | API server                   |
| Git         | Version control              |

## 4. Project Structure

```text
EchoVerse-AI/
│
├── config/
│   └── settings.py
│
├── database/
│   ├── __init__.py
│   ├── db.py
│   └── echoverse.db
│
├── assets/
├── tests/
│
├── internal_api/
│   ├── __init__.py
│   └── server.py
│
├── app.py
├── chatbot.py
├── personality.py
├── guardrails.py
│
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── .dockerignore
├── Dockerfile
└── docker-compose.yml
```

## 5. Installation

### Step 1: Clone the project

```cmd
git clone YOUR_GITHUB_REPOSITORY_URL
```

### Step 2: Open the project folder

```cmd
cd EchoVerse-AI
```

### Step 3: Create virtual environment

```cmd
python -m venv echo_env
```

### Step 4: Activate environment

```cmd
echo_env\Scripts\activate.bat
```

### Step 5: Install dependencies

```cmd
python -m pip install -r requirements.txt
```

## 6. Environment Configuration

Create a `.env` file in the project root.

Add your Groq API credentials:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
```

Never upload your actual API key to GitHub.

## 7. Running the Application

### Command Line Application

```cmd
python app.py
```

### FastAPI Server

```cmd
python -m uvicorn internal_api.server:app --reload
```

Open the API documentation:

http://127.0.0.1:8000/docs

## 8. Docker Deployment

Build the Docker image:

```cmd
docker compose build
```

Start the application:

```cmd
docker compose up
```

Stop the application:

```cmd
docker compose down
```

## 9. Database

EchoVerse AI uses SQLite to store:

* Conversation information.
* User messages.
* AI-generated responses.
* Conversation timestamps.

## 10. Future Enhancements

* Modern graphical user interface.
* User authentication.
* Multiple conversation management.
* Voice-based interaction.
* Anime and movie recommendation system.
* Improved long-term conversational memory.
* Deployment to a cloud platform.

## 11. Conclusion

EchoVerse AI demonstrates the integration of Large Language Models, Python, database management, REST APIs, and Docker to develop an intelligent entertainment chatbot.
