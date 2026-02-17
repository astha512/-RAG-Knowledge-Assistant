import streamlit as st
import os
from core.main import RagSystem
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

try:
    api_key = st.secrets.get("GROQ_API_KEY")
except Exception:
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("Groq API key not found")
    st.stop()

client = Groq(api_key=api_key)

# Page configuration
st.set_page_config(
    page_title="RAG Knowledge Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🤖 RAG Knowledge Assistant")

# Initialize session state
# st.session_state.rag_system = RagSystem()

if 'rag_system' not in st.session_state:
    with st.spinner("🔄 Initializing RAG system..."):
        try:
            st.session_state.rag_system = RagSystem()
            st.session_state.initialized = True
        except Exception as e:
            st.error(f"❌ Error initializing system: {e}")
            st.session_state.initialized = False

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []


# Sidebar
with st.sidebar:
    st.header("📁 Document Management")
    
    # Upload documents
    uploaded_files = st.file_uploader(
        "Upload Documents",
        type=['pdf', 'docx', 'txt'],
        accept_multiple_files=True,
        help="Upload PDF, DOCX, or TXT files"
    )
    
    if uploaded_files:
        if st.button("📤 Process Uploaded Files", type="primary"):
            with st.spinner("Processing documents..."):
                for uploaded_file in uploaded_files:
                    # Save to temp directory
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Add to RAG system
                    success = st.session_state.rag_system.add_document(temp_path)
                    
                    if success:
                        st.success(f"✅ {uploaded_file.name}")
                    else:
                        st.error(f"❌ Failed: {uploaded_file.name}")
                    
                    # Clean up
                    os.remove(temp_path)
    
    st.divider()

    # Settings
    st.header("⚙️ Settings")
    top_k = st.slider("Number of sources", 1, 10, 4)
        
    if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

# Main area - Q&A
st.header("💬 Ask Questions")

# Display chat history
for chat in st.session_state.chat_history:
    # User question
    with st.chat_message("user"):
        st.write(chat['question'])
# Assistant answer
    with st.chat_message("assistant"):
        st.markdown(f'<div >{chat["answer"]}</div>', unsafe_allow_html=True)
        
        # Show sources
        if chat.get('sources'):
            with st.expander(f"📚 Sources ({len(chat['sources'])})"):
                for i, source in enumerate(chat['sources'], 1):
                    st.markdown(f"""
                    <div>
                        <strong>Source {i}: {source['filename']}</strong><br>
                        Page: {source['page']} | Chunk: {source['chunk_id']}<br>
                        <em>{source['content'][:150]}...</em>
                    </div>
                    """, unsafe_allow_html=True)


# Question input
if st.session_state.initialized:
    question = st.chat_input("Ask a question about your documents...")
    
    if question:
        # Add user message
        with st.chat_message("user"):
            st.write(question)
        
        # Get answer
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                result = st.session_state.rag_system.ask_with_sources(question, top_k=top_k)

            
                st.markdown(f'<div>{result["answer"]}</div>', unsafe_allow_html=True)
                
                #Display sources
                if result.get('sources'):
                    with st.expander(f"📚 Sources ({len(result['sources'])})"):
                        for i, source in enumerate(result['sources'], 1):
                            st.markdown(f"""
                            <div >
                                <strong>Source {i}: {source['filename']}</strong><br>
                                Page: {source['page']} | Chunk: {source['chunk_id']}<br>
                                <em>{source['content'][:150]}...</em>
                            </div>
                            """, unsafe_allow_html=True)
        
        # Save to history
        st.session_state.chat_history.append({
            'question': question,
            'answer': result['answer'],
            'sources': result.get('sources', [])
        })
else:
    st.warning("⚠️ System not initialized. Check the error messages above.")
