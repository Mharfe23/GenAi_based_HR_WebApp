from minio import Minio
from dotenv import load_dotenv
import os
import logging
from werkzeug.utils import secure_filename
import uuid
import tempfile

load_dotenv()
MINIO_ROOT_USER = os.getenv('MINIO_ROOT_USER')
MINIO_ROOT_PASSWORD = os.getenv('MINIO_ROOT_PASSWORD')
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)


class MinioClientService:
    def __init__(self, bucket_name="resumes"):
        self.bucket_name = bucket_name
        self.client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ROOT_USER,
            secret_key=MINIO_ROOT_PASSWORD,
            secure=False
        )
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
            logger.info(f"Created bucket {self.bucket_name}")
        else:
            logger.info(f"Bucket {self.bucket_name} already exists")

    def upload_file(self, uploaded_file):
        """Uploads a file and returns the object name."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        secure_file_name = secure_filename(f"{uploaded_file.name}_{uuid.uuid4()}.pdf")
        self.client.fput_object(self.bucket_name, secure_file_name, tmp_path)
        logger.info(f"Uploaded {secure_file_name} to bucket {self.bucket_name}")
        return secure_file_name

    def download_file(self, object_name):
        logger.info(f"Downloaded {object_name}")
        return self.client.get_object(self.bucket_name, object_name)

    def delete_file(self, object_name):
        self.client.remove_object(self.bucket_name, object_name)
        logger.info(f"Deleted {object_name} from bucket {self.bucket_name}")
