import spacy
import re
import fitz  # PyMuPDF
from pathlib import Path

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Load external resources
RESOURCE_DIR = Path(__file__).resolve().parent.parent / "resources"

def load_lines(filepath):
    """Load lines from a file as a set of lowercase strings."""
    return {line.strip().lower() for line in open(filepath, encoding="utf-8") if line.strip() and not line.startswith("#")}

def load_title_mappings(filepath):
    """Load job title mappings from a file."""
    title_map = {}
    with open(filepath, encoding="utf-8") as file:
        for line in file:
            if "→" in line:
                key, value = line.strip().lower().split("→")
                title_map[key.strip()] = value.strip()
    return title_map

# Load resources
SKILL_LIST = load_lines(RESOURCE_DIR / "skills.txt")
TITLE_SYNONYMS = load_title_mappings(RESOURCE_DIR / "job_titles.txt")
DEGREE_KEYWORDS = load_lines(RESOURCE_DIR / "degree_keywords.txt")
TECH_WORDS = set(SKILL_LIST) | set(TITLE_SYNONYMS.keys())

# Shared text preprocessing
def preprocess_text(text):
    """Lowercase, remove stopwords and punctuation, lemmatize."""
    doc = nlp(text.lower())
    return " ".join([token.lemma_ for token in doc if not token.is_stop and not token.is_punct])

# PDF text extraction
def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    try:
        return " ".join([page.get_text() for page in fitz.open(pdf_path)])
    except Exception as e:
        print(f"Failed to extract text from PDF: {e}")
        return ""

# Generate n-grams
def generate_ngrams(words, n):
    """Generate n-grams from a list of words."""
    return [" ".join(words[i:i + n]) for i in range(len(words) - n + 1)]

# Resume component extractors
def normalize_title(title):
    """Normalize job titles using synonyms."""
    title = title.lower()
    for key, value in TITLE_SYNONYMS.items():
        if re.search(rf"\b{re.escape(key)}\b", title):
            return value
    return title.title()

def extract_skills(text):
    """Extract skills from text using unigrams, bigrams, and trigrams."""
    words = preprocess_text(text).split()  # Preprocessed text split into words
    unigrams = words
    bigrams = generate_ngrams(words, 2)
    trigrams = generate_ngrams(words, 3)

    # Combine all n-grams
    all_ngrams = set(unigrams + bigrams + trigrams)

    # Match n-grams with SKILL_LIST
    return sorted(skill for skill in SKILL_LIST if skill in all_ngrams)

def extract_experience(text):
    """Extract experience information from text."""
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

def extract_qualifications(text):
    """Extract degree qualifications from text."""
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

def extract_location(text):
    """Extract location information from text."""
    doc = nlp(text)
    return sorted({
        ent.text.strip()
        for ent in doc.ents
        if ent.label_ in {"GPE", "LOC", "FAC"} and ent.text.lower() not in TECH_WORDS
    })

def extract_title(text):
    """Extract job titles from text based on predefined synonyms."""
    lines = text.splitlines()
    titles_found = set()
    for line in lines:
        for key, value in TITLE_SYNONYMS.items():
            if re.search(rf"\b{re.escape(key)}\b", line.lower()):
                titles_found.add(value)
    return sorted(titles_found)

# Main parser
def parse_resume(pdf_path):
    """Parse a resume PDF and extract key components."""
    text = extract_text_from_pdf(pdf_path)
    return {
        "skills": extract_skills(text),
        "experience": extract_experience(text),
        "degrees": extract_qualifications(text),
        "location": extract_location(text),
        "titles": extract_title(text)
    }
