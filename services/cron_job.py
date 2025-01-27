# services/cron_job.py

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

# Importing services
import sys
sys.path.append("../")
from services.HuggingFaceDailyPapersExtractor import PaperExtractor
from services.document_parser import parse_pdf_to_json
from services.gemini_wrapper import generate_insights
from services.prompts import SUMMARIZER_PROMPT, LINKEDIN_POST_CREATOR

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='cron_job.log',
    filemode='a'  # Append mode
)
logger = logging.getLogger(__name__)

def load_json(file_path: str) -> Optional[Dict]:
    """
    Load JSON data from a file.
    
    Parameters:
    - file_path (str): Path to the JSON file.
    
    Returns:
    - Optional[Dict]: The JSON data as a dictionary, or None if an error occurs.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded JSON data from '{file_path}'.")
        return data
    except Exception as e:
        logger.error(f"Failed to load JSON from '{file_path}': {e}")
        return None

def generate_summary(paper_json: Dict, title: str) -> Optional[str]:
    """
    Generate a summary for a paper using the Gemini model.
    
    Parameters:
    - paper_json (Dict): The JSON data of the paper.
    - title (str): The title of the paper.
    
    Returns:
    - Optional[str]: The generated summary or None if an error occurs.
    """
    content = ""
    for page in paper_json.get('pages', []):
        content += page.get("content", "") + "\n\n"
    
    prompt = SUMMARIZER_PROMPT.format(title=title, content=content)
    logger.info(f"Generating summary for paper: '{title}'")
    
    summary = generate_insights(prompt)
    if summary:
        logger.info(f"Summary generated for paper: '{title}'")
    else:
        logger.error(f"Failed to generate summary for paper: '{title}'")
    return summary

def generate_linkedin_post(papers: List[Dict[str, str]]) -> Optional[str]:
    """
    Generate a LinkedIn post based on a list of paper summaries using the Gemini model.
    
    Parameters:
    - papers (List[Dict[str, str]]): A list of dictionaries containing 'title', 'summary', and 'url' of each paper.
    
    Returns:
    - Optional[str]: The generated LinkedIn post or None if an error occurs.
    """
    if not papers:
        logger.warning("No papers available to generate LinkedIn post.")
        return None
    
    # Prepare the papers content
    papers_content = ""
    for paper in papers:
        title = paper.get('title', 'Unknown Title')
        summary = paper.get('summary', 'No summary available.')
        url = paper.get('url', '')
        papers_content += f"Title: {title}\nSummary: {summary}\nReference: {url}\n\n"
    
    prompt = LINKEDIN_POST_CREATOR.format(papers=papers_content)
    logger.info("Generating LinkedIn post.")
    
    linkedin_post = generate_insights(prompt)
    if linkedin_post:
        logger.info("LinkedIn post generated successfully.")
    else:
        logger.error("Failed to generate LinkedIn post.")
    return linkedin_post

def save_text(content: str, output_dir: str, filename: str):
    """
    Save text content to a file.
    
    Parameters:
    - content (str): The text content to save.
    - output_dir (str): Directory where the file will be saved.
    - filename (str): Name of the file.
    """
    # Sanitize the filename
    sanitized_filename = ''.join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in filename)
    file_path = os.path.join(output_dir, f"{sanitized_filename}.txt")
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Content saved to '{file_path}'.")
    except Exception as e:
        logger.error(f"Failed to save content to '{file_path}': {e}")

def main():
    """
    Main function to orchestrate the extraction, parsing, summarization, LinkedIn post generation, and saving of research papers.
    """
    logger.info("Cron job started.")
    
    # Define directories
    today_date = datetime.today().strftime('%Y-%m-%d')
    save_directory = os.path.join('papers', today_date)
    summaries_directory = os.path.join('summaries', today_date)
    linkedin_post_directory = os.path.join('linkedin', today_date)
    
    # Ensure directories exist
    os.makedirs(summaries_directory, exist_ok=True)
    os.makedirs(linkedin_post_directory, exist_ok=True)
    
    # Initialize PaperExtractor
    extractor = PaperExtractor(base_url='https://huggingface.co', save_directory=save_directory)
    paper_details_list = extractor.run()
    
    if not paper_details_list:
        logger.info("No papers to process.")
        return
    
    papers = []
    # Process each paper
    for paper_detail in paper_details_list:
        pdf_path = paper_detail.get('pdf_path')
        url = paper_detail.get('url')
        title = paper_detail.get('title', 'Unknown_Title')
        
        logger.info(f"Processing PDF: '{pdf_path}'")
        
        # Parse PDF to JSON
        json_path = parse_pdf_to_json(pdf_path, overwrite=True)
        if not json_path:
            logger.error(f"Skipping PDF due to parsing failure: '{pdf_path}'")
            continue
        
        # Load parsed JSON
        paper_json = load_json(json_path)
        if not paper_json:
            logger.error(f"Skipping PDF due to JSON loading failure: '{pdf_path}'")
            continue
        
        # Generate summary
        summary = generate_summary(paper_json, title)
        if summary:
            # Save summary
            save_text(summary, summaries_directory, f"{title}_summary")
            
            # Append to papers list for LinkedIn post
            papers.append({
                'title': title,
                'summary': summary,
                'url': url
            })
        else:
            logger.error(f"Summary generation failed for paper: '{title}'")
    
    # Generate LinkedIn post
    linkedin_post = generate_linkedin_post(papers)
    if linkedin_post:
        # Save LinkedIn post
        save_text(linkedin_post, linkedin_post_directory, f"LinkedIn_Post_{today_date}")
    else:
        logger.error("LinkedIn post generation failed.")
    
    logger.info("Cron job completed successfully.")

if __name__ == "__main__":
    main()
