import os 

class Config: 
    SECRET_KEY = os.getenv("SECRET_KEY") 
    SQLALCHEMY_DATABASE_URI = "sqlite:///msa.sqlite3" 
    SQLALCHEMY_TRACK_MODIFICATIONS = False 
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")





