# services/HuggingFaceDailyPapersExtractor.py

import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Dict
import datetime
import os

class PaperExtractor:
    def __init__(self, base_url: str, save_directory: str):
        """
        Initialize the PaperExtractor with a base URL and a directory to save PDFs.

        Parameters:
        - base_url (str): The base URL of the website to scrape.
        - save_directory (str): The directory where PDFs will be saved.
        """
        self.base_url = base_url.rstrip('/')
        self.save_directory = save_directory
        self.headers = {
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                           '(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
        }

    def get_todays_date(self) -> str:
        """Return today's date in YYYY-MM-DD format."""
        return datetime.datetime.today().strftime('%Y-%m-%d')

    def get_unique_paper_urls(self) -> Optional[List[str]]:
        """
        Fetch unique paper URLs from the website for today's date.

        Returns:
            Optional[List[str]]: A list of unique paper URLs, or None if the request fails.
        """
        date = self.get_todays_date()
        url = f"{self.base_url}/papers?date={date}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to retrieve data: {e}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        paper_links = soup.find_all('a', href=True)
        unique_urls = set([
            f"{self.base_url}{link['href']}" for link in paper_links
            if "/papers/" in link['href'] and "community" not in link['href']
        ])

        return list(unique_urls)

    def fetch_paper_details_and_download_pdf(self, url: str) -> Optional[Dict[str, str]]:
        """
        Fetch details of a research paper from the provided URL and download the PDF.

        Parameters:
        - url (str): The URL of the paper page.

        Returns:
        - Optional[Dict[str, str]]: A dictionary containing the URL, title, authors, abstract, and PDF path,
          or None if the fetching fails.
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract title
            title_element = soup.find('h1')
            title = title_element.get_text(strip=True) if title_element else "Unknown Title"

            # Extract authors
            authors = [author.get_text(strip=True) for author in soup.select('div.author a')]
            authors_list = ', '.join(authors) if authors else "Unknown Authors"

            # Extract abstract
            abstract_element = soup.find('h2', string='Abstract')
            if abstract_element:
                abstract_paragraph = abstract_element.find_next('p')
                if abstract_paragraph:
                    abstract = abstract_paragraph.get_text(strip=True)
                else:
                    abstract = "No abstract available"
            else:
                abstract = "No abstract available"

            # Find the PDF link
            pdf_link_element = None
            # The PDF button uses multiple CSS classes. Using `find_all` with
            # a single class string requires an exact match of the class
            # attribute, which is brittle because the order of classes in HTML
            # is not guaranteed and extra classes may be added. Use a CSS
            # selector instead so that elements containing all of the expected
            # classes are matched regardless of order or additional classes.
            for a_tag in soup.select('a.btn.inline-flex.h-9.items-center'):
                if 'View PDF' in a_tag.get_text():
                    pdf_link_element = a_tag
                    break
            if pdf_link_element and 'href' in pdf_link_element.attrs:
                pdf_link = pdf_link_element['href']
                # Ensure full URL if needed
                if not pdf_link.startswith('http'):
                    pdf_link = self.base_url + pdf_link
            else:
                raise ValueError("PDF link not found")

            # Download the PDF
            pdf_response = requests.get(pdf_link, headers=self.headers)
            pdf_response.raise_for_status()

            # Ensure the save directory exists
            os.makedirs(self.save_directory, exist_ok=True)

            # Sanitize the filename
            sanitized_title = ''.join(c if c.isalnum() or c in (' ', '_') else '_' for c in title)
            pdf_filename = os.path.join(self.save_directory, f"{sanitized_title}.pdf")

            # Write the PDF to a file
            with open(pdf_filename, 'wb') as pdf_file:
                pdf_file.write(pdf_response.content)

            print(f"Downloaded PDF: {pdf_filename}")

            return {
                'url': url,
                'title': title,
                'authors': authors_list,
                'abstract': abstract,
                'pdf_path': pdf_filename
            }

        except requests.RequestException as e:
            print(f"Error fetching paper details or PDF: {e}")
            return None
        except ValueError as e:
            print(e)
            return None
        except Exception as e:
            print(f"An error occurred while processing the page: {e}")
            return None

    def run(self) -> List[Dict[str, str]]:
        """Run the paper extraction process and return details of all papers."""
        paper_details_list = []
        paper_urls = self.get_unique_paper_urls()
        if not paper_urls:
            print("No paper URLs found.")
            return paper_details_list
        os.makedirs(self.save_directory, exist_ok=True)
        for url in paper_urls:
            paper_details = self.fetch_paper_details_and_download_pdf(url)
            if paper_details:
                print(paper_details)
                paper_details_list.append(paper_details)
        return paper_details_list

# Usage example
if __name__ == '__main__':
    save_directory = f'./papers2/{datetime.datetime.today().strftime("%Y-%m-%d")}'
    extractor = PaperExtractor(base_url='https://huggingface.co', save_directory=save_directory)
    extractor.run()
