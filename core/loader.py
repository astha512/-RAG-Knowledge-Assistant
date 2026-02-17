import os
import logging
from typing import List
from langchain_core.documents import Document
# from langchain_unstructured import UnstructuredLoader
from langchain_community.document_loaders import(
    PyMuPDFLoader,
    TextLoader,
    Docx2txtLoader)



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def document_loader(file_path: str, mode: str = "single") -> List[Document]:
    """
    Load a single document .
    Returns a list of LangChain Document objects.
    """
    if not os.path.exists(file_path):
        logger.error(f"file not found: {file_path}")
        return []

    file_path = os.path.abspath(file_path)
    file_name = os.path.basename(file_path)

    
        # loader = PyMuPDFLoader(
        #     file_path=file_path,
        #     mode=mode
        # )
        # documents = loader.load()

    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == ".pdf":
            loader = PyMuPDFLoader(file_path)

        elif ext == ".txt":
            loader = TextLoader(file_path, encoding="utf-8")

        elif ext in [".docx"]:
            loader = Docx2txtLoader(file_path)

        else:
            logger.warning(f"Unsupported file type: {ext}")
            return []

        documents = loader.load()
                
        # Add custom metadata
        for doc in documents:
            doc.metadata["source"] = file_path
            doc.metadata["filename"] = file_name
        
        logger.info(f"✓ Loaded {len(documents)} from {file_name}")
        return documents

    except Exception as e:
        logger.error(f"✗ Error loading {file_name}: {e}")
        return []

def multiple_documents_loader(file_paths: list[str], mode: str = "single") -> List[Document]:
    """Load multiple documents."""
    
    all_documents = []
    
    logger.info(f"Loading {len(file_paths)} file(s)...")
    
    for file_path in file_paths:
        docs = document_loader(file_path, mode=mode)
        all_documents.extend(docs)
    
    logger.info(f"✓ Total documents loaded: {len(all_documents)}")
    return all_documents