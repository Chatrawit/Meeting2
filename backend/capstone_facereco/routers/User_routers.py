import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi import UploadFile,File
from fastapi.responses import FileResponse
from pymongo import MongoClient
from gridfs import GridFS
import os
import random
import math
import cv2
import pickle
import face_recognition
from dotenv import load_dotenv
load_dotenv()

# Initialize MongoDB client
client = MongoClient(os.getenv('MONGODB_URL'))
db = client[os.getenv('DATABASE_NAME')]
collection_name = db[os.getenv('COLLECTION_PROFILE')]
fs = GridFS(db)

router = APIRouter(
    prefix="/user",
    tags=['User'],
    responses={404:{
        'message': "User not found"
    }}
)

class User(BaseModel):
    id : str
    name : str
    nickname : str
    email: str
    phone_number:str
    lineID :str

class UserCreate(BaseModel):
    u_id: str
    name : str
    nickname : str
    email: str
    phone_number:str
    lineID :str

@router.post("/")
async def create_user(user: UserCreate):
    # Check if user with this u_id already exists
    if collection_name.find_one({"id": user.u_id}):
        raise HTTPException(status_code=400, detail="User with this ID already exists")
    
    user_with_picture = User(id=user.u_id, name=user.name, nickname=user.nickname, phone_number=user.phone_number, lineID=user.lineID, email=user.email)
    result = collection_name.insert_one(user_with_picture.model_dump())
    if result.acknowledged:
        return {"message": "User created successfully", "user_id": user.u_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to create user with picture") 