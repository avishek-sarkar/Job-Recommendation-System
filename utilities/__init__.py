"""
Utilities package for Job Recommendation System.
Provides resume parsing and job matching functionality.
"""

from .resume_parser import parse_resume
from .job_matcher import match_resume_to_jobs
from .common import (
    extract_all_features,
    features_to_text,
    combine_resume_features,
    safe_lowercase,
    preprocess_text,
    load_lines,
    load_title_mappings,
    extract_qualifications,
    RESOURCE_DIR,
    nlp
)

__all__ = [
    'parse_resume',
    'match_resume_to_jobs',
    'extract_all_features',
    'features_to_text',
    'combine_resume_features',
    'safe_lowercase',
    'preprocess_text',
    'load_lines',
    'load_title_mappings',
    'extract_qualifications',
    'RESOURCE_DIR',
    'nlp'
]
