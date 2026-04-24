import os
from typing import BinaryIO

import boto3
from botocore.config import Config

_client = None


def get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=os.environ["R2_ENDPOINT_URL"],
            aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )
    return _client


BUCKET = os.environ.get("R2_BUCKET_NAME", "disclosure-pdfs")


def upload_pdf(file_obj: BinaryIO, key: str, content_type: str = "application/pdf") -> str:
    """Upload a PDF to R2. Returns the object key."""
    get_client().upload_fileobj(
        file_obj,
        BUCKET,
        key,
        ExtraArgs={"ContentType": content_type},
    )
    return key


def get_presigned_url(key: str, expires_in: int = 3600) -> str:
    """Generate a presigned URL for temporary read access to a stored PDF."""
    return get_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET, "Key": key},
        ExpiresIn=expires_in,
    )
