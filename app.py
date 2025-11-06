from flask import Flask, render_template, request, redirect, url_for, flash
import os
import uuid
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from datetime import datetime
from typing import Tuple, Optional
import pandas as pd
from utilities import parse_resume, match_resume_to_jobs
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Helper functions for file upload processing
def validate_file_upload(file: FileStorage) -> Tuple[bool, Optional[str]]:
    """
    Validate uploaded file.
    
    Args:
        file: FileStorage object from request.files.
        
    Returns:
        tuple: (is_valid, error_message) - True if valid, False with error message otherwise.
    """
    if not file or file.filename == '':
        return False, 'No file selected'
    
    # Check file extension against allowed extensions
    file_ext = os.path.splitext(file.filename)[1].lower().lstrip('.')
    if file_ext not in Config.ALLOWED_EXTENSIONS:
        return False, f'Invalid file format. Only {", ".join(Config.ALLOWED_EXTENSIONS).upper()} files are allowed.'
    
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    file.seek(0)
    
    if file_length > Config.MAX_CONTENT_LENGTH:
        return False, 'The file exceeds the 10 MB size limit.'
    
    return True, None

def save_uploaded_file(file: FileStorage) -> str:
    """
    Save uploaded file with a unique filename.
    
    Args:
        file: FileStorage object to save.
        
    Returns:
        str: Path to the saved file.
    """
    extension = os.path.splitext(secure_filename(file.filename))[1]
    unique_filename = f"{uuid.uuid4().hex}{extension}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(filepath)
    return filepath

def process_resume(filepath: str) -> Optional[pd.DataFrame]:
    """
    Parse resume and match it to jobs.
    
    Args:
        filepath (str): Path to the resume file.
        
    Returns:
        pd.DataFrame or None: DataFrame with top job matches, or None if processing fails.
    """
    try:
        # Parse resume
        parsed_data = parse_resume(filepath)
        print("Parsed Resume Data:", parsed_data)  # Debugging
        
        # Match jobs
        top_matches = match_resume_to_jobs(parsed_data, Config.DATASET_PATH, top_n=Config.TOP_N_MATCHES)
        print("Top Job Matches:", top_matches)  # Debugging
        
        return top_matches
    except Exception as e:
        print(f"Error processing resume: {e}")  # Debugging
        raise

def cleanup_file(filepath: str) -> None:
    """
    Delete uploaded file after processing.
    
    Args:
        filepath (str): Path to the file to delete.
    """
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except OSError as e:
            print(f"Error deleting file {filepath}: {e}")

@app.route('/')
def index() -> str:
    """
    Render the home page.
    
    Returns:
        str: Rendered HTML template for the home page with no job matches.
    """
    return render_template('index.html', year=datetime.now().year, top_matches=None)

@app.route('/upload', methods=['POST'])
def upload_file() -> str:
    """
    Handle resume file upload, parsing, and job matching.
    
    Validates the uploaded file, parses the resume to extract features,
    matches it against job listings, and displays the top matching jobs.
    
    Returns:
        str: Rendered HTML template with job matching results or error messages.
        
    Flash Messages:
        - Error: If no file is provided, file is invalid, or processing fails
        - Success: If resume is uploaded and processed successfully
    """
    # Check if file is in request
    if 'resume' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('index'))
    
    file = request.files['resume']
    
    # Validate file
    is_valid, error_message = validate_file_upload(file)
    if not is_valid:
        flash(error_message, 'error')
        return redirect(url_for('index'))
    
    # Save and process file
    filepath = None
    top_matches = None
    
    try:
        filepath = save_uploaded_file(file)
        flash('Resume uploaded successfully!', 'success')
        top_matches = process_resume(filepath)
    except Exception as e:
        flash(f'An error occurred while processing your resume: {str(e)}', 'error')
        top_matches = None
    finally:
        if filepath:
            cleanup_file(filepath)
    
    # Render results
    return render_template(
        'index.html',
        year=datetime.now().year,
        top_matches=top_matches.to_dict(orient='records') if (top_matches is not None and not top_matches.empty) else None
    )

@app.route('/developerinfo')
def developerinfo() -> str:
    """
    Render the developer information page.
    
    Returns:
        str: Rendered HTML template with developer GitHub profiles.
    """
    return render_template('developerinfo.html', year=datetime.now().year)

# Error Handlers
@app.errorhandler(404)
def not_found_error(error) -> Tuple[str, int]:
    """Handle 404 errors - Page not found."""
    return render_template('index.html', 
                         year=datetime.now().year, 
                         top_matches=None), 404

@app.errorhandler(500)
def internal_error(error) -> Tuple[str, int]:
    """Handle 500 errors - Internal server error."""
    flash('An internal error occurred. Please try again later.', 'error')
    return render_template('index.html', 
                         year=datetime.now().year, 
                         top_matches=None), 500

@app.errorhandler(413)
def request_entity_too_large(error) -> str:
    """Handle 413 errors - File too large."""
    flash('The uploaded file is too large. Maximum size is 10 MB.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=Config.DEBUG)
