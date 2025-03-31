# Meeting Application

## Connecting Frontend to Backend Meeting API

This document outlines how the Angular frontend connects to the FastAPI backend for meeting management.

### API Integration

The frontend communicates with the backend API through the `ApiService` in `src/app/api.service.ts`, which provides the following methods:

1. `postMeeting(meetingData)`: Creates a new meeting
2. `uploadMeetingImage(meetingId, fileList)`: Uploads images for a meeting
3. `getMeetingImages(meetingId)`: Retrieves images for a meeting
4. `getMeetingByName(name)`: Retrieves a meeting by its name

### Backend API Endpoints (FastAPI)

The frontend expects the following endpoints to be available on the backend:

1. `POST /meeting/{place_id}`: Create a new meeting
   - Parameters: Meeting object with name, user_create, description, start_datetime, end_datetime, place_id and enrolled_users
   - Returns: `{"msg": "Create Meeting Complete", "ID": "meeting_id"}`

2. `POST /meeting/{meet_id}/upload`: Upload meeting images
   - Parameters: List of files to upload
   - Returns: `{"msg": "Upload Complete", "count": number_of_files}`

3. `GET /meeting/{meet_id}/getImage`: Retrieve meeting images
   - Returns: File response with the meeting image

4. `GET /meeting/?name={name}`: Get meeting ID from name
   - Returns: `{"msg": "Found Meeting!", "ID": "meeting_id"}`

### Frontend Form Structure

The `CreateMeetingComponent` in `src/app/content/create-meeting/create-meeting.component.ts` collects:

1. Meeting name
2. Description
3. Start date and time
4. End date and time
5. Place ID
6. Meeting image (optional)

The component automatically adds the current user's ID as the meeting creator.

### Data Flow

1. User fills out the form and submits
2. Component retrieves current user ID from AuthService
3. Component formats the data (dates, etc.)
4. Component calls ApiService.postMeeting()
5. If meeting is created successfully and image is selected, component calls ApiService.uploadMeetingImage()
6. User is notified of success/failure and redirected

### Backend Requirements (Meeting API)

To ensure compatibility, your FastAPI backend should implement the following structure in the meeting.py router:

```python
class Meeting(BaseModel):
    name: str
    user_create: str
    description: str
    start_datetime: datetime
    end_datetime: datetime
    place_id: str
    enrolled_users: List[str] = []
    image: Optional[str] = None

@router.post("/{place_id}")
async def create_meeting(place_id: str, meeting: Meeting):
    # Create meeting logic

@router.post("/{meet_id}/upload")
async def upload_meeting_picture(meet_id: str, files: List[UploadFile]=File(...)):
    # Upload files logic
    
@router.get("/{meet_id}/getImage")
async def download_meeting_picture(meet_id: str):
    # Get image logic
    
@router.get("/")
async def get_meeting_id_from_name(name: str):
    # Get meeting by name logic
```

### Backend Modifications Required

If your backend meeting.py file differs from the expected structure above, you'll need to make the following changes:

1. Update the Meeting model to include start_datetime and end_datetime instead of a single datetime field
2. Ensure the create_meeting endpoint accepts a place_id parameter in the URL
3. Make sure the upload_meeting_picture endpoint handles multiple file uploads
4. Update references to "place" to "meeting_id" in the image endpoints

### Testing the Integration

After making these changes:

1. Start your FastAPI backend server
2. Start your Angular frontend with `ng serve`
3. Navigate to the Create Meeting page
4. Fill out the form and submit
5. Check the console for any API errors
6. Verify the meeting was created in your database
# Meeting2
