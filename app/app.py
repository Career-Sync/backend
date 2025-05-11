from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
CORS(app)

# Configure JWT
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key')
jwt = JWTManager(app)

# Import and register routes
from routes.auth import auth_bp
from routes.jobs import jobs_bp
from routes.applications import applications_bp
from routes.resume import resume_bp
from routes.recruiter import recruiter_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(jobs_bp, url_prefix='/jobs')
app.register_blueprint(applications_bp, url_prefix='/applications')
app.register_blueprint(resume_bp, url_prefix='/resume')
app.register_blueprint(recruiter_bp, url_prefix='/recruiter')

@app.route('/')
def index():
    return jsonify({
        'message': 'Welcome to CareerSync API',
        'status': 'online'
    })

if __name__ == '__main__':
    app.run(debug=True) 