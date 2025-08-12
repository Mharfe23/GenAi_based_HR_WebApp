import streamlit as st
import pandas as pd
from typing import List, Dict, Any
import logging
import pandas as pd
import plotly.express as px
from clients.mongo_client import (
    get_skills_mongo, 
    add_new_skills_mongo, 
    replace_all_technologies,
    get_skills_statistics,
)
from embeddings.chroma_gemini_embedding import (
    add_unique_skills_to_chroma, 
    remove_skills_chroma,
    get_all_skills_chroma,
)
from services.dictionaire_service import (
    delete_skills_from_mongo_chroma,
    init_primary_skills_in_dict,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_skills_with_status() -> Dict[str, List[str]]:
    """Get skills from both databases and identify sync status"""
    try:
        mongo_skills = set(get_skills_mongo())
        chroma_skills = set(get_all_skills_chroma())
        skills = mongo_skills | chroma_skills
        return {
            "skills": list(skills),
            "total_count": len(skills)
        }
    except Exception as e:
        logger.error(f"Error getting skills: {e}")
        st.error(f"Error retrieving skills: {e}")
        return {"mongo_skills": [], "total_count": 0}

def add_skills_to_both_databases(skills_list: List[str]) -> Dict[str, Any]:
    """Add skills to both MongoDB and ChromaDB"""
    result = {"success": False, "message": "", "added_count": 0}
    
    try:
        add_new_skills_mongo(skills_list)
        add_unique_skills_to_chroma(skills_list)
        
        result["success"] = True
        result["message"] = f"✅ Successfully added {len(skills_list)} skills to both databases"
        result["added_count"] = len(skills_list)
        
    except Exception as e:
        result["message"] = f"❌ Error adding skills: {str(e)}"
        logger.error(f"Error adding skills: {e}")
    
    return result

def remove_skills_from_both_databases(skills_list: List[str]) -> Dict[str, Any]:
    """Remove skills from both MongoDB and ChromaDB"""
    result = {"success": False, "message": "", "removed_count": 0}
    
    try:
        delete_skills_from_mongo_chroma(skills_list)
        
        result["success"] = True
        result["message"] = f"✅ Successfully removed {len(skills_list)} skills from both databases"
        result["removed_count"] = len(skills_list)
        
    except Exception as e:
        result["message"] = f"❌ Error removing skills: {str(e)}"
        logger.error(f"Error removing skills: {e}")
    
    return result

def sync_databases_with_primary_skills() -> Dict[str, Any]:
    """Initialize both databases with primary skills"""
    result = {"success": False, "message": "", "skills_count": 0}
    
    try:
        init_primary_skills_in_dict()
        updated_skills = get_skills_mongo()
        
        result["success"] = True
        result["message"] = f"✅ Successfully synchronized both databases with {len(updated_skills)} primary skills"
        result["skills_count"] = len(updated_skills)
        
    except Exception as e:
        result["message"] = f"❌ Error synchronizing databases: {str(e)}"
        logger.error(f"Error synchronizing databases: {e}")
    
    return result

def display_skills_table(skills: List[str], title: str):
    """Display skills in a formatted table"""
    if not skills:
        st.warning(f"No skills found in {title}")
        return
    
    df = pd.DataFrame({
        "Skill": skills,
    })
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    csv = df.to_csv(index=False)
    st.download_button(
        f"⬇️ Download {title} CSV",
        csv,
        f"{title.lower().replace(' ', '_')}.csv",
        "text/csv"
    )
def skills_statistics():
    
    #skills dashboard
    skill_stats = get_skills_statistics()

    data = []
    for res in skill_stats:
        data.append({
            "Technology": res["_id"],
            "Number of Resumes": res["nombre_cv"],
        })

    df = pd.DataFrame(data)

    # 📈 Graphique
    if not df.empty:
        fig = px.bar(df, x="Technology", y="Number of Resumes", title="Number of Resumes per technology", height=400)
        st.plotly_chart(fig, use_container_width=True)

        csv = df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            "SkillPerResume.csv",
            "text/csv",
            key="sidebar_download"
        )

    
    else:
        st.warning("Aucune technologie trouvée.")


def SkillsManagementPage():
    """Main skills management page function"""
    st.set_page_config(
        page_title="Skills Management",
        page_icon="🛠️",
        layout="wide"
    )
    
    # Custom CSS for enhanced styling
    st.markdown("""
    <style>
        .skills-header {
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
        
        .stats-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            text-align: center;
        }
        
        .success-card {
            background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
        
        .warning-card {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
        
        .error-card {
            background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)
    # Header
    st.markdown('<h1 class="skills-header">🛠️ Skills Management</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Manage skills across MongoDB and ChromaDB databases</p>', unsafe_allow_html=True)
    skills_statistics()
    
    # Get current skills
    skills_data = get_skills_with_status()
    current_skills = skills_data["skills"]
    total_skills = skills_data["total_count"]
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📊 Database Status")
        st.metric("Total Skills", total_skills)
        
        st.divider()
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
        
        if st.button("📥 Export All Skills", use_container_width=True):
            if current_skills:
                df = pd.DataFrame({"Skill": current_skills})
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    "all_skills.csv",
                    "text/csv",
                    key="sidebar_download"
                )
        
        st.divider()
        
        # Help
        st.markdown("### ℹ️ Help")
        with st.expander("How to use"):
            st.markdown("""
            1. **View Skills**: See all current skills in the database
            2. **Add Skills**: Add individual or multiple skills
            3. **Remove Skills**: Select and remove unwanted skills
            4. **Replace Skills**: Completely replace the skills list
            5. **Sync Databases**: Ensure MongoDB and ChromaDB are synchronized
            """)
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Current skills display
        st.markdown("### 📋 Current Skills")
        
        if current_skills:
            search_term = st.text_input("🔍 Search skills:", placeholder="Type to filter skills...")
            
            if search_term:
                filtered_skills = [skill for skill in current_skills if search_term.lower() in skill.lower()]
                st.info(f"Found {len(filtered_skills)} skills matching '{search_term}'")
                display_skills_table(filtered_skills, f"Filtered Skills ({len(filtered_skills)})")
            else:
                display_skills_table(current_skills, f"All Skills ({len(current_skills)})")
        else:
            st.info("No skills found. Use the 'Add Skills' section to get started.")
    
    with col2:
        st.markdown("### 📊 Statistics")
        
        # Total skills card
        st.markdown(f"""
        <div class="stats-card">
            <h3>Total Skills</h3>
            <h2>{total_skills}</h2>
            <p>Across both databases</p>
        </div>
        """, unsafe_allow_html=True)
        
        if current_skills:
            categories = {
                "Programming": len([s for s in current_skills if any(tech in s.lower() for tech in ["python", "java", "javascript", "c++", "c#", "go", "rust"])]),
                "Web Dev": len([s for s in current_skills if any(tech in s.lower() for tech in ["html", "css", "react", "angular", "vue", "node"])]),
                "Database": len([s for s in current_skills if any(tech in s.lower() for tech in ["mysql", "mongodb", "postgresql", "redis"])]),
                "Cloud": len([s for s in current_skills if any(tech in s.lower() for tech in ["aws", "azure", "gcp", "docker", "kubernetes"])])
            }
            
            for category, count in categories.items():
                if count > 0:
                    st.metric(category, count)
    
    # Action sections
    st.markdown("---")
    
    # Add skills section
    st.markdown("### ➕ Add New Skills")
    
    with st.expander("Add Individual Skills", expanded=False):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            new_skill = st.text_input("Enter skill name:", placeholder="e.g., FastAPI, Kubernetes")
        
        with col2:
            if st.button("Add Skill"):
                if new_skill.strip():
                    result = add_skills_to_both_databases([new_skill.strip()])
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
                else:
                    st.warning("Please enter a skill name")
    
    with st.expander("Add Multiple Skills", expanded=False):
        skills_text = st.text_area("Enter skills (one per line or comma-separated):", height=150)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("Add from Text"):
                if skills_text.strip():
                    skills_list = []
                    for line in skills_text.split('\n'):
                        for skill in line.split(','):
                            skill_clean = skill.strip()
                            if skill_clean:
                                skills_list.append(skill_clean)
                    
                    if skills_list:
                        result = add_skills_to_both_databases(skills_list)
                        if result["success"]:
                            st.success(result["message"])
                            st.rerun()
                        else:
                            st.error(result["message"])
                    else:
                        st.warning("No valid skills found")
                else:
                    st.warning("Please enter skills")
        
        with col2:
            if st.button("Add Primary Skills"):
                with st.spinner("Adding primary skills..."):
                    result = sync_databases_with_primary_skills()
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
    
    # Remove skills section
    if current_skills:
        st.markdown("### 🗑️ Remove Skills")
        
        with st.expander("Remove Selected Skills", expanded=False):
            skills_to_remove = st.multiselect(
                "Select skills to remove:",
                options=current_skills
            )
            
            if skills_to_remove:
                if st.button("Remove Selected"):
                    result = remove_skills_from_both_databases(skills_to_remove)
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
    
    # Replace skills section
    st.markdown("### 🔄 Replace All Skills")
    
    with st.expander("Replace Skills List", expanded=False):
        st.warning("⚠️ This will completely replace the current skills list!")
        
        replacement_skills = st.text_area("Enter new skills list:", height=150)
        
        if st.button("Replace All Skills", type="secondary"):
            if replacement_skills.strip():
                skills_list = []
                for line in replacement_skills.split('\n'):
                    for skill in line.split(','):
                        skill_clean = skill.strip()
                        if skill_clean:
                            skills_list.append(skill_clean)
                
                if skills_list:
                    try:
                        replace_all_technologies(skills_list)
                        st.success(f"✅ Successfully replaced skills with {len(skills_list)} new skills")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error replacing skills: {str(e)}")
                else:
                    st.warning("No valid skills found")
            else:
                st.warning("Please enter skills")
    
    # Database sync section
    st.markdown("### 🔄 Database Synchronization")
    
    with st.expander("Sync Operations", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Sync with Primary Skills"):
                with st.spinner("Synchronizing databases..."):
                    result = sync_databases_with_primary_skills()
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
            
            if st.button("🔧 Force Database Sync"):
                with st.spinner("Forcing database synchronization..."):
                    try:
                        # Get current skills from MongoDB
                        mongo_skills = get_skills_mongo()
                        
                        # Clear and re-add to ChromaDB
                        if mongo_skills:
                            # Remove all from ChromaDB first
                            chroma_skills = get_all_skills_chroma()
                            if chroma_skills:
                                remove_skills_chroma(chroma_skills)
                            
                            # Re-add all from MongoDB
                            add_unique_skills_to_chroma(mongo_skills)
                            
                            st.success(f"✅ Forced sync completed! Both databases now contain {len(mongo_skills)} skills")
                            st.rerun()
                        else:
                            st.warning("No skills in MongoDB to sync")
                    except Exception as e:
                        st.error(f"❌ Error during forced sync: {str(e)}")
        
        with col2:
            if st.button("📊 Check Sync Status"):
                try:
                    mongo_skills = get_skills_mongo()
                    chroma_skills = get_all_skills_chroma()
                    
                    st.info(f"📊 MongoDB contains {len(mongo_skills)} skills")
                    st.info(f"🔄 ChromaDB contains {len(chroma_skills)} skills")
                    
                    # Check sync status
                    mongo_set = set(mongo_skills)
                    chroma_set = set(chroma_skills)
                    
                    if mongo_set == chroma_set:
                        st.success("✅ Databases are perfectly synchronized!")
                    elif mongo_set.issubset(chroma_set):
                        st.warning("⚠️ ChromaDB has more skills than MongoDB")
                        for skill in (chroma_set - mongo_set):
                            st.write(f"• {skill}")
                    elif chroma_set.issubset(mongo_set):
                        st.warning("⚠️ MongoDB has more skills than ChromaDB")
                        for skill in (mongo_set - chroma_set):
                            st.write(f"• {skill}")
                    else:
                        st.error("❌ Databases are out of sync")
                    
                            
                except Exception as e:
                    st.error(f"Error checking sync status: {e}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>🔄 Changes are automatically synchronized between MongoDB and ChromaDB</p>
        <p>💡 Use the search and filter features to manage large skill sets efficiently</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    SkillsManagementPage()
