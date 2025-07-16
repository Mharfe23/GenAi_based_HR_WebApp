from minio import Minio
from dotenv import load_dotenv
import os
import logging

load_dotenv()
MINIO_ROOT_USER = os.getenv('MINIO_ROOT_USER')
MINIO_ROOT_PASSWORD = os.getenv('MINIO_ROOT_PASSWORD')
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')


logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

bucket_name = "CV"

def init_minio_client():

    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ROOT_USER,
        secret_key=MINIO_ROOT_PASSWORD,
        secure=False
    )
    found = client.bucket_exists(bucket_name)
    if not found:
        client.make_bucket(bucket_name)
        print("Created bucket", bucket_name)
    else:
        print("Bucket", bucket_name, "already exists")

    return client

if __name__ == "__main__":
    load_dotenv()
    try:
        minio_client = init_minio_client()
    except Exception as e:
        logging.error(f"Failed to initialize MinIO client: {e}")