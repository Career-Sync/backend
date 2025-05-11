"""
Application Model for MongoDB
"""
from datetime import datetime
from bson import ObjectId

class Application:
    """
    Application model representing job applications
    """
    
    collection_name = 'applications'
    
    def __init__(self, user_id, job_id, resume_url, 
                 alignment_score=None, missing_keywords=None, 
                 applied_at=None, status='pending', _id=None):
        self._id = _id or ObjectId()
        self.user_id = user_id
        self.job_id = job_id
        self.resume_url = resume_url
        self.alignment_score = alignment_score
        self.missing_keywords = missing_keywords or []
        self.applied_at = applied_at or datetime.now()
        self.status = status  # 'pending', 'viewed', 'rejected', 'shortlisted'
    
    @classmethod
    def from_dict(cls, data):
        """
        Create an Application instance from a dictionary
        """
        return cls(
            _id=data.get('_id'),
            user_id=data.get('user_id'),
            job_id=data.get('job_id'),
            resume_url=data.get('resume_url'),
            alignment_score=data.get('alignment_score'),
            missing_keywords=data.get('missing_keywords'),
            applied_at=data.get('applied_at'),
            status=data.get('status', 'pending')
        )
    
    def to_dict(self):
        """
        Convert the Application instance to a dictionary
        """
        return {
            '_id': self._id,
            'user_id': self.user_id,
            'job_id': self.job_id,
            'resume_url': self.resume_url,
            'alignment_score': self.alignment_score,
            'missing_keywords': self.missing_keywords,
            'applied_at': self.applied_at,
            'status': self.status
        }
    
    def to_json(self):
        """
        Convert to JSON-friendly dict
        """
        app_dict = self.to_dict()
        # Convert ObjectId to string for JSON serialization
        app_dict['_id'] = str(app_dict['_id'])
        app_dict['user_id'] = str(app_dict['user_id'])
        app_dict['job_id'] = str(app_dict['job_id'])
        # Format datetime
        app_dict['applied_at'] = app_dict['applied_at'].isoformat()
        return app_dict 