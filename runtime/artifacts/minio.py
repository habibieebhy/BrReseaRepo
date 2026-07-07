from pathlib import Path
from io import BytesIO
from minio.error import S3Error
from minio import Minio
from runtime.artifacts.backend import ArtifactBackend


class MinIOBackend(ArtifactBackend):

    def __init__(self):

        self.client = Minio(
            "localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False,
        )

        self.bucket = "brixta"

        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def save_raw(
        self,
        job_id: str,
        data: str,
        ) -> None:
        object_name = f"raw/{job_id}.html"
        payload = data.encode("utf-8")
        self.client.put_object(
        self.bucket,
        object_name,
        BytesIO(payload),
        length=len(payload),
        content_type="text/html",
    )
    def load_raw(
        self,
        job_id: str,
        ) -> str:

        object_name = f"raw/{job_id}.html"

        response = self.client.get_object(
        self.bucket,
        object_name,
        )

        try:
            return response.read().decode("utf-8")
        finally:
            response.close()
            response.release_conn()    

    def raw_exists(
        self,
        job_id: str,
        ) -> bool:

        object_name = f"raw/{job_id}.html"

        try:
            self.client.stat_object(
            self.bucket,
            object_name,
        )
            return True

        except S3Error:
            return False
    def load_docling(self, job_id: str) -> str:
            object_name = f"docling/{job_id}.json"
        
            response = self.client.get_object(self.bucket, object_name)
        
            try:
                return response.read().decode("utf-8")
            finally:
                response.close()
                response.release_conn()

    def docling_exists(self, job_id: str) -> bool:
        object_name = f"docling/{job_id}.json"
        
        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except S3Error:
            return False

    def save_markdown(
        self,
        job_id: str,
        data: str,
    ) -> None:

        object_name = f"markdown/{job_id}.md"

        payload = data.encode("utf-8")

        self.client.put_object(
            self.bucket,
            object_name,
            BytesIO(payload),
            length=len(payload),
            content_type="text/markdown",
        )


    def load_markdown(
        self,
        job_id: str,
    ) -> str:

        object_name = f"markdown/{job_id}.md"

        response = self.client.get_object(
            self.bucket,
            object_name,
        )

        try:
            return response.read().decode("utf-8")
        finally:
            response.close()
            response.release_conn()


    def markdown_exists(
        self,
        job_id: str,
    ) -> bool:

        object_name = f"markdown/{job_id}.md"

        try:
            self.client.stat_object(
                self.bucket,
                object_name,
            )
            return True

        except S3Error: 
            return False
    def save_chunks(
        self,
        job_id: str,
        data: str,
    ) -> None:

        object_name = f"chunks/{job_id}.json"

        payload = data.encode("utf-8")

        self.client.put_object(
            self.bucket,
            object_name,
            BytesIO(payload),
            length=len(payload),
            content_type="application/json",
        )


    def load_chunks(
        self,
        job_id: str,
    ) -> str:

        object_name = f"chunks/{job_id}.json"

        response = self.client.get_object(
            self.bucket,
            object_name,
        )

        try:
            return response.read().decode("utf-8")
        finally:
            response.close()
            response.release_conn()


    def chunks_exists(
        self,
        job_id: str,
    ) -> bool:

        object_name = f"chunks/{job_id}.json"

        try:
            self.client.stat_object(
                self.bucket,
                object_name,
            )
            return True

        except S3Error:
            return False

    def save_embeddings(
        self,
        job_id: str,
        data: str,
    ) -> None:

        object_name = f"embeddings/{job_id}.json"

        payload = data.encode("utf-8")

        self.client.put_object(
            self.bucket,
            object_name,
            BytesIO(payload),
            length=len(payload),
            content_type="application/json",
        )
    def save_docling(
        self,
        job_id: str,
        data: str,
    ) -> None:

        object_name = f"docling/{job_id}.json"

        payload = data.encode("utf-8")

        self.client.put_object(
            self.bucket,
            object_name,
            BytesIO(payload),
            length=len(payload),
            content_type="application/json",
        )

    def load_embeddings(
        self,
        job_id: str,
    ) -> str:

        object_name = f"embeddings/{job_id}.json"

        response = self.client.get_object(
            self.bucket,
            object_name,
        )

        try:
            return response.read().decode("utf-8")
        finally:
            response.close()
            response.release_conn()


    def embeddings_exists(
        self,
        job_id: str,
    ) -> bool:

        object_name = f"embeddings/{job_id}.json"

        try:
            self.client.stat_object(
                self.bucket,
                object_name,
            )
            return True

        except S3Error:
            return False
    def provider(self) -> str:
        return "minio"


    def health(self) -> bool:
        try:
            return self.client.bucket_exists(self.bucket)
        except Exception:
            return False


    def info(self) -> dict:
        return {
            "endpoint": "localhost:9000",
            "bucket": self.bucket,
        }