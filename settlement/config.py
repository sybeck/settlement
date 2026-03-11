import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Cafe24Credential:
    admin_id: str
    password: str


def get_bool_env(key: str, default: bool = False) -> bool:
    v = os.getenv(key)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def get_brand_credential(brand: str) -> Cafe24Credential:
    brand = brand.strip().lower()
    if brand == "burdenzero":
        return Cafe24Credential(
            admin_id=os.getenv("CAFE24_BURDENZERO_ID", "").strip(),
            password=os.getenv("CAFE24_BURDENZERO_PW", "").strip(),
        )
    elif brand == "brainology":
        return Cafe24Credential(
            admin_id=os.getenv("CAFE24_BRAINOLOGY_ID", "").strip(),
            password=os.getenv("CAFE24_BRAINOLOGY_PW", "").strip(),
        )
    else:
        raise ValueError(f"지원하지 않는 브랜드입니다: {brand}")


def get_download_dir() -> str:
    return os.getenv("DOWNLOAD_DIR", "./downloads")


def get_artifact_dir() -> str:
    return os.getenv("ARTIFACT_DIR", "./artifacts")


def get_headless() -> bool:
    return get_bool_env("PLAYWRIGHT_HEADLESS", True)