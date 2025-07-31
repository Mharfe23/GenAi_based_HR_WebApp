# AI Talent Scout

AI Talent Scout is a Streamlit-based web application designed to streamline the process of managing, searching, and analyzing candidate resumes using advanced LLMs (Large Language Models), MongoDB, MinIO, and vector search with ChromaDB. The app features resume extraction, semantic search, CSV export, and integration with the ELK stack for logging and analytics.

---

## Features

- **Resume Upload & Extraction**: Upload PDF resumes, extract structured candidate data using LLMs (Groq LLaMA 3.3 or local Ollama), and store them in MongoDB.
- **Semantic Skill Matching**: Uses ChromaDB and Google Generative AI embeddings to deduplicate and match skills, supporting fuzzy/semantic search.
- **Candidate Search & Chat**: Query the candidate database using natural language, with LLMs generating MongoDB queries for flexible search.
- **CSV Export**: View and export candidate summaries as CSV.
- **Resume Library**: Browse, preview, and download all uploaded resumes.
- **MinIO Integration**: Store and retrieve PDF files securely.
- **ELK Stack Logging**: All app logs are shipped to Logstash/Elasticsearch for monitoring and analytics.
- **Skill Dictionary Management**: Centralized and extensible skill set, with automatic deduplication and similarity matching.

---

## Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **Backend**: Python 3.12
- **Database**: MongoDB
- **Object Storage**: MinIO
- **Vector Search**: ChromaDB + Google Generative AI Embeddings
- **LLMs**: Groq API (LLaMA 3.3), Ollama (local)
- **Logging/Monitoring**: ELK Stack (Elasticsearch, Logstash, Kibana)


![Frontend App Structure](./static/Global_architecture.png)  
*AI Talent Scout Global Architecture*

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.12 (for local development)
- MongoDB instance (local or cloud)
- API keys for Groq, Google Generative AI.

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
MINIO_ENDPOINT=localhost:9000
MINIO_ROOT_USER=your_minio_user
MINIO_ROOT_PASSWORD=your_minio_password
MONGO_ENDPOINT=mongodb://your_mongo_uri
GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key
CHROMA_GOOGLE_GENAI_API_KEY=your_google_genai_key
```

### Running with Docker Compose

```bash
docker-compose up --build
```

- The app will be available at [http://localhost:8501](http://localhost:8501)
- MinIO Console: [http://localhost:9001](http://localhost:9001)
- Kibana: [http://localhost:5601](http://localhost:5601)


## Usage

### Upload Resume
1. Navigate to the "Upload Page"
2. Select one or more PDF resumes
3. Choose your preferred LLM (Groq API or local Ollama)
4. The app will extract structured data and store it in MongoDB and MinIO
5. Skills are automatically deduplicated and matched using semantic search

### Chat Search
1. Go to the "Chat Page"
2. Select your preferred LLM client
3. Ask questions in natural language, such as:
   - "Show me Python developers with 5+ years experience"
   - "Find candidates who know React and have worked with AWS"
   - "Who has experience in machine learning and data science?"
4. The LLM generates MongoDB queries and returns matching candidates
5. Download candidate resumes directly from the results

### CSV Export
1. Visit the "CSV Table" page
2. Search and filter candidates by name, email, role, or summary
3. View a comprehensive table of all candidates
4. Download the data as a CSV file for external analysis

### Resume Library
1. Access the "Resume Library" page
2. Browse all uploaded resumes with PDF preview
3. Search candidates by various criteria
4. Download individual resumes as needed



## Logging & Monitoring

The application uses the ELK stack for comprehensive logging and monitoring:

- **Logstash**: Receives logs on port 5000 and processes them
- **Elasticsearch**: Stores and indexes all application logs
- **Kibana**: Provides visualization and monitoring dashboard at [http://localhost:5601](http://localhost:5601)

All application events, including:
- Resume uploads and processing
- Skill matching
- Search queries and results
- Error handling and debugging

are logged and can be monitored through Kibana.

