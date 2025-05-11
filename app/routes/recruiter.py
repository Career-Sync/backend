"""
Recruiter routes for the CareerSync API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo import MongoClient, DESCENDING
import os
from bson import ObjectId
from datetime import datetime

from models.job import Job
from models.user import User
from models.application import Application

# Create a blueprint for recruiter routes
recruiter_bp = Blueprint('recruiter', __name__)

# MongoDB connection
mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
client = MongoClient(mongo_uri)
db = client['careersync']
jobs_collection = db['jobs']
users_collection = db['users']
applications_collection = db['applications']

@recruiter_bp.route('/jobs', methods=['POST'])
@jwt_required()
def create_job():
    """
    Create a new job posting (recruiter only)
    """
    # Get current user's email from JWT
    current_user_email = get_jwt_identity()
    
    # Find user by email
    user_data = users_collection.find_one({"email": current_user_email})
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    
    user = User.from_dict(user_data)
    
    # Check if user is a recruiter
    if user.user_type != 'recruiter':
        return jsonify({"error": "Only recruiters can create job postings"}), 403
    
    data = request.get_json()
    
    # Check if required fields are present
    required_fields = ['title', 'company', 'description', 'location']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Generate a unique job_id_external
    job_id_external = f"manual_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Create job posting
    job = Job(
        title=data['title'],
        company=data['company'],
        description=data['description'],
        location=data['location'],
        source="Manual",
        apply_link=data.get('apply_link', ''),
        job_id_external=job_id_external,
        skills_required=data.get('skills_required', [])
    )
    
    # Insert job into the database
    jobs_collection.insert_one(job.to_dict())
    
    # Return success response
    return jsonify({
        "message": "Job posting created successfully",
        "job": job.to_json()
    }), 201

@recruiter_bp.route('/jobs', methods=['GET'])
@jwt_required()
def get_recruiter_jobs():
    """
    Get jobs posted by the recruiter
    """
    # Get current user's email from JWT
    current_user_email = get_jwt_identity()
    
    # Find user by email
    user_data = users_collection.find_one({"email": current_user_email})
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    
    user = User.from_dict(user_data)
    
    # Check if user is a recruiter
    if user.user_type != 'recruiter':
        return jsonify({"error": "Only recruiters can access this endpoint"}), 403
    
    # Get pagination parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    # Calculate skip value for pagination
    skip = (page - 1) * per_page
    
    # Get jobs posted by this recruiter
    try:
        # For simplicity, we're using company name to filter jobs
        # In a real app, you'd have a recruiter_id field in the job model
        
        # Get total count for pagination
        total_count = jobs_collection.count_documents({"company": user.name})
        
        # Get jobs with pagination
        jobs_cursor = jobs_collection.find({"company": user.name}) \
            .sort('posted_at', DESCENDING) \
            .skip(skip) \
            .limit(per_page)
        
        # Convert cursor to list of jobs
        jobs = []
        for job_data in jobs_cursor:
            job = Job.from_dict(job_data)
            
            # Get application count for this job
            app_count = applications_collection.count_documents({"job_id": job._id})
            
            # Add job with application count
            job_json = job.to_json()
            job_json['application_count'] = app_count
            
            jobs.append(job_json)
        
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
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@recruiter_bp.route('/candidates/<job_id>', methods=['GET'])
@jwt_required()
def get_job_candidates(job_id):
    """
    Get candidates who applied for a specific job
    """
    # Get current user's email from JWT
    current_user_email = get_jwt_identity()
    
    # Find user by email
    user_data = users_collection.find_one({"email": current_user_email})
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    
    user = User.from_dict(user_data)
    
    # Check if user is a recruiter
    if user.user_type != 'recruiter':
        return jsonify({"error": "Only recruiters can access this endpoint"}), 403
    
    try:
        # Find job by ID
        job_id_obj = ObjectId(job_id)
        job_data = jobs_collection.find_one({"_id": job_id_obj})
        
        if not job_data:
            return jsonify({"error": "Job not found"}), 404
        
        job = Job.from_dict(job_data)
        
        # Check if recruiter has permission to view this job's candidates
        # For simplicity, we're using company name
        if job.company != user.name:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Get sort parameter (by default, sort by alignment score)
        sort_by = request.args.get('sort', 'alignment_score')
        sort_direction = -1 if sort_by == 'alignment_score' else 1
        
        # Calculate skip value for pagination
        skip = (page - 1) * per_page
        
        # Get applications for this job
        total_count = applications_collection.count_documents({"job_id": job_id_obj})
        
        # Get applications with pagination and sorting
        applications_cursor = applications_collection.find({"job_id": job_id_obj}) \
            .sort(sort_by, sort_direction) \
            .skip(skip) \
            .limit(per_page)
        
        # Convert cursor to list of applications with applicant details
        candidates = []
        for app_data in applications_cursor:
            app = Application.from_dict(app_data)
            
            # Get applicant details
            applicant_data = users_collection.find_one({"_id": app.user_id})
            applicant = User.from_dict(applicant_data) if applicant_data else None
            
            # Add application with applicant details
            candidate = app.to_json()
            candidate['applicant'] = applicant.to_json() if applicant else None
            
            candidates.append(candidate)
        
        # Return candidates with pagination info
        return jsonify({
            "job": job.to_json(),
            "candidates": candidates,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": (total_count + per_page - 1) // per_page
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@recruiter_bp.route('/application/<application_id>/status', methods=['PUT'])
@jwt_required()
def update_application_status(application_id):
    """
    Update the status of an application
    """
    # Get current user's email from JWT
    current_user_email = get_jwt_identity()
    
    # Find user by email
    user_data = users_collection.find_one({"email": current_user_email})
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    
    user = User.from_dict(user_data)
    
    # Check if user is a recruiter
    if user.user_type != 'recruiter':
        return jsonify({"error": "Only recruiters can update application status"}), 403
    
    data = request.get_json()
    
    # Check if status is provided
    if 'status' not in data:
        return jsonify({"error": "Status is required"}), 400
    
    # Validate status
    valid_statuses = ['pending', 'viewed', 'rejected', 'shortlisted']
    if data['status'] not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400
    
    try:
        # Find application by ID
        app_id_obj = ObjectId(application_id)
        app_data = applications_collection.find_one({"_id": app_id_obj})
        
        if not app_data:
            return jsonify({"error": "Application not found"}), 404
        
        app = Application.from_dict(app_data)
        
        # Get job details to check permissions
        job_data = jobs_collection.find_one({"_id": app.job_id})
        
        if not job_data:
            return jsonify({"error": "Job not found"}), 404
        
        job = Job.from_dict(job_data)
        
        # Check if recruiter has permission to update this application
        # For simplicity, we're using company name
        if job.company != user.name:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Update application status
        applications_collection.update_one(
            {"_id": app_id_obj},
            {"$set": {"status": data['status']}}
        )
        
        # Get updated application
        updated_app_data = applications_collection.find_one({"_id": app_id_obj})
        updated_app = Application.from_dict(updated_app_data)
        
        # Return updated application
        return jsonify({
            "message": "Application status updated successfully",
            "application": updated_app.to_json()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400 