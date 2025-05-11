"""
Job Model for MongoDB
"""
from datetime import datetime
from bson import ObjectId

class Job:
    """
    Job model representing job listings
    """
    
    collection_name = 'jobs'
    
    def __init__(self, title, company, description, location, 
                 source, apply_link, job_id_external, skills_required=None, 
                 posted_at=None, _id=None):
        self._id = _id or ObjectId()
        self.job_id_external = job_id_external
        self.title = title
        self.company = company
        self.description = description
        self.location = location
        self.source = source
        self.apply_link = apply_link
        self.skills_required = skills_required or []
        self.posted_at = posted_at or datetime.now()
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a Job instance from a dictionary
        """
        return cls(
            _id=data.get('_id'),
            job_id_external=data.get('job_id_external'),
            title=data.get('title'),
            company=data.get('company'),
            description=data.get('description'),
            location=data.get('location'),
            source=data.get('source'),
            apply_link=data.get('apply_link'),
            skills_required=data.get('skills_required'),
            posted_at=data.get('posted_at')
        )
    
    def to_dict(self):
        """
        Convert the Job instance to a dictionary
        """
        return {
            '_id': self._id,
            'job_id_external': self.job_id_external,
            'title': self.title,
            'company': self.company,
            'description': self.description,
            'location': self.location,
            'source': self.source,
            'apply_link': self.apply_link,
            'skills_required': self.skills_required,
            'posted_at': self.posted_at
        }
    
    def to_json(self):
        """
        Convert to JSON-friendly dict
        """
        job_dict = self.to_dict()
        # Convert ObjectId to string for JSON serialization
        job_dict['_id'] = str(job_dict['_id'])
        # Format datetime
        job_dict['posted_at'] = job_dict['posted_at'].isoformat()
        return job_dict 