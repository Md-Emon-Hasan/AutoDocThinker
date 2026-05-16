from app.ingestion.loaders.docx_loader import DocxLoader
from app.ingestion.loaders.pdf_loader import PdfLoader
from app.ingestion.loaders.text_loader import TextLoader
from app.ingestion.loaders.txt_loader import TxtLoader
from app.ingestion.loaders.url_loader import UrlLoader


def get_loader(file_type: str):
    loaders = {
        "pdf": PdfLoader(),
        "docx": DocxLoader(),
        "txt": TxtLoader(),
        "url": UrlLoader(),
        "text": TextLoader(),
    }
    if file_type not in loaders:
        raise ValueError(f"Unsupported file type: {file_type}")
    return loaders[file_type]
