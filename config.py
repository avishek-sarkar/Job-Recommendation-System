"""
Configuration management for the Job Recommendation System.
Loads settings from environment variables with sensible defaults.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class."""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')
    
    # Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'resources', 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB max file size
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # Resource Paths
    BASE_DIR = os.path.dirname(__file__)
    RESOURCES_DIR = os.path.join(BASE_DIR, 'resources')
    DATASET_PATH = os.path.join(RESOURCES_DIR, 'job_dataset.csv')
    
    # Job Matching Configuration
    TOP_N_MATCHES = 5  # Number of top job matches to return
    
    # Feature weights for resume-to-job matching
    # Higher weights mean the feature is more important in matching
    FEATURE_WEIGHTS = {
        "titles": 10,      # Job titles (highest priority)
        "skills": 9,       # Technical and soft skills
        "experience": 3,   # Years of experience
        "degrees": 3,      # Educational qualifications
        "location": 2      # Geographic location
    }
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration."""
        # Ensure upload directory exists
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
