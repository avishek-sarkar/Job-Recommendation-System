import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List
from pathlib import Path
from utilities.common import preprocess_text, extract_all_features, features_to_text, combine_resume_features, safe_lowercase, extract_qualifications

# Dataset preprocessing
def load_and_clean_dataset(dataset_path: str) -> pd.DataFrame:
    """
    Load and clean the job dataset.
    
    Args:
        dataset_path (str): Path to the CSV file containing job listings.
        
    Returns:
        pd.DataFrame: Cleaned DataFrame with processed job descriptions and metadata.
        
    Raises:
        FileNotFoundError: If the dataset file does not exist.
    """
    # Check if dataset file exists
    if not Path(dataset_path).exists():
        raise FileNotFoundError(f"Dataset file not found at: {dataset_path}")
    
    df = pd.read_csv(dataset_path)

    # Drop rows with critical null values
    df.dropna(subset=["Job Title", "Job Link", "Company", "Job Description"], inplace=True)

    # Remove outdated jobs
    #df['Deadline'] = pd.to_datetime(df['Deadline'], format="%d-%b-%y", errors="coerce")
    #df = df[df['Deadline'] >= pd.Timestamp.today()]

    # Drop duplicates
    df.drop_duplicates(subset=["Job Title", "Company", "Deadline", "Job Description"], inplace=True)

    # Retain the original job title
    df["Original_Title"] = df["Job Title"]

    # Normalize job titles
    df["Job Title"] = df["Job Title"].apply(lambda x: safe_lowercase(preprocess_text(x)) if isinstance(x, str) else "")

    # Extract and normalize education qualifications (using common function)
    df["Education"] = df["Education"].fillna("").apply(lambda x: " ".join(extract_qualifications(x)) if x else "")
    df["Experience"] = df["Experience"].fillna("").str.lower()

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

def extract_keywords_from_description(text: str) -> str:
    """
    Extract and return relevant keywords from job description.
    
    Args:
        text (str): Raw job description text.
        
    Returns:
        str: Space-separated string of extracted keywords (skills, experience, degrees, titles).
    """
    features = extract_all_features(text)
    return features_to_text(features)

# Job matching
def match_resume_to_jobs(resume_data: Dict[str, List[str]], dataset_path: str, top_n: int = 5) -> pd.DataFrame:
    """
    Match resume to jobs using TF-IDF vectorization and cosine similarity.
    
    Args:
        resume_data (dict): Dictionary containing parsed resume features:
            - titles (list): Job titles
            - skills (list): Skills
            - experience (list): Experience years
            - degrees (list): Educational qualifications
            - location (list): Geographic locations
        dataset_path (str): Path to the CSV file containing job listings.
        top_n (int, optional): Number of top matching jobs to return. Defaults to 5.
        
    Returns:
        pd.DataFrame: DataFrame with top N matching jobs, including:
            - Original_Title: Job title
            - Company: Company name
            - Location: Job location
            - Deadline: Application deadline
            - Job Link: URL to job posting
            - Similarity: Cosine similarity score
    """
    df = load_and_clean_dataset(dataset_path)
    
    # Check if dataset is empty after cleaning
    if df.empty:
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=["Original_Title", "Company", "Location", "Deadline", "Job Link", "Similarity"])

    # Combine resume fields with weights
    resume_text = combine_resume_features(resume_data)
    resume_text = preprocess_text(resume_text)

    # Fit TF-IDF with bigrams and trigrams
    # min_df=1 to capture rare but important skills, max_df=0.9 to filter common words
    all_docs = df["Processed_Description"].tolist() + [resume_text]
    tfidf = TfidfVectorizer(ngram_range=(1, 3), min_df=1, max_df=0.9)
    tfidf_matrix = tfidf.fit_transform(all_docs)

    # Compute cosine similarity
    cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    df["Similarity"] = cosine_sim

    # Get top matches
    matched_jobs = df.sort_values(by="Similarity", ascending=False).head(top_n)

    return matched_jobs[["Original_Title", "Company", "Location", "Deadline", "Job Link", "Similarity"]]
