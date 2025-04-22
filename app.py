from flask import Flask, render_template, request, redirect, url_for, flash
import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime
from utilities.resume_parser import parse_resume
from utilities.job_matcher import match_resume_to_jobs

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

UPLOAD_FOLDER = 'resources/uploads'
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists with error handling
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except OSError as e:
    print(f"Error creating upload folder: {e}")
    raise

@app.route('/')
def index():
    # Ensure top_matches is defined as None when rendering the home page
    return render_template('index.html', year=datetime.now().year, top_matches=None, has_results=False)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'resume' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('index'))

    file = request.files['resume']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))

    if file and file.filename.endswith('.pdf'):
        file.seek(0, os.SEEK_END)
        file_length = file.tell()
        file.seek(0)

        if file_length > MAX_FILE_SIZE:
            flash('The file exceeds the 10 MB size limit.', 'error')
            return redirect(url_for('index'))

        # Generate unique filename
        extension = os.path.splitext(secure_filename(file.filename))[1]
        unique_filename = f"{uuid.uuid4().hex}{extension}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

        try:
            file.save(filepath)
            flash('Resume uploaded successfully!', 'success')

            # Parse resume
            parsed_data = parse_resume(filepath)
            print("Parsed Resume Data:", parsed_data)  # Debugging

            # Match jobs
            dataset_path = 'resources/job_dataset.csv'
            top_matches = match_resume_to_jobs(parsed_data, dataset_path, top_n=5)
            print("Top Job Matches:", top_matches)  # Debugging

        finally:
            # Always delete the file after processing
            if os.path.exists(filepath):
                os.remove(filepath)

    else:
        flash('The file is not in PDF format.', 'error')
        top_matches = None  # Ensure top_matches is defined

    # Check if there are any matching jobs
    has_results = top_matches is not None and not top_matches.empty

    return render_template(
        'index.html',
        year=datetime.now().year,
        top_matches=top_matches.to_dict(orient='records') if has_results else None,
        has_results=has_results
    )

@app.route('/developerinfo')
def developerinfo():
    return "<h2>Developer Info Page (To Be Developed)</h2>"

if __name__ == '__main__':
    app.run(debug=True)
