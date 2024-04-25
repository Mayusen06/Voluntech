from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
from typing import Dict
from models import volunteer, organization
from fastapi.security import HTTPBasic
from fastapi.staticfiles import StaticFiles
from pymongo.collection import Collection
from datetime import datetime
from database import sessions_collection
from models import User, volunteer, organization
from database import volunteer_collection, organization_collection, sessions_collection
import bcrypt
import re
import secrets

security = HTTPBasic()
verification_tokens = {}  # Dictionary to store verification tokens
app = FastAPI()
# Mount static files directory
app.mount("/templates", StaticFiles(directory="templates"), name="static")
# Define Jinja templates directory
templates = Jinja2Templates(directory="templates")
# In-memory session storage (for demonstration purposes)
sessions: Dict[str, dict] = {}



 #Verify the password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify the provided plain password against the hashed password.
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# Check if the password meets complexity requirements
def is_password_complex(password: str) -> bool:
    """
    Check if the password meets complexity requirements.
    """
    min_length = 8
    has_lowercase = re.search(r'[a-z]', password)
    has_uppercase = re.search(r'[A-Z]', password)
    has_digit = re.search(r'\d', password)
    has_special = re.search(r'[!@#$%^&*()-_+=]', password)

    return (
        len(password) >= min_length and
        has_lowercase and
        has_uppercase and
        has_digit and
        has_special
    )

# Hash the password
def hash_password(password: str) -> str:
   def hash_password(password: str) -> str:
    """
    Hash the provided password using bcrypt.
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password.decode('utf-8')

# Create session token
def create_session_token(username: str) -> str:
    """
    Generate a session token for the authenticated user.
    """
    token = secrets.token_urlsafe(32)
    return token

# Store session token
def store_session_token(session_token: str, username: str, expiration_time: datetime):
    """
    Store the session token and its expiration time in the session store (MongoDB).
    """
    session_data = {
        "session_token": session_token,
        "username": username,
        "expiration_time": expiration_time
    }
    # Assuming you have a sessions_collection defined elsewhere
    sessions_collection.insert_one(session_data)

# Common function for user registration
async def register_user(request: Request, collection: Collection, template: str, form_data: dict, redirect_url: str):
        # Check if the email already exists in the database collection
        user = collection.find_one({"email": form_data['email']})
        if user:
            # Email already exists
            return templates.TemplateResponse(
                template,
                {"request": request, "error_message": "Email already exists. Login instead?."}
            )

        # Check if password meets complexity requirements
        if not is_password_complex(form_data['password']):
            # Password is not complex enough
            return templates.TemplateResponse(
                template,
                {"request": request, "error_message": "Password does not meet complexity requirements"}
            )

        # If email is unique and password is complex, proceed with registration
        # Hash the password
        hashed_password = hash_password(form_data['password'])
        # Store the hashed password in your database along with other user details
        # You can store this data in the provided collection
        user_data = {**form_data, "hashed_password": hashed_password}
        collection.insert_one(user_data)
        # Generate a session token
        session_token = create_session_token(form_data['email'])
        # Set the expiration time for the session token (e.g., 1 hour from now)
        expiration_time = datetime.now() + timedelta(hours=1)
        # Store the session token and its expiration time in the session store
        store_session_token(session_token, form_data['email'], expiration_time)
        # Redirect to the specified URL after registration
        return RedirectResponse(redirect_url, status_code=303, headers={"Refresh": "5; url=" + redirect_url})
  
# Root landing page
@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("landing_page.html", {"request": request})

# Route for rendering signup selection page
@app.get("/register", response_class=HTMLResponse)
async def get_signup_selection(request: Request):
    return templates.TemplateResponse("register_selection.html", {"request": request})

# Route for handling login form submission
@app.post("/login/")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    # Check if email exists in either volunteer or organization collections
    user = volunteer_collection.find_one({"email": email}) or organization_collection.find_one({"email": email})
    if not user:
        # Email not found in any collection
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    # Check if the password matches
    hashed_password = user.get("hashed_password")  # Retrieve hashed password from user
    if not hashed_password or not verify_password(password, hashed_password):
        # Invalid email or password
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    # Redirect to volunteer or organization page based on user type
    if volunteer_collection.find_one({"email": email}):
        return RedirectResponse(url="/volunteer", status_code=303)
    elif organization_collection.find_one({"email": email}):
        return RedirectResponse(url="/organization", status_code=303)

    
# Route for rendering signup selection page
@app.get("/register", response_class=HTMLResponse)
async def get_signup_selection(request: Request):
    return templates.TemplateResponse("register_selection.html", {"request": request})

# Route for handling volunteer registration
@app.post("/register/volunteer")
async def register_volunteer(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    age: str = Form(...),
    gender: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    city: str = Form(...),
    skills: str = Form(...),
    cause: str = Form(...),
):
    # Extract form data
    form_data = {
        "first_name": first_name,
        "last_name": last_name,
        "age": age,
        "gender": gender,
        "email": email,
        "password": password,
        "city": city,
        "skills": skills,
        "cause": cause
    }
    hashed_password = hash_password(form_data['password'])
    print(hashed_password)
    return await register_user(request, volunteer_collection, "volunteer/register_volunteer.html", form_data, "/volunteer")

# Route for handling organization registration
@app.post("/register/organization")
async def register_organization(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    city: str = Form(...),
):
    # Extract form database
    form_data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": password,  
        "city": city,
    }

    # Debugging: Log form data before processing
    print("Form data before processing:", form_data)

    # Call the register_user function
    return await register_user(request, organization_collection, "organization/register_organization.html", form_data, "/organization")

# Route for displaying the volunteer page
@app.get("/volunteer", response_class=HTMLResponse)
async def get_volunteer_page(request: Request):
    return templates.TemplateResponse("/volunteer/volunteer.html", {"request": request})

# Route for displaying the volunteer registration form
@app.get("/register/volunteer", response_class=HTMLResponse)
async def get_register_volunteer_form(request: Request):
    return templates.TemplateResponse("volunteer/register_volunteer.html", {"request": request})

# Route for displaying the organization registration page
@app.get("/organization", response_class=HTMLResponse)
async def get_organization_page(request: Request):
    return templates.TemplateResponse("/organization/organization.html", {"request": request})

# Route for displaying the orgnization registration form
@app.get("/register/organization", response_class=HTMLResponse)
async def get_register_organization_form(request: Request):
    return templates.TemplateResponse("organization/register_organization.html", {"request": request})
