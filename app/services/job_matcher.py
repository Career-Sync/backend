"""
Job matching service using NLP techniques
"""
import os
from pymongo import MongoClient, DESCENDING
import spacy
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from models.job import Job

# MongoDB connection
mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
client = MongoClient(mongo_uri)
db = client['careersync']
jobs_collection = db['jobs']

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

def calculate_skill_match_score(user_skills, job_skills):
    """
    Calculate match score based on skills overlap
    """
    if not user_skills or not job_skills:
        return 0
    
    # Convert to lowercase for better matching
    user_skills_lower = [skill.lower() for skill in user_skills]
    job_skills_lower = [skill.lower() for skill in job_skills]
    
    # Find matching skills
    matching_skills = set(user_skills_lower).intersection(set(job_skills_lower))
    
    # Calculate score as percentage of job skills matched
    if job_skills:
        return (len(matching_skills) / len(job_skills_lower)) * 100
    return 0

def get_missing_skills(user_skills, job_skills):
    """
    Identify skills in the job that the user is missing
    """
    if not user_skills or not job_skills:
        return job_skills
    
    # Convert to lowercase for better matching
    user_skills_lower = [skill.lower() for skill in user_skills]
    job_skills_lower = [skill.lower() for skill in job_skills]
    
    # Find missing skills
    missing_skills = [skill for skill in job_skills_lower if skill.lower() not in user_skills_lower]
    
    return missing_skills

def calculate_role_match_score(user_preferred_roles, job_title):
    """
    Calculate match score based on preferred roles
    """
    if not user_preferred_roles or not job_title:
        return 0
    
    # Convert to lowercase for better matching
    job_title_lower = job_title.lower()
    
    # Check if any preferred role appears in the job title
    for role in user_preferred_roles:
        if role.lower() in job_title_lower:
            return 100  # Full match if preferred role is in title
    
    # No direct match found
    return 0

def calculate_location_match_score(user_location, job_location):
    """
    Calculate match score based on location
    """
    if not user_location or not job_location:
        return 0
    
    # Convert to lowercase for better matching
    user_location_lower = user_location.lower()
    job_location_lower = job_location.lower()
    
    # Check for exact match or remote
    if 'remote' in job_location_lower:
        return 100  # Remote jobs are good for everyone
    
    if user_location_lower in job_location_lower or job_location_lower in user_location_lower:
        return 100  # Location matches
    
    # No match found
    return 0

def get_job_matches(user, page=1, per_page=10):
    """
    Get job matches for a user using scoring algorithms
    """
    # Calculate skip value for pagination
    skip = (page - 1) * per_page
    
    # Get all jobs
    jobs_cursor = jobs_collection.find().sort('posted_at', DESCENDING)
    
    # Calculate match scores for each job
    scored_jobs = []
    for job_data in jobs_cursor:
        job = Job.from_dict(job_data)
        
        # Calculate different match scores
        skill_score = calculate_skill_match_score(user.skills, job.skills_required)
        role_score = calculate_role_match_score(user.preferred_roles, job.title)
        location_score = calculate_location_match_score(user.location, job.location)
        
        # Calculate overall match score (weighted average)
        overall_score = (skill_score * 0.6) + (role_score * 0.3) + (location_score * 0.1)
        
        # Get missing skills
        missing_skills = get_missing_skills(user.skills, job.skills_required)
        
        # Add job with score to list
        job_json = job.to_json()
        job_json['match_score'] = round(overall_score, 2)
        job_json['missing_skills'] = missing_skills
        
        scored_jobs.append(job_json)
    
    # Sort by match score (descending)
    scored_jobs.sort(key=lambda x: x['match_score'], reverse=True)
    
    # Apply pagination
    paginated_jobs = scored_jobs[skip:skip + per_page]
    
    # Return jobs with pagination info
    return {
        "jobs": paginated_jobs,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_count": len(scored_jobs),
            "total_pages": (len(scored_jobs) + per_page - 1) // per_page
        }
    }

def analyze_resume_job_match(resume_text, job_id):
    """
    Analyze how well a resume matches a specific job
    """
    # Find job by ID
    job_data = jobs_collection.find_one({"_id": job_id})
    if not job_data:
        return None
    
    job = Job.from_dict(job_data)
    
    # Extract skills from resume text using spaCy
    resume_doc = nlp(resume_text)
    
    # Get skills mentioned in resume (simplified approach)
    resume_text_lower = resume_text.lower()
    found_skills = []
    
    # Common tech skills to look for
    tech_skills = [
        "python", "javascript", "java", "c++", "c#", "ruby", "php", "swift",
        "kotlin", "go", "rust", "typescript", "react", "angular", "vue",
        "node.js", "django", "flask", "spring", "express", "mongodb",
        "postgresql", "mysql", "redis", "aws", "azure", "gcp", "docker",
        "kubernetes", "jenkins", "git", "agile", "scrum", "machine learning",
        "data science", "artificial intelligence", "devops", "ci/cd"
    ]
    
    for skill in tech_skills:
        if skill in resume_text_lower:
            found_skills.append(skill)
    
    # Calculate skill match score
    skill_score = calculate_skill_match_score(found_skills, job.skills_required)
    
    # Get missing skills
    missing_skills = get_missing_skills(found_skills, job.skills_required)
    
    # Use TF-IDF to calculate content similarity
    if job.description and resume_text:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([resume_text, job.description])
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        content_score = cosine_sim * 100
    else:
        content_score = 0
    
    # Calculate overall match score
    overall_score = (skill_score * 0.7) + (content_score * 0.3)
    
    # Return analysis results
    return {
        "match_score": round(overall_score, 2),
        "skill_score": round(skill_score, 2),
        "content_score": round(content_score, 2),
        "missing_skills": missing_skills,
        "identified_skills": found_skills
    } 