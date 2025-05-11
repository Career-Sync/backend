"""
Authentication routes for the CareerSync API
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os

from models.user import User

# Create a blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

# MongoDB connection
mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
client = MongoClient(mongo_uri)
db = client['careersync']
users_collection = db['users']

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Register a new user
    """
    data = request.get_json()
    
    # Check if required fields are present
    required_fields = ['name', 'email', 'password', 'user_type']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Check if user already exists
    if users_collection.find_one({"email": data['email']}):
        return jsonify({"error": "User with this email already exists"}), 409
    
    # Create a new user with hashed password
    user_data = {
        "name": data['name'],
        "email": data['email'],
        "password": generate_password_hash(data['password']),
        "user_type": data['user_type'],
        "skills": data.get('skills', []),
        "experience": data.get('experience'),
        "education": data.get('education'),
        "preferred_roles": data.get('preferred_roles', []),
        "location": data.get('location')
    }
    
    user = User.from_dict(user_data)
    
    # Insert user into the database
    users_collection.insert_one(user.to_dict())
    
    # Create access token
    access_token = create_access_token(identity=user.email)
    
    # Return user info and token
    return jsonify({
        "message": "User registered successfully",
        "user": user.to_json(),
        "access_token": access_token
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login an existing user
    """
    data = request.get_json()
    
    # Check if email and password are provided
    if not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400
    
    # Find user by email
    user_data = users_collection.find_one({"email": data['email']})
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    
    user = User.from_dict(user_data)
    
    # Check password
    if not check_password_hash(user.password, data['password']):
        return jsonify({"error": "Invalid password"}), 401
    
    # Create access token
    access_token = create_access_token(identity=user.email)
    
    # Return user info and token
    return jsonify({
        "message": "Login successful",
        "user": user.to_json(),
        "access_token": access_token
    }), 200

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    """
    Get user profile (requires authentication)
    """
    # Get current user's email from JWT
    current_user_email = get_jwt_identity()
    
    # Find user by email
    user_data = users_collection.find_one({"email": current_user_email})
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    
    user = User.from_dict(user_data)
    
    # Return user info
    return jsonify({
        "user": user.to_json()
    }), 200

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update user profile (requires authentication)
    """
    # Get current user's email from JWT
    current_user_email = get_jwt_identity()
    
    # Find user by email
    user_data = users_collection.find_one({"email": current_user_email})
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    
    # Fields that can be updated
    updatable_fields = [
        'name', 'skills', 'experience', 'education', 
        'preferred_roles', 'location', 'resume_url'
    ]
    
    # Create update dictionary
    update_data = {}
    for field in updatable_fields:
        if field in data:
            update_data[field] = data[field]
    
    # Update user in database
    if update_data:
        users_collection.update_one(
            {"email": current_user_email},
            {"$set": update_data}
        )
    
    # Get updated user data
    updated_user_data = users_collection.find_one({"email": current_user_email})
    user = User.from_dict(updated_user_data)
    
    # Return updated user info
    return jsonify({
        "message": "Profile updated successfully",
        "user": user.to_json()
    }), 200 