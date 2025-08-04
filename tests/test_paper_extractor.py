import os
import sys
from pathlib import Path

# Ensure the project root is on the Python path so that the `services` package
# can be imported when tests are executed from any directory.
sys.path.append(str(Path(__file__).resolve().parent.parent))
from services import HuggingFaceDailyPapersExtractor as extractor_module


class MockResponse:
    def __init__(self, text='', content=b'', status_code=200):
        self.text = text
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error {self.status_code}")


def test_fetch_paper_details_pdf_link_class_order(monkeypatch, tmp_path):
    html_content = (
        "<html><body>"
        "<h1>Sample Paper</h1>"
        "<div class='author'><a>John Doe</a></div>"
        "<h2>Abstract</h2><p>This is abstract.</p>"
        "<a href='/sample.pdf' class='inline-flex btn h-9 items-center extra'>View PDF</a>"
        "</body></html>"
    )

    def mock_get(url, headers=None):
        if url.endswith('.pdf'):
            return MockResponse(content=b'%PDF-1.4 test pdf')
        return MockResponse(text=html_content)

    # Patch requests.get used within the extractor module
    monkeypatch.setattr(extractor_module.requests, "get", mock_get)

    extractor = extractor_module.PaperExtractor(
        base_url='https://huggingface.co', save_directory=str(tmp_path)
    )
    details = extractor.fetch_paper_details_and_download_pdf('https://huggingface.co/paper1')

    assert details['title'] == 'Sample Paper'
    assert details['authors'] == 'John Doe'
    assert details['abstract'] == 'This is abstract.'
    assert os.path.exists(details['pdf_path'])

