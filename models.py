from pydantic import BaseModel
from datetime import date
class User(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    city:str
    
class volunteer(BaseModel):
    first_name: str
    last_name: str
    age:int
    gender: str
    email: str
    password: str
    city:str
    skills: list[str]
    cause: list[str]
    gender: str

class organization (BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    city:str
