"""
Job routes for the CareerSync API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo import MongoClient, DESCENDING
import os
from bson import ObjectId
from datetime import datetime

from models.job import Job
from models.user import User
from services.job_matcher import get_job_matches

# Create a blueprint for job routes
jobs_bp = Blueprint('jobs', __name__)

# MongoDB connection
mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
client = MongoClient(mongo_uri)
db = client['careersync']
jobs_collection = db['jobs']
users_collection = db['users']

@jobs_bp.route('/search', methods=['GET'])
def search_jobs():
    """
    Search for jobs with optional filters
    """
    # Get query parameters
    query = request.args.get('query', '')
    location = request.args.get('location', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    # Calculate skip value for pagination
    skip = (page - 1) * per_page
    
    # Build search filter
    search_filter = {}
    
    if query:
        # Search in title and description
        search_filter['$or'] = [
            {'title': {'$regex': query, '$options': 'i'}},
            {'description': {'$regex': query, '$options': 'i'}}
        ]
    
    if location:
        # Search in location
        search_filter['location'] = {'$regex': location, '$options': 'i'}
    
    # Get total count for pagination
    total_count = jobs_collection.count_documents(search_filter)
    
    # Get jobs with pagination
    jobs_cursor = jobs_collection.find(search_filter) \
        .sort('posted_at', DESCENDING) \
        .skip(skip) \
        .limit(per_page)
    
    # Convert cursor to list of jobs
    jobs = []
    for job_data in jobs_cursor:
        job = Job.from_dict(job_data)
        jobs.append(job.to_json())
    
    # Return jobs with pagination info
    return jsonify({
        "jobs": jobs,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_count": total_count,
            "total_pages": (total_count + per_page - 1) // per_page
        }
    }), 200

@jobs_bp.route('/suggested', methods=['GET'])
@jwt_required()
def suggested_jobs():
    """
    Get AI-matched jobs for the current user
    """
    # Get current user's email from JWT
    current_user_email = get_jwt_identity()
    
    # Find user by email
    user_data = users_collection.find_one({"email": current_user_email})
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    
    user = User.from_dict(user_data)
    
    # Check if user is a job seeker
    if user.user_type != 'job_seeker':
        return jsonify({"error": "Only job seekers can access suggested jobs"}), 403
    
    # Get pagination parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    # Get job matches for the user (from matching service)
    matched_jobs = get_job_matches(user, page, per_page)
    
    # Return matched jobs
    return jsonify({
        "jobs": matched_jobs['jobs'],
        "pagination": matched_jobs['pagination']
    }), 200

@jobs_bp.route('/<job_id>', methods=['GET'])
def get_job(job_id):
    """
    Get job details by ID
    """
    try:
        # Find job by ID
        job_data = jobs_collection.find_one({"_id": ObjectId(job_id)})
        if not job_data:
            return jsonify({"error": "Job not found"}), 404
        
        job = Job.from_dict(job_data)
        
        # Return job details
        return jsonify({
            "job": job.to_json()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400 