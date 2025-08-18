import streamlit as st
import base64
from clients.mongo_client import mongo_candidat_init
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
        search_query = st.text_input("🔍 Search by name, email, role or summary").lower()
    
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
    filtered_resumes = [
        c for c in resumes
        if (not search_query or 
            search_query in (c.get("full_name") or "").lower()
            or (
            isinstance(c.get("email"), list)
            and any(search_query in (email or "").lower() for email in c["email"])
            )
            or (
                isinstance(c.get("email"), str)
                and search_query in (email or "").lower()
            )
            or search_query in (c.get("current_role_experience", {}).get("role", "") or "").lower()
            or search_query in (c.get("summary") or "").lower())
        and (selected_job_offer == "All Job Offers" or c.get("job_offer") == selected_job_offer)
    ]
    
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

    for index, pdf_info in enumerate(filtered_resumes):
        # Load PDF
        # Metadata display
        max_experience = max(pdf_info['roles_experience'],key=lambda x:x['years_experience'])
        st.subheader(f"📄 {max_experience["role"]} : {max_experience["years_experience"]}  years of experience")
        st.write(f"**Author:** {pdf_info.get('full_name')}")
        st.write(f"**Overview:** {pdf_info['summary']}")
        
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
            file_name=f"{pdf_info["full_name"]}_{pdf_info['_id']}.pdf",
            mime='application/pdf',
            key=f"download_button_{index}"  # Ensure unique keys
        )

        st.markdown("---")
