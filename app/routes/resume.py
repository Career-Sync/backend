"""
Resume analysis routes for the CareerSync API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo import MongoClient
import os
from bson import ObjectId
import uuid
import boto3
from werkzeug.utils import secure_filename
import tempfile

from models.user import User
from services.job_matcher import analyze_resume_job_match

# Create a blueprint for resume routes
resume_bp = Blueprint('resume', __name__)

# MongoDB connection
mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
client = MongoClient(mongo_uri)
db = client['careersync']
users_collection = db['users']
jobs_collection = db['jobs']

# S3 configuration
s3_bucket = os.environ.get('S3_BUCKET_NAME', 'careersync-resumes')
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'),
    region_name=os.environ.get('AWS_REGION', 'us-east-1')
)

def upload_file_to_s3(file, filename):
    """
    Upload a file to S3 bucket
    """
    try:
        s3_client.upload_fileobj(
            file,
            s3_bucket,
            filename,
            ExtraArgs={
                "ContentType": file.content_type
            }
        )
        
        # Generate URL
        url = f"https://{s3_bucket}.s3.amazonaws.com/{filename}"
        return url
    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")
        return None

def extract_text_from_resume(file):
    """
    Extract text from resume file
    Currently a placeholder - would normally use libraries like PyPDF2, docx2txt, etc.
    """
    # Simple implementation - assuming it's a text file
    # In a real app, you'd handle different file formats
    try:
        content = file.read()
        # Convert bytes to string if needed
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        return content
    except Exception as e:
        print(f"Error extracting text: {str(e)}")
        return ""

@resume_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_resume():
    """
    Upload a resume file
    """
    # Get current user's email from JWT
    current_user_email = get_jwt_identity()
    
    # Find user by email
    user_data = users_collection.find_one({"email": current_user_email})
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    
    # Check if a file was included
    if 'resume' not in request.files:
        return jsonify({"error": "No resume file provided"}), 400
    
    file = request.files['resume']
    
    # Check if file is empty
    if file.filename == '':
        return jsonify({"error": "No resume file selected"}), 400
    
    # Check file extension (only allow PDF, DOCX, DOC, TXT)
    allowed_extensions = {'pdf', 'docx', 'doc', 'txt'}
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    if file_ext not in allowed_extensions:
        return jsonify({"error": "File type not allowed. Please upload PDF, DOCX, DOC, or TXT file"}), 400
    
    # Generate a secure filename
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    
    # Upload to S3
    resume_url = upload_file_to_s3(file, unique_filename)
    
    if not resume_url:
        return jsonify({"error": "Failed to upload resume"}), 500
    
    # Update user's resume URL
    users_collection.update_one(
        {"email": current_user_email},
        {"$set": {"resume_url": resume_url}}
    )
    
    # Get updated user data
    updated_user_data = users_collection.find_one({"email": current_user_email})
    user = User.from_dict(updated_user_data)
    
    # Return success response
    return jsonify({
        "message": "Resume uploaded successfully",
        "resume_url": resume_url,
        "user": user.to_json()
    }), 200

@resume_bp.route('/analyze', methods=['POST'])
@jwt_required()
def analyze_resume():
    """
    Analyze resume for a specific job
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
    
    # Check if user has uploaded a resume
    if not user.resume_url:
        return jsonify({"error": "No resume found. Please upload a resume first."}), 400
    
    # Parse resume content - in a real app, you'd download from S3 and extract
    # For now, we'll simulate with a simple approach
    resume_text = "Experienced software developer with skills in Python, JavaScript, React, and MongoDB."
    
    # Analyze resume against job
    try:
        job_id_obj = ObjectId(job_id)
        analysis = analyze_resume_job_match(resume_text, job_id_obj)
        
        if not analysis:
            return jsonify({"error": "Job not found"}), 404
        
        # Return analysis results
        return jsonify({
            "analysis": analysis
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400 