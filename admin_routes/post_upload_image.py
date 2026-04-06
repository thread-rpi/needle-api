import os
import json
from io import BytesIO
from datetime import datetime, timezone

import boto3
from bson import ObjectId
from dateutil.parser import isoparse
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity

from PIL import Image, ImageFilter

# Register AVIF support for Pillow (provided by pillow-avif-plugin)
import pillow_avif  # noqa: F401


def _error(message: str, status_code: int):
    return jsonify({"error": message}), status_code


def _parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in {"true", "1", "yes", "y", "on"}:
        return True
    if s in {"false", "0", "no", "n", "off"}:
        return False
    return default


def _parse_object_id(value):
    if value is None or value == "":
        return None
    return ObjectId(str(value))


def _parse_object_id_list(value):
    if value is None or value == "":
        return []
    # value may be JSON array string or comma-separated
    if isinstance(value, (list, tuple)):
        raw = list(value)
    else:
        s = str(value).strip()
        if s.startswith("["):
            raw = json.loads(s)
        else:
            raw = [p.strip() for p in s.split(",") if p.strip()]
    return [ObjectId(str(v)) for v in raw]


def _normalize_prefix(prefix: str) -> str:
    p = (prefix or "").strip()
    if p == "":
        return ""
    return p if p.endswith("/") else (p + "/")


def _generate_avif_variants(jpeg_bytes: bytes):
    """
    Returns:
      (variants, width, height)
      variants: dict[name] = bytes
    """
    img = Image.open(BytesIO(jpeg_bytes))
    img = img.convert("RGB")
    width, height = img.size

    is_cover = width >= height

    if is_cover:
        widths = {"blur": 32, "sm": 400, "md": 800, "lg": 1800}
    else:
        widths = {"blur": 32, "sm": 300, "md": 700, "lg": 1400}

    qualities = {"blur": 24, "sm": 42, "md": 55, "lg": 67}

    variants = {}
    for name in ("blur", "sm", "md", "lg"):
        target_w = widths[name]
        if width <= target_w:
            resized = img
        else:
            target_h = round((target_w / width) * height)
            resized = img.resize((target_w, target_h), resample=Image.Resampling.LANCZOS)

        if name != "blur":
            resized = resized.filter(ImageFilter.UnsharpMask(radius=1.2, percent=115, threshold=3))

        out = BytesIO()
        resized.save(out, format="AVIF", quality=qualities[name])
        variants[name] = out.getvalue()

    return variants, width, height


def upload_image_endpoint(*, events, images, members, admins):
    """
    Admin-protected endpoint: POST /admin/upload-image
    Expects multipart/form-data with:
      - image: file (jpg/jpeg)
      - event_id: ObjectId string (required)
      - date: datetime string (required)
      - optional fields per Issue #47
    """
    # AuthN
    current_user_email = get_jwt_identity()
    if not current_user_email:
        return _error("Unauthenticated or unauthorized request", 403)

    user = members.find_one({"email": current_user_email})
    if not user or "_id" not in user:
        return _error("Unauthenticated or unauthorized request", 403)

    user_id = user["_id"]

    # AuthZ: ensure user is an admin
    if not admins.find_one({"_id": user_id}):
        return _error("Unauthenticated or unauthorized request", 403)

    # Multipart parsing
    file = request.files.get("image")
    if not file:
        return _error("Required fields are missing, malformed, or inaccurate fields are present", 400)

    filename = (file.filename or "").lower()
    if not (filename.endswith(".jpg") or filename.endswith(".jpeg")):
        return _error("Required fields are missing, malformed, or inaccurate fields are present", 400)

    try:
        jpeg_bytes = file.read()
        if not jpeg_bytes:
            return _error("Required fields are missing, malformed, or inaccurate fields are present", 400)
    except Exception:
        return _error("Required fields are missing, malformed, or inaccurate fields are present", 400)

    # Required fields
    event_id_raw = request.form.get("event_id")
    date_raw = request.form.get("date")
    if not event_id_raw or not date_raw:
        return _error("Required fields are missing, malformed, or inaccurate fields are present", 400)

    try:
        event_obj_id = ObjectId(str(event_id_raw))
    except Exception:
        return _error("Required fields are missing, malformed, or inaccurate fields are present", 400)

    try:
        taken_at = isoparse(str(date_raw))
        if taken_at.tzinfo is None:
            taken_at = taken_at.replace(tzinfo=timezone.utc)
    except Exception:
        return _error("Required fields are missing, malformed, or inaccurate fields are present", 400)

    # Optional fields with defaults
    caption = request.form.get("caption", "")
    if caption is None:
        caption = ""
    caption = str(caption)

    published = _parse_bool(request.form.get("published"), default=False)

    try:
        photographer_id = _parse_object_id(request.form.get("photographer_id"))
        creative_director_id = _parse_object_id(request.form.get("creative_director_id"))
        model_ids = _parse_object_id_list(request.form.get("model_ids"))
    except Exception:
        return _error("Required fields are missing, malformed, or inaccurate fields are present", 400)

    additional_personnel = []
    additional_personnel_raw = request.form.get("additional_personnel")
    if additional_personnel_raw is not None:
        try:
            parsed = json.loads(str(additional_personnel_raw))
            if not isinstance(parsed, list):
                raise ValueError("additional_personnel must be a list")
            for item in parsed:
                if not isinstance(item, dict):
                    raise ValueError("additional_personnel entries must be objects")
                member_id = _parse_object_id(item.get("member_id"))
                role = item.get("role", "")
                if member_id is None:
                    raise ValueError("additional_personnel.member_id missing")
                additional_personnel.append({"member_id": member_id, "role": str(role)})
        except Exception:
            return _error("Required fields are missing, malformed, or inaccurate fields are present", 400)

    # Event validation + retrieve image_path + image_ids
    event = events.find_one({"_id": event_obj_id})
    if not event:
        return _error("Required fields are missing, malformed, or inaccurate fields are present", 400)

    event_image_path = event.get("image_path") or event.get("cover_image_path")
    if not event_image_path:
        return _error("Required fields are missing, malformed, or inaccurate fields are present", 400)

    event_image_ids = event.get("image_ids") or []
    if not isinstance(event_image_ids, list):
        return _error("Required fields are missing, malformed, or inaccurate fields are present", 400)

    image_index = len(event_image_ids)
    base_prefix = _normalize_prefix(str(event_image_path))
    image_prefix = f"{base_prefix}{image_index}/"

    # Generate AVIF variants
    try:
        variants, width, height = _generate_avif_variants(jpeg_bytes)
    except Exception:
        return _error("Something went wrong with the image generation or upload", 500)

    # Upload to S3
    bucket = os.getenv("S3_BUCKET")
    if not bucket:
        return _error("Something went wrong internally", 500)

    s3 = boto3.client("s3")
    try:
        for name, data in variants.items():
            key = f"{image_prefix}{name}.avif"
            s3.upload_fileobj(
                Fileobj=BytesIO(data),
                Bucket=bucket,
                Key=key,
                ExtraArgs={"ContentType": "image/avif"},
            )
    except Exception:
        return _error("Something went wrong with the image generation or upload", 500)

    # DB operations
    now = datetime.now(timezone.utc)
    new_image_id = ObjectId()
    image_doc = {
        "_id": new_image_id,
        "event_id": event_obj_id,
        "date": taken_at,
        "caption": caption,
        "published": published,
        "photographer_id": photographer_id or None,
        "creative_director_id": creative_director_id or None,
        "model_ids": model_ids or [],
        "additional_personnel": additional_personnel or [],
        "path": image_prefix,
        "width": int(width),
        "height": int(height),
        "created_at": now,
        "updated_at": now,
        "created_by": user_id,
        "updated_by": user_id,
    }

    try:
        images.insert_one(image_doc)
        events.update_one(
            {"_id": event_obj_id},
            {
                "$push": {"image_ids": new_image_id},
                "$set": {"updated_at": now, "updated_by": user_id},
            },
        )
    except Exception:
        return _error("Something went wrong internally", 500)

    return jsonify({"data": {"id": str(new_image_id)}}), 200

