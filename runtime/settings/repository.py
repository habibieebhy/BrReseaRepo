import json
from pathlib import Path
from threading import Lock


class RuntimeSettingsRepository:
    _path = Path("storage/control-plane/settings.json")
    _env_path = Path("storage/control-plane/runtime.env")
    _lock = Lock()

    @classmethod
    def get(cls) -> dict:
        if not cls._path.exists():
            return {}
        return json.loads(cls._path.read_text(encoding="utf-8"))

    @classmethod
    def save(cls, data: dict) -> dict:
        cls._path.parent.mkdir(parents=True, exist_ok=True)
        temporary = cls._path.with_suffix(".tmp")
        with cls._lock:
            temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
            temporary.replace(cls._path)
            env = {
                "ARTIFACT_BACKEND": data["artifact_backend"],
                "MINIO_ENDPOINT": data["minio_endpoint"],
                "MINIO_CONSOLE_URL": data["minio_console_url"],
                "MINIO_BUCKET": data["minio_bucket"],
                "EMBEDDING_PLUGIN": data["default_plugins"]["embedding"],
                "EMBEDDING_MODEL": data["embedding_model"],
            }
            cls._env_path.write_text("\n".join(f"{key}={value}" for key, value in env.items()) + "\n", encoding="utf-8")
        return data
