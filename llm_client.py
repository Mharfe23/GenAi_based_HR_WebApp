
from groq import Groq
import os
import dotenv


dotenv.load_dotenv()


client_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def resume_to_json_with_groq(resume_text):
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

def text_to_mongo_query(text):
    prompt = f"""
    You are a professional backend assistant specializing in MongoDB.

    Given a dataset where each document represents a candidate profile, structured like this:

    - full_name: string
    - email: string or null
    - phone: string
    - address: string or null
    - skills: list of objects: {{ "technology": string, "years_experience": number or null }}
    - roles_experience: list of objects: {{ "role": string, "years_experience": number or null }}
    - current_role_experience: object {{ "role": string, "years_experience": number }}
    - education: a list of {{ "degree": string, "institution": string, "year_completed": string }}
    - certifications: a list of {{ "name": string, "year_obtained": string }}
    - projects: a list of {{ "project_name": string, "description": string }}
    summary: string
    languages_spoken: list of string
    any_other_relevant_information: object (contains optional fields like tools, personal qualities, etc.)

    IMPORTANT INSTRUCTIONS:

    Use $regex with $options: "i" for all text-based filters (e.g., skills, roles, address, certifications, project names).
    For arrays of nested objects (like skills or roles_experience), use $elemMatch.
    Use strict equality {{field: value}} only for exact numeric matching (like years of experience).
    When checking for nulls, use {{ field: null}}.
    Use dot notation for nested fields (example: "current_role_experience.role").
    Generate MongoDB json querie using this data model.

    Here is the Question {text}

    Do not return explanations — only return the json MongoDB query.
    """

    completion = client_groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content

if __name__ == "__main__": 
    print(text_to_mongo_query("i want the condidate that are good with React and flask and have 4 years of experience as full stack"))