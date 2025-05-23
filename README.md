# CareerSync Backend

The backend component of the CareerSync platform, built with Flask and MongoDB. This API provides functionality for job matching, resume analysis, and application tracking.

## Features

- User authentication with JWT tokens
- Job listing and searching
- AI-powered resume analysis
- Job application management
- Recruiter tools for posting jobs and managing candidates
- Automated job fetching from external APIs

## Tech Stack

- **Framework**: Flask (Python)
- **Database**: MongoDB
- **Authentication**: JWT (JSON Web Tokens)
- **NLP/AI**: spaCy, scikit-learn (TF-IDF, cosine similarity)
- **Storage**: AWS S3 for resume storage
- **Job API Integration**: Adzuna, Arbeitnow, GitHub Jobs

## Getting Started

### Prerequisites

- Python 3.8 or higher
- MongoDB installed and running
- AWS S3 bucket (for resume storage)

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - On Windows: `venv\Scripts\activate`
   - On macOS/Linux: `source venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Install spaCy model:
   ```
   python -m spacy download en_core_web_sm
   ```
6. Create a `.env` file with your configuration (see `.env.example`)
7. Run the application:
   ```
   python app/app.py
   ```

### Setting up cron job

To automate job fetching, you can run:

```
python jobs_cron.py
```

This will start a scheduler that fetches jobs from external APIs every 6 hours.

## API Endpoints

### Authentication

- `POST /auth/signup` - Register a new user
- `POST /auth/login` - Login and receive JWT token
- `GET /auth/profile` - Get user profile
- `PUT /auth/profile` - Update user profile

### Jobs

- `GET /jobs/search` - Search for jobs with filters
- `GET /jobs/suggested` - Get AI-matched jobs for current user
- `GET /jobs/:id` - Get job details

### Applications

- `POST /applications/apply` - Apply for a job
- `GET /applications/` - Get user's applications
- `GET /applications/:id` - Get application details

### Resume

- `POST /resume/upload` - Upload a resume
- `POST /resume/analyze` - Analyze resume against a job

### Recruiter

- `POST /recruiter/jobs` - Create a job posting
- `GET /recruiter/jobs` - Get jobs posted by recruiter
- `GET /recruiter/candidates/:job_id` - Get candidates for a job
- `PUT /recruiter/application/:id/status` - Update application status #   b a c k e n d  
 