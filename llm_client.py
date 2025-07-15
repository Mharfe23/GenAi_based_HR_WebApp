
from groq import Groq
import os
import dotenv


dotenv.load_dotenv()


client_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def extract_with_groq(resume_text):
    prompt = f"""
You are a professional recruiter assistant.

Given the following resume text, extract ALL useful candidate information and return it STRICTLY as a well-formatted JSON object with no extra explanations.

Include at least the following fields:
- full_name
- email
- phone
- address (if available)
- skills: a list of {{ "technology": string, "years_experience": number }}
- roles_experience: a list of {{ "role": string, "years_experience": number }}
- current_role_experience: {{"role": number}}
- education: a list of {{ "degree": string, "institution": string, "year_completed": string }}
- certifications: a list of {{ "name": string, "year_obtained": string }}
- projects: a list of {{ "project_name": string, "description": string }}
- summary: a brief professional summary (string)
- languages_spoken: list of languages (if mentioned)
- any_other_relevant_information: capture anything else useful for recruiter decisions 

Important Constraints:
- Output ONLY a valid JSON object, nothing else.
- Include "years_experience" wherever possible in both technologies and roles.
- If certain fields are not present, use an empty array or null.

Here is the resume text:

{resume_text}
"""
    completion = client_groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content
