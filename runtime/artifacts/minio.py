from io import BytesIO
from minio.error import S3Error
from minio import Minio
from runtime.artifacts.backend import ArtifactBackend
from core.config import MINIO_ACCESS_KEY, MINIO_BUCKET, MINIO_ENDPOINT, MINIO_SECRET_KEY, MINIO_SECURE


class MinIOBackend(ArtifactBackend):

    def __init__(self):

        self.client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE,
        )
        self.bucket = MINIO_BUCKET

    def _ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def save_object(
        self,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        self._ensure_bucket()
        self.client.put_object(
            self.bucket,
            object_name,
            BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

    def load_object(self, object_name: str) -> bytes:
        response = self.client.get_object(self.bucket, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def object_exists(self, object_name: str) -> bool:
        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except S3Error:
            return False

    def list_objects(self, prefix: str = "", limit: int = 200) -> list[dict]:
        if not self.client.bucket_exists(self.bucket):
            return []
        result = []
        for item in self.client.list_objects(self.bucket, prefix=prefix, recursive=True):
            result.append(
                {
                    "name": item.object_name,
                    "size": item.size,
                    "last_modified": (
                        item.last_modified.isoformat() if item.last_modified else None
                    ),
                }
            )
            if len(result) >= limit:
                break
        return result

    def save_raw(
        self,
        job_id: str,
        data: str,
        ) -> None:
        self._ensure_bucket()
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

        self._ensure_bucket()
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

        self._ensure_bucket()
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

        self._ensure_bucket()
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

        self._ensure_bucket()
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
            "endpoint": MINIO_ENDPOINT,
            "bucket": self.bucket,
        }

    def objects(self, prefix: str = "", limit: int = 200) -> list[dict]:
        return self.list_objects(prefix=prefix, limit=limit)
