# MongoDB connection
from pymongo import MongoClient

client = MongoClient("mongodb+srv://Agather:avocado2001@cl-iptl.i2vsn1h.mongodb.net/?retryWrites=true&w=majority&appName=cl-iptl")
db = client.db_voluntech
volunteer_collection = db.volunteer
organization_collection = db.organization
sessions_collection = db.sessions
