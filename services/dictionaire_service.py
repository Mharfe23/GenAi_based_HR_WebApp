from clients.mongo_client import get_skills_mongo, add_new_skills_mongo, init_techs_if_not_exist_mongo,remove_skills_mongo
from embeddings.chroma_gemini_embedding import add_unique_skills_to_chroma, find_similar_skill,remove_skills_chroma
import logging

logging.basicConfig(
    level=logging.WARNING,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


primary_skills = [
    # programming languages
    "python", "java", "c++", "c#", "javascript", "typescript", "go (golang)", "rust", "kotlin", "swift", "sql", "bash",

    # web development
    "html", "css", "react.js", "angular", "vue.js", "next.js", "node.js", "express.js", "django", "flask", "spring boot",

    # databases
    "mysql", "postgresql", "sqlite", "mongodb", "redis", "oracle database", "microsoft sql server",

    # devops & ci/cd
    "docker", "kubernetes", "jenkins", "github actions", "gitlab ci/cd", "terraform", "ansible", "circleci",

    # cloud platforms
    "amazon web services (aws)", "microsoft azure", "google cloud platform (gcp)", "firebase", "heroku", "vercel", "netlify",

    # version control
    "git", "github", "gitlab", "bitbucket",

    # testing
    "junit", "pytest", "jest", "selenium", "cypress", "mockito", "postman",

    # data & ai
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras", "opencv", "hugging face", "langchain",

    # data engineering
    "apache kafka", "apache spark", "airflow", "hadoop", "dbt", "snowflake", "bigquery",

    # apis & protocols
    "restful apis", "graphql", "websockets", "oauth2", "jwt",

    # mobile development
    "flutter", "react native", "android (kotlin/java)", "ios (swift)",

    # architecture & patterns
    "microservices", "monolithic architecture", "event-driven architecture", "mvc", "clean architecture", "design patterns",

    # soft skills & practices
    "agile", "scrum", "devops", "tdd", "clean code", "system design", "problem solving", "code review",

    # security
    "owasp", "tls/ssl", "oauth 2.0", "input validation", "role-based access control (rbac)",

    # tools & ides
    "vscode", "intellij idea", "pycharm", "figma", "notion", "slack",

    # file formats
    "json", "yaml", "xml", "csv", "parquet",

    # operating systems
    #"linux", "ubuntu", "macos", "windows",

    # misc
    "shell scripting", "api integration", "continuous deployment", "monitoring & logging", "nginx", "prometheus", "grafana"
]

def delete_skills_from_mongo_chroma(ids):
    remove_skills_chroma(ids)
    remove_skills_mongo(ids)
    

def init_primary_skills_in_dict():
    add_unique_skills_to_chroma(primary_skills)
    init_techs_if_not_exist_mongo(primary_skills)

def add_skill_if_new(new_skills_dict,existing_skills_set):
    """ 
    if the skill doesn't exist in existing skills , search for similar option if it exists replace it with existing one 
    if not add it to existing ones

    """
    ## Skills returned from mongodb
    # existing_skills = get_skills_mongo()
    ## convert them to sets for O(1) search
    # existing_skills_set = set(existing_skills)

    ##list of technologies
    new_skills = new_skills_dict["skills"]
    skills_to_add = []
    for index,new_skill in enumerate(new_skills):
        lower_skill_val = new_skill["technology"].lower()
        if lower_skill_val in existing_skills_set:
            logger.info(f"skill : {new_skill} already exists in the mongodb dictionary ")
            new_skills[index]["technology"] = lower_skill_val
            continue

        similar = find_similar_skill(lower_skill_val)

        if similar:
            new_skills[index]["technology"] = similar
            logger.info(f"{lower_skill_val} found similar : {similar}")
        else:
            skills_to_add.append(lower_skill_val)

    if skills_to_add:
        logger.info(f"adding new {skills_to_add} technologies(skills)")
        add_new_skills_mongo(skills_to_add)
        add_unique_skills_to_chroma(skills_to_add)

def main():
    # Step 1: Initialize the system with primary skills if needed
    init_primary_skills_in_dict()

    # Step 2: Get existing skills from MongoDB (to avoid duplicates)
    existing_skills = get_skills_mongo()
    existing_skills_set = set(skill.lower() for skill in existing_skills)

    # Step 3: Simulate a new candidate with new skills
    candidate_skills_dict = {
        "skills": [
            {"technology": "PyThon"},
            {"technology": "LangChain"},
            {"technology": "SpringBoot"},
            {"technology": "Data Visualisation"},  # likely a new or misspelled one
            {"technology": "React.js"},            # existing
            {"technology": "GCP"}                  # should match Google Cloud Platform
        ]
    }

    # Step 4: Run the matcher function
    add_skill_if_new(candidate_skills_dict, existing_skills_set)

    # Step 5: Show the updated candidate skill list
    print("\n🔍 Final candidate skills (after similarity resolution):")
    print(candidate_skills_dict["skills"])

if __name__ == "__main__":
    #delete_skills_from_mongo_chroma(["LangChain","Data Visualisation","GCP"])
    main()
# python -m services.dictionaire_service
