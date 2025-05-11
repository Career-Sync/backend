"""
User Model for MongoDB
"""
from datetime import datetime
from bson import ObjectId

class User:
    """
    User model representing job seekers and recruiters
    """
    
    collection_name = 'users'
    
    def __init__(self, name, email, password, user_type, 
                 resume_url=None, skills=None, experience=None, 
                 education=None, preferred_roles=None, location=None, 
                 created_at=None, _id=None):
        self._id = _id or ObjectId()
        self.name = name
        self.email = email
        self.password = password  # Should be hashed before storing
        self.user_type = user_type  # 'job_seeker' or 'recruiter'
        self.resume_url = resume_url
        self.skills = skills or []
        self.experience = experience
        self.education = education
        self.preferred_roles = preferred_roles or []
        self.location = location
        self.created_at = created_at or datetime.now()
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a User instance from a dictionary
        """
        return cls(
            _id=data.get('_id'),
            name=data.get('name'),
            email=data.get('email'),
            password=data.get('password'),
            user_type=data.get('user_type'),
            resume_url=data.get('resume_url'),
            skills=data.get('skills'),
            experience=data.get('experience'),
            education=data.get('education'),
            preferred_roles=data.get('preferred_roles'),
            location=data.get('location'),
            created_at=data.get('created_at')
        )
    
    def to_dict(self):
        """
        Convert the User instance to a dictionary
        """
        return {
            '_id': self._id,
            'name': self.name,
            'email': self.email,
            'password': self.password,
            'user_type': self.user_type,
            'resume_url': self.resume_url,
            'skills': self.skills,
            'experience': self.experience,
            'education': self.education,
            'preferred_roles': self.preferred_roles,
            'location': self.location,
            'created_at': self.created_at
        }
    
    def to_json(self):
        """
        Convert to JSON-friendly dict (without sensitive data)
        """
        user_dict = self.to_dict()
        # Remove sensitive information
        user_dict.pop('password', None)
        # Convert ObjectId to string for JSON serialization
        user_dict['_id'] = str(user_dict['_id'])
        # Format datetime
        user_dict['created_at'] = user_dict['created_at'].isoformat()
        return user_dict 