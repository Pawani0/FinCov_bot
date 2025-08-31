from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.twilio_verify import send_verification_code, check_verification_code
from utils.sessions import active_session

router = APIRouter()

class PhoneRequest(BaseModel):
    phone: str
    session_id: str

class VerifyRequest(BaseModel):
    phone: str
    code: str

@router.post("/auth/send-otp", tags=["Mobile Verification"])
async def send_otp(data: PhoneRequest):
    if "+91" not in data.phone:
        phone = "+91" + data.phone
    else:
        phone = data.phone
    status = send_verification_code(phone)
    if status != "pending":
        raise HTTPException(status_code=400, detail="Failed to send OTP")
    
    active_session[data.session_id]["phone_number"] = phone
    return {"message": "OTP sent successfully"}

@router.post("/auth/verify-otp", tags=["Mobile Verification"])
async def verify_otp(data: VerifyRequest):
    if "+91" not in data.phone:
        phone = "+91" + data.phone
    else:
        phone = data.phone
    if check_verification_code(phone, data.code):
        return {"verified": True, "message": "Phone verified"}
    raise HTTPException(status_code=400, detail="Invalid OTP")