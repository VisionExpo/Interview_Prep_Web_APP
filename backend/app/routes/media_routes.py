from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from typing import List
from ..models.user import User
from ..utils.auth import get_current_user
from ..db.connection import db
import boto3
import os
from uuid import uuid4
from datetime import datetime

router = APIRouter(prefix="/media", tags=["media"])

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: str = None,
    tags: List[str] = None,
    current_user: User = Depends(get_current_user)
):
    session = db.get_session()
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid4()}{file_extension}"
    
    # Upload to S3
    try:
        s3_client.upload_fileobj(
            file.file,
            BUCKET_NAME,
            f"uploads/{current_user.id}/{unique_filename}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Store file metadata in database
    session.execute("""
        INSERT INTO media_files 
        (id, user_id, filename, original_filename, category, 
         tags, upload_date, file_type, file_size)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        uuid4(),
        current_user.id,
        unique_filename,
        file.filename,
        category,
        tags,
        datetime.now(),
        file.content_type,
        file.size
    ))
    
    return {
        "message": "File uploaded successfully",
        "filename": unique_filename
    }

@router.get("/files")
async def list_files(
    category: str = None,
    tag: str = None,
    current_user: User = Depends(get_current_user)
):
    session = db.get_session()
    query = "SELECT * FROM media_files WHERE user_id = %s"
    params = [current_user.id]
    
    if category:
        query += " AND category = %s"
        params.append(category)
    if tag:
        query += " AND %s = ANY(tags)"
        params.append(tag)
        
    result = session.execute(query, params)
    return list(result)

@router.get("/files/{file_id}")
async def get_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    session = db.get_session()
    file_info = session.execute(
        "SELECT * FROM media_files WHERE id = %s AND user_id = %s",
        (file_id, current_user.id)
    ).one()
    
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Generate presigned URL for S3 object
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': f"uploads/{current_user.id}/{file_info.filename}"
            },
            ExpiresIn=3600  # URL expires in 1 hour
        )
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    session = db.get_session()
    file_info = session.execute(
        "SELECT * FROM media_files WHERE id = %s AND user_id = %s",
        (file_id, current_user.id)
    ).one()
    
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete from S3
    try:
        s3_client.delete_object(
            Bucket=BUCKET_NAME,
            Key=f"uploads/{current_user.id}/{file_info.filename}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Delete from database
    session.execute(
        "DELETE FROM media_files WHERE id = %s",
        (file_id,)
    )
    
    return {"message": "File deleted successfully"}