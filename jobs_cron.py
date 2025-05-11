"""
Jobs Cron Script
Fetches jobs from external APIs and updates the database every 6 hours.
"""
import os
import time
import requests
import spacy
import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

# Load environment variables
load_dotenv()

# Load spaCy model for skills extraction
nlp = spacy.load("en_core_web_sm")

# Connect to MongoDB
mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
client = MongoClient(mongo_uri)
db = client['careersync']
jobs_collection = db['jobs']

# API endpoints
API_ENDPOINTS = {
    'adzuna': {
        'url': 'https://api.adzuna.com/v1/api/jobs',
        'params': {
            'app_id': os.environ.get('ADZUNA_APP_ID'),
            'app_key': os.environ.get('ADZUNA_API_KEY'),
            'results_per_page': 50,
            'what': 'software developer',
            'location0': 'uk'
        }
    },
    'arbeitnow': {
        'url': 'https://www.arbeitnow.com/api/job-board-api',
        'params': {}
    },
    'github_jobs': {
        'url': 'https://jobs.github.com/positions.json',
        'params': {
            'description': 'developer',
            'location': ''
        }
    }
}

def extract_skills(job_description):
    """Extract skills from job description using spaCy NER."""
    # Common tech skills to look for
    tech_skills = [
        "python", "javascript", "java", "c++", "c#", "ruby", "php", "swift",
        "kotlin", "go", "rust", "typescript", "react", "angular", "vue",
        "node.js", "django", "flask", "spring", "express", "mongodb",
        "postgresql", "mysql", "redis", "aws", "azure", "gcp", "docker",
        "kubernetes", "jenkins", "git", "agile", "scrum", "machine learning",
        "data science", "artificial intelligence", "devops", "ci/cd"
    ]
    
    # Convert job description to lowercase for better matching
    text_lower = job_description.lower()
    
    # Extract skills
    found_skills = []
    for skill in tech_skills:
        if skill in text_lower:
            found_skills.append(skill)
    
    return found_skills

def fetch_adzuna_jobs():
    """Fetch jobs from Adzuna API."""
    try:
        endpoint = API_ENDPOINTS['adzuna']
        response = requests.get(
            f"{endpoint['url']}/gb/search/1",
            params=endpoint['params']
        )
        
        if response.status_code == 200:
            jobs_data = response.json().get('results', [])
            processed_jobs = []
            
            for job in jobs_data:
                processed_job = {
                    "job_id_external": f"adzuna_{job.get('id')}",
                    "title": job.get('title'),
                    "company": job.get('company', {}).get('display_name', 'Unknown'),
                    "description": job.get('description'),
                    "location": job.get('location', {}).get('display_name', 'Unknown'),
                    "source": "Adzuna",
                    "apply_link": job.get('redirect_url'),
                    "posted_at": datetime.now(),
                    "skills_required": extract_skills(job.get('description', ''))
                }
                processed_jobs.append(processed_job)
            
            return processed_jobs
        else:
            print(f"Error fetching Adzuna jobs: {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception while fetching Adzuna jobs: {str(e)}")
        return []

def fetch_arbeitnow_jobs():
    """Fetch jobs from Arbeitnow API."""
    try:
        endpoint = API_ENDPOINTS['arbeitnow']
        response = requests.get(endpoint['url'], params=endpoint['params'])
        
        if response.status_code == 200:
            jobs_data = response.json().get('data', [])
            processed_jobs = []
            
            for job in jobs_data:
                processed_job = {
                    "job_id_external": f"arbeitnow_{job.get('slug')}",
                    "title": job.get('title'),
                    "company": job.get('company_name', 'Unknown'),
                    "description": job.get('description'),
                    "location": job.get('location', 'Unknown'),
                    "source": "Arbeitnow",
                    "apply_link": job.get('url'),
                    "posted_at": datetime.now(),
                    "skills_required": extract_skills(job.get('description', ''))
                }
                processed_jobs.append(processed_job)
            
            return processed_jobs
        else:
            print(f"Error fetching Arbeitnow jobs: {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception while fetching Arbeitnow jobs: {str(e)}")
        return []

def fetch_github_jobs():
    """Fetch jobs from GitHub Jobs API."""
    try:
        endpoint = API_ENDPOINTS['github_jobs']
        response = requests.get(endpoint['url'], params=endpoint['params'])
        
        if response.status_code == 200:
            jobs_data = response.json()
            processed_jobs = []
            
            for job in jobs_data:
                processed_job = {
                    "job_id_external": f"github_{job.get('id')}",
                    "title": job.get('title'),
                    "company": job.get('company', 'Unknown'),
                    "description": job.get('description'),
                    "location": job.get('location', 'Remote'),
                    "source": "GitHub Jobs",
                    "apply_link": job.get('url'),
                    "posted_at": datetime.now(),
                    "skills_required": extract_skills(job.get('description', ''))
                }
                processed_jobs.append(processed_job)
            
            return processed_jobs
        else:
            print(f"Error fetching GitHub jobs: {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception while fetching GitHub jobs: {str(e)}")
        return []

def update_jobs_database():
    """Fetch jobs from all sources and update the database."""
    print(f"[{datetime.now()}] Starting job fetch...")
    
    # Fetch jobs from all sources
    all_jobs = []
    all_jobs.extend(fetch_adzuna_jobs())
    all_jobs.extend(fetch_arbeitnow_jobs())
    all_jobs.extend(fetch_github_jobs())
    
    # Insert or update jobs in MongoDB
    for job in all_jobs:
        jobs_collection.update_one(
            {"job_id_external": job["job_id_external"]},
            {"$set": job},
            upsert=True
        )
    
    print(f"[{datetime.now()}] Job fetch completed. {len(all_jobs)} jobs processed.")

def main():
    """Run the job scheduler."""
    scheduler = BlockingScheduler()
    
    # Schedule job to run every 6 hours
    scheduler.add_job(update_jobs_database, 'interval', hours=6)
    
    # Run once immediately on startup
    update_jobs_database()
    
    print("Job scheduler started. Jobs will be fetched every 6 hours.")
    scheduler.start()

if __name__ == "__main__":
    main() 