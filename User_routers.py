import logging
from fastapi import APIRouter
from pydantic import BaseModel
from fastapi import UploadFile,File,HTTPException
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
import string
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
    u_id : str
    name : str
    nickname : str
    email: str
    phone_number:str
    lineID :str
    

def generate_user_id(length=28):
    """Generate a random string ID in format like 'WJm7z1tKaqOIwDXP8rsaefWxkdB2'"""
    characters = string.ascii_letters + string.digits
    user_id = ''.join(random.choice(characters) for _ in range(length))
    return user_id



@router.get("/")
def read_root():
    try:
        # Your code here
        return {"message": "Success"}
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise



@router.get('/{u_id}')
async def getObjID_by_id(u_id:str):
    x = collection_name.find_one({"u_id":str(u_id)})
    return x["name"] 

@router.post("/")
async def create_user(user:User):
    new_u_id = generate_user_id()
    #check the same id
    while collection_name.find_one({"u_id": str(new_u_id)}):
        new_u_id = generate_user_id()
    user_with_picture = User(u_id=new_u_id, name=user.name, nickname=user.nickname, phone_number=user.phone_number, lineID=user.lineID, email=user.email)
    result = collection_name.insert_one(user_with_picture.model_dump())
    if result.acknowledged:
        return {"message": "User created successfully", "user_id": str(result.inserted_id)}
    else:
        raise HTTPException(status_code=500, detail="Failed to create user with picture")

@router.delete("/{u_id}")
async def delete_user (u_id:str):
    my_query = {"u_id":str(u_id)}
    collection_name.delete_one(my_query)
    result = {'msg',f"{u_id} was delete!!" }
    return result

@router.put("/{u_id}")
async def update_user(u_id:str,field_update: str, to_new_value: str):
    x = collection_name.find_one({},{"u_id":str(u_id)})
    #search old value
    if x:
    # Retrieve the old value
        old_value_document = collection_name.find_one({"_id": x["_id"]}, {field_update: 1})
        old_value = old_value_document.get(field_update) if old_value_document else None

    # Perform the update
        update_operation = {"$set": {field_update: to_new_value}}
        collection_name.update_one({"_id": x["_id"]}, update_operation)

        result = {'msg': f"Old value: {old_value}. Update successful! New value: {to_new_value}"}
    else:
        result = {'msg': "Document not found."}
    return result


@router.post("/{u_id}/upload")
async def upload_user_picture(u_id:str,file : UploadFile=File(...)):
    picture_contents = await file.read() #read file
    file_name, file_extension = os.path.splitext(file.filename)
    new_filename = f"{u_id}{file_extension}"
    with open(new_filename, "wb") as new_file:
        new_file.write(picture_contents)
    collection = db["user_picture"]
    image_document = {
        "user_id": u_id,
        "filename": new_filename,
        "file_extension": file_extension,
        "image_data": picture_contents
    }
    collection.insert_one(image_document)
    new_file.close
    encode_pickel()
    return {"msg":"Upload and Encode Complete"}

@router.get("/{u_id}/getImage")
async def download_user_picture(u_id:str):
    collection = db["user_picture"]
    image_document = collection.find_one({"user_id": u_id})
    image_name = image_document["filename"]
    image_data = image_document["image_data"]
    foldermodepath = 'lall_img\img_file'
    path = f"{foldermodepath}\{image_name}"
    return FileResponse(path)

def findEncodeing(imgLIst):
    encodeList= []
    for img in imgLIst:
        img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList


def encode_pickel():
    #import img to the list
    foldermodepath = 'lall_img\img_file'
    pathlis = os.listdir(foldermodepath)
    print(pathlis)
    imgLIst_a = [] #array of img
    studentIds = []
    collection = db["user_picture"]
    image_documents = collection.find()
    for image_document in image_documents:
        filename = image_document["filename"]
        image_data = image_document["image_data"]
        with open(os.path.join(foldermodepath, filename), "wb") as f:
            f.write(image_data)
            imgLIst_a.append(cv2.imread(os.path.join(foldermodepath,filename)))
            studentIds.append(os.path.splitext(filename)[0])#print list numberpath

    f.close
        
    print(studentIds) #img name not png
    print("Encoding Started...")
    encodeListKnow = findEncodeing(imgLIst_a)
    encodeLIstKnowWithIds = [encodeListKnow,studentIds]
    print("Encode Complete")

    file = open("EncodeFile.p",'wb')
    pickle.dump(encodeLIstKnowWithIds,file)
    file.close() 