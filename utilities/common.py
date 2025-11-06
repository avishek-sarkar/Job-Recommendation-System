"""
Common utility functions shared across the application.
Consolidates repeated code patterns for text processing and feature extraction.
"""

import spacy
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Union

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Resource directory path
RESOURCE_DIR = Path(__file__).resolve().parent.parent / "resources"


# Resource loading functions
def load_lines(filepath: Union[str, Path]) -> Set[str]:
    """
    Load lines from a file as a set of lowercase strings.
    
    Args:
        filepath (str or Path): Path to the file to load.
        
    Returns:
        set: Set of lowercase strings from the file, excluding comments and empty lines.
    """
    with open(filepath, encoding="utf-8") as f:
        return {line.strip().lower() for line in f if line.strip() and not line.startswith("#")}


# Load degree keywords for qualification extraction
DEGREE_KEYWORDS = load_lines(RESOURCE_DIR / "degree_keywords.txt")


def load_title_mappings(filepath: Union[str, Path]) -> Dict[str, str]:
    """
    Load job title mappings from a file.
    
    Args:
        filepath (str or Path): Path to the file containing title mappings.
        
    Returns:
        dict: Dictionary mapping job title variations to standardized titles.
    """
    title_map = {}
    with open(filepath, encoding="utf-8") as file:
        for line in file:
            if "→" in line:
                key, value = line.strip().lower().split("→")
                title_map[key.strip()] = value.strip()
    return title_map


# Text preprocessing
def preprocess_text(text: str) -> str:
    """
    Preprocess text by lowercasing, removing stopwords and punctuation, and lemmatizing.
    
    Args:
        text (str): Raw text to preprocess.
        
    Returns:
        str: Preprocessed text with lemmatized tokens.
    """
    doc = nlp(text.lower())
    return " ".join([token.lemma_ for token in doc if not token.is_stop and not token.is_punct])


def extract_qualifications(text: str) -> List[str]:
    """
    Extract degree qualifications from text using keywords and patterns.
    
    Args:
        text (str): Raw text to extract qualifications from.
        
    Returns:
        list: Sorted list of degree qualifications found in the text.
    """
    if not text or not text.strip():
        return []
    
    text_lower = text.lower()
    degrees_found = set()

    for kw in DEGREE_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", text_lower):
            degrees_found.add(kw)

    patterns = [
        r"\b(b\.?s\.?|m\.?s\.?|bsc|msc|ph\.?d\.?|bachelor(?:'s)?|master(?:'s)?)\b",
        r"(bachelor|master) of [a-z\s]+" 
    ]
    for pattern in patterns:
        for match in re.findall(pattern, text_lower):
            degrees_found.add(match.strip())

    return sorted(degrees_found)


# Feature extraction utilities (delegating to resume_parser for actual extraction)
def extract_all_features(text: str) -> Dict[str, List[str]]:
    """
    Extract all features from text in one call.
    
    Consolidates the repeated pattern of calling all extraction functions
    and combining their results.
    
    Args:
        text (str): Text to extract features from.
        
    Returns:
        dict: Dictionary containing:
            - skills (list): Extracted skills
            - experience (list): Extracted experience
            - degrees (list): Extracted degrees
            - titles (list): Extracted titles
    """
    # Import here to avoid circular dependency
    from utilities.resume_parser import extract_skills, extract_experience, extract_title
    
    # Pass raw text - extraction functions handle preprocessing internally
    return {
        "skills": extract_skills(text),
        "experience": extract_experience(text),
        "degrees": extract_qualifications(text),  # Use common function
        "titles": extract_title(text)
    }


def features_to_text(features_dict: Dict[str, List[str]]) -> str:
    """
    Convert features dictionary to a single text string.
    
    Args:
        features_dict (dict): Dictionary with feature lists.
        
    Returns:
        str: Space-separated string of all features.
    """
    all_features = []
    for key in ["skills", "experience", "degrees", "titles"]:
        all_features.extend(features_dict.get(key, []))
    return " ".join(all_features)


def combine_resume_features(resume_data: Dict[str, List[str]], weights: Optional[Dict[str, int]] = None) -> str:
    """
    Combine resume features with optional weighting.
    
    Args:
        resume_data (dict): Dictionary containing resume features.
        weights (dict, optional): Dictionary with weights for each feature.
            If None, uses Config.FEATURE_WEIGHTS from config.py.
            
    Returns:
        str: Combined and weighted text representation of resume.
    """
    if weights is None:
        # Import here to avoid circular dependency
        from config import Config
        weights = Config.FEATURE_WEIGHTS
    
    weighted_parts = []
    for feature, weight in weights.items():
        feature_list = resume_data.get(feature, [])
        if feature_list:
            feature_text = " ".join(feature_list).lower()
            weighted_parts.append(feature_text * weight)
    
    return " ".join(weighted_parts)


def safe_lowercase(text: Any) -> str:
    """
    Safely convert text to lowercase, handling None and non-string values.
    
    Args:
        text: Text to convert (can be str, None, or other types).
        
    Returns:
        str: Lowercase string, or empty string if input is None/invalid.
    """
    if text is None:
        return ""
    if isinstance(text, str):
        return text.lower()
    return str(text).lower()
