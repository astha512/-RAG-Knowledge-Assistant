import os
import streamlit as st
from .Rag_logic import RagLogic
from .vector_db import VectorDB
from typing import List,Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from .config import get_groq_api_key
from .config import (
    LLM_MODEL, 
    LLM_TEMPERATURE,
    PERSIST_DIRECTORY
)

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RagSystem:

    def __init__(self):
        #initialize raglogic and vectordb
        #validate api key first

        Groq_API_KEY = get_groq_api_key()
        if not Groq_API_KEY:
            raise ValueError("Groq_API_KEY is required")
        
        #initialize RagLogic
        # Initialize RagLogic
        logger.info("Loading document processor...")
        self.rag_logic = RagLogic()

        # initialize vectordb
        logger.info("loading vector database..")
        self.vector_db = VectorDB(
            rag_logic=self.rag_logic,
            persist_directory=PERSIST_DIRECTORY
        )
        logger.info("vectordb initialized")

        #initialize LLM

        logger.info(f"loading LLM:{LLM_MODEL}..")
        self.llm = ChatGroq(
            api_key=Groq_API_KEY,
            model = LLM_MODEL,
            temperature=LLM_TEMPERATURE
        )
        logger.info(f"llm initialized:{LLM_MODEL}")

        #initialize query chain
        self._initialize_qa_chain()

    def _initialize_qa_chain(self):
        '''initialize the question-answering chain using LCEL(langchain exp lang)'''


        #check if vector store is initialized

        if not self.vector_db.vector_store:
            logger.warning('vectorestore is not initialzed add document first')
            self.retriever= None
            self.qa_chain = None
            return
        
        #create retriver

        try:
            self.retriever = self.vector_db.vector_store.as_retriever(
                search_kwargs={"k":3}
            )
            logger.info("Retriver created")
        except Exception as e:
            logger.error(f" error creating retriver:{e}")
            self.retriever = None
            self.qa_chain = None
            return
        
        prompt = ChatPromptTemplate.from_template(
            """
            You are a helpful assistant.
            Answer the question ONLY using the context below.

            Context:
            {context}

            Question:
            {input}
            """
            )
        #create chain

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        try:
            self.qa_chain = (
                {
                    "context": self.retriever|format_docs,
                    "input":RunnablePassthrough()
                }
                |prompt|self.llm|StrOutputParser()
            )
            logger.info("QA chain initialized")

        except Exception as e:
            logger.error(f"error creating QA chain:{e}")
            self.qa_chain = None
#=====================================================================
    def add_document(self, file_path: str) -> bool:
        '''
        add a single document to the system
        '''
        success = self.vector_db.process_and_add_file(file_path)

        #reinitialize QA chain if this was the first document
        if success and self.qa_chain is None:
            logger.info("Reinitializing QA chain after adding first document..")
            self._initialize_qa_chain()

        return success
        
    def add_documents(self, file_paths: List[str]) -> bool:
        """Add multiple documents to the system."""
        success = self.vector_db.process_and_add_files(file_paths)
        
        # Reinitialize QA chain if this was the first batch
        if success and self.qa_chain is None:
            logger.info("Reinitializing QA chain after adding documents...")
            self._initialize_qa_chain()
        
        return success
#=======================================================================

    def ask_question(self, question: str, top_k = 3) -> Dict:
        
        '''
        1. ask question and get answers 
        2. question should not be empty
        3. retreive top_k answers
        '''
        if not question.strip():
            logger.warning("Empty question provided")
            return {"answer": "Please provide a valid question.", "context": []}
        
        # Check if QA chain is initialized
        if self.qa_chain is None:
            logger.error("QA chain not initialized. Please add documents first.")
            return {
                "answer": "No documents indexed. Please add documents before asking questions.",
                "context": []
            }
        
        try:
            # Update retriever k
            self.retriever.search_kwargs["k"] = top_k
            
            # Get relevant documents
            logger.info(f"Processing question: {question}")
            docs = self.retriever.invoke(question)
            
            # Get answer
            answer = self.qa_chain.invoke(question)
            
            logger.info(f"✓ Answer generated with {len(docs)} sources")
            
            return {
                "answer": answer,
                "context": docs
            }
        
        except Exception as e:
            logger.error(f"✗ Error answering question: {e}")
            return {"answer": f"Error: {str(e)}", "context": []}




    # def ask_question(self, question: str, top_k=3) -> Dict:
    #     print("DEBUG ask_question called")

    #     return {
    #         "answer": "Test answer",
    #         "context": []
    #     }


#-----------------------------------------------------------------------------------------------------        
    # def ask_with_sources(self, question: str, top_k: int = 3) -> Dict:
    #     result = self.ask_question(question, top_k)

    #     sources = []
    #     for doc in result.get("context", []):
    #         # Try multiple possible keys for page number
    #         page_num = (
    #             doc.metadata.get("page") or 
    #             doc.metadata.get("page_number") or 
    #             doc.metadata.get("page_label") or
    #             "N/A"
    #         )
    #         source_info = {
    #             "filename": doc.metadata.get("filename") or doc.metadata.get("source", "Unknown"),
    #             "page": page_num,
    #             "chunk_id": doc.metadata.get("chunk_id", "N/A"),
    #             "content": doc.page_content[:1000] + "..." if len(doc.page_content) > 1000 else doc.page_content,
    #             "all_metadata": doc.metadata  # Temporary: to see all metadata
    #         }
    #         sources.append(source_info)

    #         return {
    #         "answer": result.get("answer", "No answer generated"),
    #         "sources": sources
    #     } 

    def ask_with_sources(self, question: str, top_k: int = 3) -> Dict:

        result = self.ask_question(question, top_k)

        
        if not result:
            return {
                "answer": "⚠️ Please upload and process documents first.",
                "sources": []
            }

        sources = []

        for doc in result.get("context", []):
            page_num = (
                doc.metadata.get("page") or 
                doc.metadata.get("page_number") or 
                doc.metadata.get("page_label") or
                "N/A"
            )

            source_info = {
                "filename": doc.metadata.get("filename") or doc.metadata.get("source", "Unknown"),
                "page": page_num,
                "chunk_id": doc.metadata.get("chunk_id", "N/A"),
                "content": doc.page_content[:1000] + "..." 
                        if len(doc.page_content) > 1000 
                        else doc.page_content,
            }

            sources.append(source_info)

        # 
        return {
            "answer": result.get("answer", "No answer generated"),
            "sources": sources
        }

