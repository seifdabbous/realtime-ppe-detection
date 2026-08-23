from pydantic import BaseModel,EmailStr,Field

class UserRegister(BaseModel):
    username:str = Field(min_length=1,max_length=50)
    email:EmailStr
    password:str = Field(min_length=8,max_length=72)
    
    
    
class UserLogin(BaseModel):
    email:EmailStr
    password: str = Field(min_length=8,max_length=72)