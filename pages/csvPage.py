import streamlit as st
import json
import pandas as pd
from clients.mongo_client import mongo_candidat_init

def CsvPage():

    st.set_page_config(layout="wide")
    st.title("📋 Candidate Viewer & CSV Exporter")

    # Simulate loading candidates (in real case, load from DB or file)
    # Paste or load your full JSON array here
    collection_candidat = mongo_candidat_init()
    candidates = list(collection_candidat.find())

    # 1. SEARCH
    st.title("📄 Candidate Table with PDF Preview")
    search_query = st.text_input("🔍 Search by name, email or role").lower()
    filtered_candidates = candidates
    
    # 2. FILTER
    if search_query is not None:
        filtered_candidates = [
            c for c in candidates
            if search_query in (c.get("full_name") or "").lower()
            or search_query in (c.get("email") or "").lower()
            or search_query in (c.get("current_role_experience") or "").lower()
        ]

    # Extract summary table
    summary_rows = []
    for c in filtered_candidates:
        summary_rows.append({
            "Name": c.get("full_name", ""),
            "Email": c.get("email", ""),
            "Phone": c.get("phone", ""),
            "Current Role": c.get("current_role_experience", {}).get("role", ""),
            "Current Exp (yrs)": c.get("current_role_experience", {}).get("years_experience", ""),
            "Summary": c.get("summary",""),
        })

    summary_df = pd.DataFrame(summary_rows)

    # Show summary table
    st.subheader("📊 Candidate Overview")
    st.dataframe(summary_df)

    # Download summary
    csv = summary_df.to_csv(index=False)
    st.download_button("⬇️ Download Summary CSV", csv, "candidates_summary.csv", "text/csv")

    st.markdown("---")

    # Show detailed info per candidate
    st.subheader("🧾 Candidate Details")
    for idx, candidate in enumerate(filtered_candidates):
        with st.expander(f"{idx+1}. {candidate.get('full_name', 'Unnamed')}"):
            st.markdown(f"**Email**: {candidate.get('email', '')}")
            st.markdown(f"**Phone**: {candidate.get('phone', '')}")
            st.markdown(f"**Summary**:{candidate.get("summary","")}")
            st.markdown(f"**Current Role**: {candidate.get('current_role_experience', {}).get('role', '')}")
            st.markdown(f"**Years in Current Role**: {candidate.get('current_role_experience', {}).get('years_experience', '')}")
            
            for section in ["skills", "roles_experience", "education"]:
                if section in candidate:
                    st.markdown(f"**{section.replace('_', ' ').title()}**")
                    data = candidate[section]

                    # Deduplicate "skills" by technology name (case-insensitive)
                    if section == "skills":
                        seen = set()
                        unique_skills = []
                        for skill in data:
                            tech = skill.get("technology", "").strip().lower()
                            if tech and tech not in seen:
                                seen.add(tech)
                                unique_skills.append(skill)
                        df = pd.DataFrame(unique_skills)
                    else:
                        df = pd.DataFrame(data)

                    st.dataframe(df, use_container_width=True)