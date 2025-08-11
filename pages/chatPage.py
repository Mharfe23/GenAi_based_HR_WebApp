import streamlit as st
from llms.groqClient import GroqClient
from llms.ollamaClient import OllamaClient
from services.llm_service import query_to_resume,text_to_mongo_query
from clients.mongo_client import mongo_candidat_init, get_skills_mongo
from clients.minio_client import MinioClientService

import logging
from typing import List, Dict, Any
import json
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="HR Resume Assistant",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    .example-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem;
        cursor: pointer;
        transition: transform 0.2s;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .example-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
    }
    
    .stats-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .feature-highlight {
        background: linear-gradient(45deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        margin: 0.2rem;
        font-size: 0.9rem;
    }
    
    .welcome-container {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        text-align: center;
    }
    
    .chat-container {
        background: #ffffff;
        border-radius: 15px;
        padding: 1rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_clients():
    """Initialize and cache client connections"""
    try:
        ollama_client = OllamaClient()
        groq_client = GroqClient()
        mongo_collection = mongo_candidat_init()
        minio_service = MinioClientService()
        dict_skills = get_skills_mongo()
        
        logger.info("All clients initialized successfully")
        return ollama_client, groq_client, mongo_collection, minio_service, dict_skills
    except Exception as e:
        logger.error(f"Failed to initialize clients: {e}")
        st.error(f"Failed to initialize services: {e}")
        st.stop()

def display_resumes(resumes: List[Dict[str, Any]], minio_service: MinioClientService) -> None:
    """Display resume results with enhanced formatting"""
    if not resumes:
        st.warning("🔍 No resumes found matching your criteria.")
        return
    
    st.success(f"✅ Found {len(resumes)} matching candidate(s)")
    
    # Create columns for better layout
    for i, resume in enumerate(resumes):
        with st.container():
            # Enhanced resume card styling
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Candidate header with better styling
                st.markdown(f"### 👤 {resume.get('full_name', 'Unknown')} #{resume['_id']}")
                
                # Summary
                if resume.get('summary'):
                    st.markdown("**📋 Summary:**")
                    st.write(resume['summary'])
                
                
                # Experience with icon
                if resume.get('experience_years'):
                    st.markdown(f"**⏰ Experience:** {resume['experience_years']} years")
                
                # Location if available
                if resume.get('location'):
                    st.markdown(f"**📍 Location:** {resume['location']}")
            
            with col2:
                # Enhanced download button
                try:
                    pdf = minio_service.download_file(resume["minio_file_name"])
                    pdf_data = pdf.read()
                    
                    st.download_button(
                        label="📥 Download CV",
                        data=pdf_data,
                        file_name=f"{resume.get('full_name', 'candidate')}_{resume['_id']}.pdf",
                        mime='application/pdf',
                        key=f"download_{resume['_id']}",
                        use_container_width=True,
                        type="primary"
                    )
                    
                    # File size info
                    file_size = len(pdf_data) / 1024  # KB
                    st.caption(f"📄 Size: {file_size:.1f} KB")
                    
                except Exception as e:
                    logger.error(f"Failed to prepare download for {resume['_id']}: {e}")
                    st.error("❌ Download unavailable")
            
            st.markdown("</div>", unsafe_allow_html=True)

def display_query_info(query: str) -> None:
    """Display the generated MongoDB query in an expandable section"""
    with st.expander("🔍 View Generated MongoDB Query", expanded=False):
        try:
            if query.strip().startswith('{'):
                formatted_query = json.dumps(json.loads(query), indent=2)
                st.code(formatted_query, language='json')
            else:
                st.code(query, language='text')
        except json.JSONDecodeError:
            st.code(query, language='text')

def clear_chat_history():
    """Clear chat history"""
    st.session_state.messages = []
    st.rerun()

def display_example_questions():
    """Display example questions that disappear after first user input"""
    example_questions = [
        {
            "text": "Find Python developers with 5+ years experience",
            "icon": "🐍",
            "category": "Technical"
        },
        {
            "text": "Show me candidates with machine learning skills",
            "icon": "🤖",
            "category": "AI/ML"
        },
        {
            "text": "Find senior frontend developers",
            "icon": "💻",
            "category": "Frontend"
        },
        {
            "text": "Candidates with cloud computing experience",
            "icon": "☁️",
            "category": "Cloud"
        },
        {
            "text": "Show data scientists with PhD",
            "icon": "📊",
            "category": "Data Science"
        },
        {
            "text": "Find full-stack developers",
            "icon": "🔧",
            "category": "Full-Stack"
        }
    ]
    
    st.markdown("""
    <div class="welcome-container">
        <h2>🎯 Welcome to HR Resume Assistant!</h2>
        <p>Click on any example below to get started, or type your own question in the chat input.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 💡 Try these example questions:")
    
    # Create a grid layout for example questions
    cols = st.columns(3)
    
    for i, example in enumerate(example_questions):
        col_idx = i % 3
        with cols[col_idx]:
            if st.button(
                f"{example['icon']} {example['text']}", 
                key=f"example_{i}",
                use_container_width=True,
                type="secondary"
            ):
                # Set the example question to be processed
                st.session_state.example_question = example['text']
                st.rerun()
    
    # Add some helpful tips
    st.markdown("""
    <div style="background: #e8f4fd; padding: 1rem; border-radius: 10px; margin: 2rem 0;">
        <h4>💡 Tips for better searches:</h4>
        <ul>
            <li>Be specific about skills (e.g., "React", "AWS", "Machine Learning")</li>
            <li>Mention experience level (e.g., "5+ years", "senior", "junior")</li>
            <li>Include location preferences if needed</li>
            <li>Combine multiple criteria for precise results</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def display_enhanced_sidebar(user_messages_count: int):
    """Enhanced sidebar with better styling and information"""
    with st.sidebar:
        # Logo and branding
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h2 style="color: #667eea;">⚙️ Configuration</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # LLM selection with better styling
        st.markdown("#### 🤖 AI Model Selection")
        llm_choice = st.radio(
            "",
            ("Groq API llama3.3_70B", "llama3.2 3B(local)"),
            help="Select the language model for query processing",
            key="llm_choice"
        )
        
        st.divider()
        
        # Action buttons
        st.markdown("#### 🎛️ Actions")
        if st.button("🗑️ Clear Chat History", use_container_width=True, type="primary"):
            clear_chat_history()
        
        if st.button("🔄 Refresh App", use_container_width=True):
            st.rerun()
        
        st.divider()
        
        # Enhanced statistics
        if user_messages_count > 0:
            st.markdown("#### 📊 Session Statistics")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Questions", user_messages_count, delta=None)
        
            st.divider()
        
        # Help and information
        st.markdown("#### ℹ️ Help & Info")
        with st.expander("🎯 How to use"):
            st.markdown("""
            1. **Choose AI Model**: Select between cloud or local processing
            2. **Ask Questions**: Type naturally about candidates you're looking for
            3. **Review Results**: Browse matched resumes and download CVs
            4. **Refine Search**: Ask follow-up questions to narrow results
            """)
        
        with st.expander("🔧 Features"):
            st.markdown("""
            - **Natural Language Processing**: Ask in plain English
            - **Smart Matching**: AI-powered candidate matching
            - **Resume Download**: Direct PDF downloads
            - **Real-time Results**: Instant search results
            """)
        
        return llm_choice

def ChatPage():
    """Main chat page function"""
    # Initialize clients
    ollama_client, groq_client, mongo_collection, minio_service, dict_skills = initialize_clients()
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Check if user has started chatting
    user_messages = [msg for msg in st.session_state.messages if msg["role"] == "user"]
    has_user_messages = len(user_messages) > 0
    
    # Enhanced sidebar
    llm_choice = display_enhanced_sidebar(len(user_messages))
    
    # Main page header with enhanced styling
    st.markdown('<h1 class="main-header">🤖 HR Resume Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">AI-Powered Candidate Discovery & Resume Matching</p>', unsafe_allow_html=True)
    
    # Show example questions only if user hasn't asked anything yet
    if not has_user_messages:
        display_example_questions()
    else:
        # Show a brief summary when chat has started
        st.markdown(f"""
        <div class="stats-container">
            <h4>📋 Session Summary</h4>
            <p>You've asked <strong>{len(user_messages)}</strong> questions. Continue searching or clear history to start fresh.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Select LLM client
    llm_client = groq_client if llm_choice == "Groq API llama3.3_70B" else ollama_client
    
    # Chat container with enhanced styling
    if has_user_messages:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.write(message["content"])
            else:
                # Assistant message
                st.write("**🔍 Generated Query:**")
                display_query_info(message["content"])
                
                if "resumes" in message:
                    logger.debug(f"Displaying {len(message['resumes'])} saved resumes")
                    display_resumes(message["resumes"], minio_service)
    
    if has_user_messages:
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle example question selection
    if hasattr(st.session_state, 'example_question'):
        question = st.session_state.example_question
        del st.session_state.example_question
        
        # Add user message to history
        st.session_state.messages.append({
            "role": "user",
            "content": question
        })
        
        # Process the question
        process_question(question, llm_client, mongo_collection, minio_service, dict_skills)
        st.rerun()
    
    # Chat input
    if question := st.chat_input("💬 Ask about candidates (e.g., 'I want a developer with 5+ years of experience')"):
        # Add user message to history
        st.session_state.messages.append({
            "role": "user",
            "content": question
        })
        
        # Process the question
        process_question(question, llm_client, mongo_collection, minio_service, dict_skills)
        st.rerun()

def process_question(question: str, llm_client, mongo_collection, minio_service, dict_skills):
    """Process a user question and generate response"""
    # Display user message
    with st.chat_message("user"):
        st.markdown(question)
    
    # Process and display assistant response
    with st.chat_message("assistant"):
        try:
            with st.spinner("🔄 Processing your query..."):
                # Generate MongoDB query
                query = text_to_mongo_query(question, llm_client, dict_skills)
                
                st.write("**🔍 Generated Query:**")
                display_query_info(query)
                
                # Execute query and get resumes
                resumes = query_to_resume(query, mongo_collection)
                resumes_list = list(resumes)
                
                # Display results
                display_resumes(resumes_list, minio_service)
                
                # Add assistant message to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": query,
                    "resumes": resumes_list
                })
                
                logger.info(f"Query processed successfully. Found {len(resumes_list)} results.")
                
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            st.error(f"❌ An error occurred while processing your query: {str(e)}")

if __name__ == "__main__":
    ChatPage()