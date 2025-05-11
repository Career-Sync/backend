"""
Application routes for the CareerSync API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo import MongoClient, DESCENDING
import os
from bson import ObjectId
from datetime import datetime

from models.application import Application
from models.user import User
from models.job import Job
from services.job_matcher import analyze_resume_job_match

# Create a blueprint for application routes
applications_bp = Blueprint('applications', __name__)

# MongoDB connection
mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
client = MongoClient(mongo_uri)
db = client['careersync']
applications_collection = db['applications']
users_collection = db['users']
jobs_collection = db['jobs']

@applications_bp.route('/apply', methods=['POST'])
@jwt_required()
def apply_for_job():
    """
    Apply for a job
    """
    data = request.get_json()
    
    # Check if job_id is provided
    if 'job_id' not in data:
        return jsonify({"error": "Job ID is required"}), 400
    
    job_id = data['job_id']
    
    # Get current user's email from JWT
    current_user_email = get_jwt_identity()
    
    # Find user by email
    user_data = users_collection.find_one({"email": current_user_email})
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    
    user = User.from_dict(user_data)
    
    # Check if user is a job seeker
    if user.user_type != 'job_seeker':
        return jsonify({"error": "Only job seekers can apply for jobs"}), 403
    
    # Check if user has a resume
    if not user.resume_url:
        return jsonify({"error": "Please upload a resume before applying"}), 400
    
    # Check if job exists
    try:
        job_id_obj = ObjectId(job_id)
        job_data = jobs_collection.find_one({"_id": job_id_obj})
        
        if not job_data:
            return jsonify({"error": "Job not found"}), 404
        
        job = Job.from_dict(job_data)
        
        # Check if user has already applied for this job
        existing_application = applications_collection.find_one({
            "user_id": user._id,
            "job_id": job_id_obj
        })
        
        if existing_application:
            return jsonify({"error": "You have already applied for this job"}), 409
        
        # Analyze resume match (simplified - in real app, extract from actual resume)
        resume_text = "Experienced software developer with skills in Python, JavaScript, React, and MongoDB."
        analysis = analyze_resume_job_match(resume_text, job_id_obj)
        
        # Create application
        application = Application(
            user_id=user._id,
            job_id=job_id_obj,
            resume_url=user.resume_url,
            alignment_score=analysis['match_score'] if analysis else None,
            missing_keywords=analysis['missing_skills'] if analysis else None
        )
        
        # Insert application into the database
        applications_collection.insert_one(application.to_dict())
        
        # Return success response
        return jsonify({
            "message": "Application submitted successfully",
            "application": application.to_json(),
            "job": job.to_json(),
            "analysis": analysis
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@applications_bp.route('/', methods=['GET'])
@jwt_required()
def get_user_applications():
    """
    Get applications for the current user
    """
    # Get current user's email from JWT
    current_user_email = get_jwt_identity()
    
    # Find user by email
    user_data = users_collection.find_one({"email": current_user_email})
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    
    user = User.from_dict(user_data)
    
    # Get pagination parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    # Calculate skip value for pagination
    skip = (page - 1) * per_page
    
    # Get applications for the user with pagination
    try:
        # Get total count for pagination
        total_count = applications_collection.count_documents({"user_id": user._id})
        
        # Get applications with pagination
        applications_cursor = applications_collection.find({"user_id": user._id}) \
            .sort('applied_at', DESCENDING) \
            .skip(skip) \
            .limit(per_page)
        
        # Convert cursor to list of applications with job details
        applications = []
        for app_data in applications_cursor:
            app = Application.from_dict(app_data)
            
            # Get job details
            job_data = jobs_collection.find_one({"_id": app.job_id})
            job = Job.from_dict(job_data) if job_data else None
            
            # Add application with job details
            app_json = app.to_json()
            app_json['job'] = job.to_json() if job else None
            
            applications.append(app_json)
        
        # Return applications with pagination info
        return jsonify({
            "applications": applications,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": (total_count + per_page - 1) // per_page
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@applications_bp.route('/<application_id>', methods=['GET'])
@jwt_required()
def get_application(application_id):
    """
    Get application details by ID
    """
    # Get current user's email from JWT
    current_user_email = get_jwt_identity()
    
    # Find user by email
    user_data = users_collection.find_one({"email": current_user_email})
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    
    user = User.from_dict(user_data)
    
    try:
        # Find application by ID
        app_id_obj = ObjectId(application_id)
        app_data = applications_collection.find_one({"_id": app_id_obj})
        
        if not app_data:
            return jsonify({"error": "Application not found"}), 404
        
        app = Application.from_dict(app_data)
        
        # Check if user is authorized to view this application
        if user.user_type == 'job_seeker' and app.user_id != user._id:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Get job details
        job_data = jobs_collection.find_one({"_id": app.job_id})
        job = Job.from_dict(job_data) if job_data else None
        
        # Get user details (if recruiter)
        applicant_data = None
        if user.user_type == 'recruiter':
            applicant_data = users_collection.find_one({"_id": app.user_id})
        
        # Add details to application
        app_json = app.to_json()
        app_json['job'] = job.to_json() if job else None
        
        if applicant_data:
            applicant = User.from_dict(applicant_data)
            app_json['applicant'] = applicant.to_json()
        
        # Return application details
        return jsonify({
            "application": app_json
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400 