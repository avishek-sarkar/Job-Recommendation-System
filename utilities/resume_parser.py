import re
import fitz  # PyMuPDF
from typing import Dict, List
from utilities.common import preprocess_text, load_lines, load_title_mappings, RESOURCE_DIR, nlp, extract_qualifications

# Load resources
SKILL_LIST = load_lines(RESOURCE_DIR / "skills.txt")
TITLE_SYNONYMS = load_title_mappings(RESOURCE_DIR / "job_titles.txt")
TECH_WORDS = set(SKILL_LIST) | set(TITLE_SYNONYMS.keys())

# PDF text extraction
def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file.
        
    Returns:
        str: Extracted text from all pages of the PDF, or empty string if extraction fails.
    """
    try:
        return " ".join([page.get_text() for page in fitz.open(pdf_path)])
    except Exception as e:
        print(f"Failed to extract text from PDF: {e}")
        return ""

# Generate n-grams
def generate_ngrams(words: List[str], n: int) -> List[str]:
    """
    Generate n-grams from a list of words.
    
    Args:
        words (list): List of words to generate n-grams from.
        n (int): Size of the n-grams to generate.
        
    Returns:
        list: List of n-grams as space-separated strings.
    """
    return [" ".join(words[i:i + n]) for i in range(len(words) - n + 1)]

# Resume component extractors
def normalize_title(title: str) -> str:
    """
    Normalize job titles using predefined synonyms.
    
    Args:
        title (str): Raw job title to normalize.
        
    Returns:
        str: Normalized job title.
    """
    title = title.lower()
    for key, value in TITLE_SYNONYMS.items():
        if re.search(rf"\b{re.escape(key)}\b", title):
            return value
    return title.title()

def extract_skills(text: str) -> List[str]:
    """
    Extract skills from text using unigrams, bigrams, and trigrams.
    
    Args:
        text (str): Raw text to extract skills from.
        
    Returns:
        list: Sorted list of matched skills found in the text.
    """
    if not text or not text.strip():
        return []
    
    words = preprocess_text(text).split()  # Preprocessed text split into words
    if not words:
        return []
    
    unigrams = words
    bigrams = generate_ngrams(words, 2)
    trigrams = generate_ngrams(words, 3)

    # Combine all n-grams
    all_ngrams = set(unigrams + bigrams + trigrams)

    # Match n-grams with SKILL_LIST
    return sorted(skill for skill in SKILL_LIST if skill in all_ngrams)

def extract_experience(text: str) -> List[str]:
    """
    Extract experience information from text using regex patterns.
    
    Args:
        text (str): Raw text to extract experience from.
        
    Returns:
        list: Sorted list of experience strings found in the text.
    """
    if not text or not text.strip():
        return []
    
    processed = preprocess_text(text)
    patterns = [
        r"\b\d+\s*(?:to|-)\s*\d+\s*years?\b",
        r"\b\d+\+?\s*years?\b",
        r"\bat least\s+\d+\s*years?\b",
        r"\b\d+\s*years?\b"
    ]
    experiences = set()
    for pattern in patterns:
        experiences.update(re.findall(pattern, processed))
    return sorted(list(experiences))

def extract_location(text: str) -> List[str]:
    """
    Extract location information from text using spaCy NER.
    
    Args:
        text (str): Raw text to extract locations from.
        
    Returns:
        list: Sorted list of location entities found in the text, excluding tech-related terms.
    """
    if not text or not text.strip():
        return []
    
    doc = nlp(text)
    return sorted({
        ent.text.strip()
        for ent in doc.ents
        if ent.label_ in {"GPE", "LOC", "FAC"} and ent.text.lower() not in TECH_WORDS
    })

def extract_title(text: str) -> List[str]:
    """
    Extract job titles from text based on predefined synonyms.
    
    Args:
        text (str): Raw text to extract job titles from.
        
    Returns:
        list: Sorted list of normalized job titles found in the text.
    """
    if not text or not text.strip():
        return []
    
    lines = text.splitlines()
    titles_found = set()
    for line in lines:
        for key, value in TITLE_SYNONYMS.items():
            if re.search(rf"\b{re.escape(key)}\b", line.lower()):
                titles_found.add(value)
    return sorted(titles_found)

# Main parser
def parse_resume(pdf_path: str) -> Dict[str, List[str]]:
    """
    Parse a resume PDF and extract key components.
    
    Args:
        pdf_path (str): Path to the resume PDF file.
        
    Returns:
        dict: Dictionary containing extracted features:
            - skills (list): Identified skills
            - experience (list): Years of experience
            - degrees (list): Educational qualifications
            - location (list): Geographic locations
            - titles (list): Job titles
    """
    text = extract_text_from_pdf(pdf_path)
    return {
        "skills": extract_skills(text),
        "experience": extract_experience(text),
        "degrees": extract_qualifications(text),
        "location": extract_location(text),
        "titles": extract_title(text)
    }
