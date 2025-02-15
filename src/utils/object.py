from pydantic import BaseModel, condecimal
from typing import Optional, List


class PrimaryDiagnosticsResponse(BaseModel):
    confidence_score: condecimal(ge=-1, le=1)
    concluding_prompt: Optional[str] = None
    clarification_guidance: Optional[str] = None


class AIresponce_SkipStatus(BaseModel):
    AIresponce: Optional[str] = None
    SkipStatus: bool

class UserResponce(BaseModel):
    user_response: Optional[str] = None

if __name__ == "__main__":
    responce = PrimaryDiagnosticsResponse(
        confidence_score = 0.6, 
        concluding_prompt = "Thinking about it overall, would you describe yourself as generally at ease or more prone to restlessness?",
        clarification_guidance = "I understand that it might vary depending on the situation. Would you say you feel this way more often than not, or is it only in specific stressful moments?"
    )

    print(responce.concluding_prompt)