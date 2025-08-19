import streamlit as st
import base64
from clients.mongo_client import mongo_candidat_init, get_skills_mongo
from clients.minio_client import MinioClientService
# Example list of PDFs with metadata
from streamlit_pdf_viewer import pdf_viewer

def listResume():
    st.title("📚 Resume Library")

    collection = mongo_candidat_init()
    minio = MinioClientService()
    if "resumes" not in st.session_state:
        st.session_state.resumes = list(collection.find())
    
    st.title("📄 Candidate Table with PDF Preview")
    
    # Search and filter section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**🛠 Advanced Filters**")
        name_filter = st.text_input("Filter by Name (contains):", key="list_name_filter").strip().lower()
        role_filter = st.text_input("Filter by Role (contains):", key="list_role_filter").strip().lower()
        # Skills filter: load from Mongo skills dictionary
        try:
            skills_dict = get_skills_mongo()
        except Exception:
            st.error("Error loading skills dictionary")
            skills_dict = []
        selected_skills = st.multiselect(
            "Filter by Skills:",
            options=sorted(skills_dict),
            help="Choose one or more skills from the reference dictionary",
            key="list_skills_filter"
        )
        skill_match_mode = st.radio(
            "Match Mode:",
            options=["Any", "All"],
            horizontal=True,
            help="Any: candidate has at least one selected skill. All: candidate has all selected skills.",
            key="list_skills_match_mode"
        )
        email_filter = st.text_input("Filter by Email (contains):", key="list_email_filter").strip().lower()
        summary_filter = st.text_input("Filter by Summary Keyword:", key="list_summary_filter").strip().lower()
    
    with col2:
        # Job offer filter
        job_offers = ["All Job Offers"] + list(set([c.get("job_offer", "No Job Offer") for c in st.session_state.resumes if c.get("job_offer")]))
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

    resumes = st.session_state.resumes
    filtered_resumes = []
    for c in resumes:
        # Name filter
        name_match = True
        if name_filter:
            name_match = name_filter in (c.get("full_name") or "").lower()

        # Email filter (contains)
        email_match = True
        if email_filter:
            if isinstance(c.get("email"), list):
                email_match = any(email_filter in (e or "").lower() for e in c["email"])
            else:
                email_match = email_filter in (c.get("email") or "").lower()

        # Role filter
        role_match = True
        if role_filter:
            role_match = role_filter in (c.get("current_role_experience", {}).get("role", "") or "").lower()

        # Summary keyword filter
        summary_match = True
        if summary_filter:
            summary_match = summary_filter in (c.get("summary") or "").lower()

        # Job offer filter
        job_offer_match = (selected_job_offer == "All Job Offers" or c.get("job_offer") == selected_job_offer)

        # Skills filter
        skills_match = True
        if selected_skills:
            # Extract techs from candidate
            candidate_techs = []
            try:
                for s in c.get("skills", []):
                    tech = (s.get("technology") or "").strip().lower()
                    if tech:
                        candidate_techs.append(tech)
            except Exception:
                candidate_techs = []

            selected_skills_norm = [s.strip().lower() for s in selected_skills]
            if skill_match_mode == "All":
                skills_match = all(s in candidate_techs for s in selected_skills_norm)
            else:
                skills_match = any(s in candidate_techs for s in selected_skills_norm)

        if name_match and email_match and role_match and summary_match and job_offer_match and skills_match:
            filtered_resumes.append(c)
    
    # Apply date filtering if job offer is selected and dates are specified
    if selected_job_offer != "All Job Offers" and start_date and end_date:
        from datetime import datetime
        # Filter by date range
        date_filtered_resumes = []
        for c in filtered_resumes:
            if c.get("job_offer_date"):
                try:
                    job_date = datetime.fromisoformat(c["job_offer_date"]).date()
                    if start_date <= job_date <= end_date:
                        date_filtered_resumes.append(c)
                except (ValueError, TypeError):
                    continue
        filtered_resumes = date_filtered_resumes

    # Notify when filters are applied
    active_filters = []
    if name_filter:
        active_filters.append(f"Name contains '{name_filter}'")
    if email_filter:
        active_filters.append(f"Email contains '{email_filter}'")
    if role_filter:
        active_filters.append(f"Role contains '{role_filter}'")
    if summary_filter:
        active_filters.append(f"Summary contains '{summary_filter}'")
    if selected_skills:
        mode_txt = "all" if skill_match_mode == "All" else "any"
        active_filters.append(f"Skills ({mode_txt}): {', '.join(selected_skills)}")
    if selected_job_offer != "All Job Offers":
        active_filters.append(f"Job Offer: {selected_job_offer}")
        if start_date and end_date:
            active_filters.append(f"Date: {start_date} → {end_date}")

    if active_filters:
        msg = " | ".join(active_filters) + f"  •  {len(filtered_resumes)} result(s)"
        toast_fn = getattr(st, "toast", None)
        if callable(toast_fn):
            toast_fn(msg)
        else:
            st.info(msg)

    for index, pdf_info in enumerate(filtered_resumes):
        # Load PDF
        # Metadata display
        max_experience = max(pdf_info['roles_experience'], key=lambda x: x.get('years_experience', 0)) if pdf_info.get('roles_experience') else {"role": "", "years_experience": 0}
        st.subheader(f"📄 {max_experience['role']} : {max_experience['years_experience']} years of experience")
        st.write(f"**Author:** {pdf_info.get('full_name')}")
        st.write(f"**Overview:** {pdf_info.get('summary', '')}")
        
        # Job offer information
        if pdf_info.get('job_offer'):
            st.write(f"**💼 Job Offer:** {pdf_info['job_offer']}")
        if pdf_info.get('job_offer_date'):
            st.write(f"**📅 Job Offer Date:** {pdf_info['job_offer_date']}")

        pdf = minio.download_file(pdf_info["minio_file_name"])
        pdf_data = pdf.read()
        
        pdf_viewer(
            pdf_data,
            
            height=350
        )

        # Download button
        st.download_button(
            label="📥 Download PDF",
            data=pdf_data,
            file_name=f"{pdf_info['full_name']}_{pdf_info['_id']}.pdf",
            mime='application/pdf',
            key=f"download_button_{index}"  # Ensure unique keys
        )

        st.markdown("---")
