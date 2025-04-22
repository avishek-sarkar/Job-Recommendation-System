import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path
from utilities.resume_parser import preprocess_text, extract_skills, extract_experience, extract_qualifications, extract_title

# Load resources
RESOURCE_DIR = Path(__file__).resolve().parent.parent / "resources"

# Dataset preprocessing
def load_and_clean_dataset(dataset_path):
    """Load and clean the job dataset."""
    df = pd.read_csv(dataset_path)

    # Drop rows with critical null values
    df.dropna(subset=["Job Title", "Job Link", "Company", "Job Description"], inplace=True)

    # Remove outdated jobs
    df['Deadline'] = pd.to_datetime(df['Deadline'], format="%d-%b-%y", errors="coerce")
    df = df[df['Deadline'] >= pd.Timestamp.today()]

    # Drop duplicates
    df.drop_duplicates(subset=["Job Title", "Company", "Deadline", "Job Description"], inplace=True)

    # Retain the original job title
    df["Original_Title"] = df["Job Title"]

    # Normalize job titles
    df["Job Title"] = df["Job Title"].apply(lambda x: preprocess_text(x).lower() if isinstance(x, str) else "")

    # Convert Education and Experience to lowercase
    df["Education"] = df["Education"].str.lower()
    df["Experience"] = df["Experience"].str.lower()

    # Extract keywords from job descriptions
    df["Extracted_Keywords"] = df["Job Description"].apply(extract_keywords_from_description)
    df["Extracted_Keywords"] = df["Extracted_Keywords"].str.lower()

    # Combine original fields and extracted keywords
    df["Combined_Text"] = (
        df["Job Title"].astype(str).str.lower() + " " +
        df["Location"].astype(str).str.lower() + " " +
        df["Education"].astype(str) + " " +
        df["Experience"].astype(str) + " " +
        df["Extracted_Keywords"]
    )

    # Preprocess combined text
    df["Processed_Description"] = df["Combined_Text"].apply(preprocess_text)

    return df

def extract_keywords_from_description(text):
    """Extract and return relevant keywords from job description."""
    preprocessed_text = preprocess_text(text)
    skills = extract_skills(preprocessed_text)
    experience = extract_experience(preprocessed_text)
    degrees_info = extract_qualifications(preprocessed_text)
    titles = extract_title(preprocessed_text)
    return " ".join(skills + experience + degrees_info + titles)

# Job matching
def match_resume_to_jobs(resume_data, dataset_path, top_n=5):
    """Match resume to jobs using TF-IDF and cosine similarity."""
    df = load_and_clean_dataset(dataset_path)

    # Combine resume fields (convert lists to strings)
    resume_text = " ".join([
        " ".join(resume_data.get("titles", [])).lower() * 10,
        " ".join(resume_data.get("skills", [])).lower() * 9,
        " ".join(resume_data.get("experience", [])).lower() * 3,
        " ".join(resume_data.get("degrees", [])).lower() * 3,
        " ".join(resume_data.get("location", [])).lower() * 2,
    ])

    resume_text = preprocess_text(resume_text)

    # Fit TF-IDF with bigrams and trigrams
    all_docs = df["Processed_Description"].tolist() + [resume_text]
    tfidf = TfidfVectorizer(ngram_range=(1, 3), min_df=2, max_df=0.9)
    tfidf_matrix = tfidf.fit_transform(all_docs)

    # Compute cosine similarity
    cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    df["Similarity"] = cosine_sim

    # Get top matches
    matched_jobs = df.sort_values(by="Similarity", ascending=False).head(top_n)

    return matched_jobs[["Original_Title", "Company", "Location", "Deadline", "Job Link", "Similarity"]]
