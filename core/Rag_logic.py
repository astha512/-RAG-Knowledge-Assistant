import os
from typing import List
from pathlib import Path
from .loader import multiple_documents_loader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RagLogic:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int=200):

        #validate input

        if chunk_size<=0:
            raise ValueError("chunksize must be positive")
        
        if chunk_overlap>= chunk_size:
            raise ValueError("chunk_overlap must be less than chunksize")
        

        #textsplitter

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = chunk_size,
            chunk_overlap=chunk_overlap,
            length_function = len
        )

        #huggingface embeddings

        self.embeddings = HuggingFaceEmbeddings (
            model_name = "sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs = {"device":"cpu"},
            encode_kwargs = {"normalize_embeddings":True }
            )
            
     
        
         # Logging initialization details
        logger.info(f"✓ RagLogic initialized with model")
        logger.info(f"  Chunk size: {chunk_size}, Overlap: {chunk_overlap}")

        #step 1: load document using document loader
        #step 2: split doc into fixed size chunks


    def split_documents(self, documents: List[Document]) -> list[Document]:

            if not documents:
                logger.warning("no documents to split")
                return []
            
            #split doc
            chunks = self.text_splitter.split_documents(documents)

            #assigning chunk id per document
            chunk_id = {}
            for chunk in chunks:
                source = chunk.metadata.get('filename','unknown')

                if not source in chunk_id:
                    chunk_id[source] = 0
                    
                chunk.metadata['chunk_id'] = chunk_id[source]
                chunk_id[source] += 1

                if 'page' not in chunk.metadata:
                    chunk.metadata['page'] = (
                        chunk.metadata.get('page_number') or 
                    chunk.metadata.get('page_label') or
                    chunk.metadata.get('source_page') or
                    "N/A"
                    )

            logger.info(f"✓ Split into {len(chunks)} chunks from {len(documents)} document(s)")
            return chunks
     # load and split documents
    def process_files(self, file_paths: str | list[str], mode: str = "single") -> list[Document]:
        documents = multiple_documents_loader(file_paths, mode=mode)  # ✅ Fixed: file_paths not file_path
    
        if not documents:
            logger.warning("No documents loaded from provided files")
            return []
        
        return self.split_documents(documents)
    
    def process_file(self, file_path: str):
        return self.process_files([file_path])

   
            
