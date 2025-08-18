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

    # 1. SEARCH AND FILTERS
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_query = st.text_input("🔍 Search by name, email, role or summary").lower()
    
    with col2:
        # Job offer filter
        job_offers = ["All Job Offers"] + list(set([c.get("job_offer", "No Job Offer") for c in candidates if c.get("job_offer")]))
        selected_job_offer = st.selectbox("💼 Filter by Job Offer:", job_offers)
        
        # Date range filter for job offers
        if selected_job_offer != "All Job Offers":
            st.markdown("**📅 Filter by Date Range:**")
            col_date1, col_date2 = st.columns(2)
            with col_date1:
                from datetime import date, timedelta
                start_date = st.date_input(
                    "From Date:",
                    value=date.today() - timedelta(days=30),
                    help="Show resumes from this date onwards"
                )
            with col_date2:
                end_date = st.date_input(
                    "To Date:",
                    value=date.today(),
                    help="Show resumes up to this date"
                )
        else:
            start_date = None
            end_date = None
    
    filtered_candidates = candidates
    
    # 2. FILTER
    if search_query or selected_job_offer != "All Job Offers":
        filtered_candidates = [
            c for c in candidates
            if (not search_query or 
                search_query in (c.get("full_name") or "").lower()
                or (
                isinstance(c.get("email"), list)
                and any(search_query in (email or "").lower() for email in c["email"])
                )
                or (
                    isinstance(c.get("email"), str)
                    and search_query in (c.get("email") or "").lower()
                )
                or search_query in (c.get("current_role_experience", {}).get("role", "") or "").lower()
                or search_query in (c.get("summary") or "").lower())
            and (selected_job_offer == "All Job Offers" or c.get("job_offer") == selected_job_offer)
        ]
        
        # Apply date filtering if job offer is selected and dates are specified
        if selected_job_offer != "All Job Offers" and start_date and end_date:
            from datetime import datetime
            # Filter by date range
            date_filtered_candidates = []
            for c in filtered_candidates:
                if c.get("job_offer_date"):
                    try:
                        job_date = datetime.fromisoformat(c["job_offer_date"]).date()
                        if start_date <= job_date <= end_date:
                            date_filtered_candidates.append(c)
                    except (ValueError, TypeError):
                        continue
            filtered_candidates = date_filtered_candidates
        

    # Extract summary table
    summary_rows = []
    for c in filtered_candidates:
        summary_rows.append({
            "Name": c.get("full_name", ""),
            "Email": c.get("email", ""),
            "Phone": c.get("phone", ""),
            "Job Offer": c.get("job_offer", "No Job Offer"),
            "Job Offer Date": c.get("job_offer_date", ""),
            "Current Role": c.get("current_role_experience", {}).get("role", ""),
            "Current Exp (yrs)": c.get("current_role_experience", {}).get("years_experience", ""),
            "Summary": (c.get("summary","") or ""),
            "skills": list({skill["technology"] for skill in c["skills"]})
        })

    summary_df = pd.DataFrame(summary_rows)

    # Show filtering summary
    if selected_job_offer != "All Job Offers":
        st.info(f"🔍 **Filtering Results:** Showing candidates for job offer: **{selected_job_offer}**")
        if start_date and end_date:
            st.info(f"📅 **Date Range:** From {start_date} to {end_date}")
        st.info(f"📊 **Total Results:** {len(filtered_candidates)} candidates found")
    
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
            st.markdown(f"**Job Offer**: {candidate.get('job_offer', 'No Job Offer')}")
            st.markdown(f"**Job Offer Date**: {candidate.get('job_offer_date', '')}")
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