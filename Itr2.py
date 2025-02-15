from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.utils.loader import *
from src.utils.env import *
import requests
import asyncio
import json
from typing import List
from pydantic import BaseModel


# <--------------------------------------------
from pydantic import BaseModel, condecimal
from typing import Optional, List
from openai import OpenAI
from types import SimpleNamespace


class ChatAnalysisLLMResponce(BaseModel):
    clarity_score: condecimal(ge=0, le=1)
    positive_score: condecimal(ge=0, le=1)
    concluding_prompt: Optional[str] = None
    clarification_guidance: Optional[str] = None
    reasoning: Optional[List[str]] = None  


class DisorderRequest(BaseModel):
    disorder: str


def llmChatResponse(ResponceFormat, system_role, max_retries=3, **IOarg) -> ChatAnalysisLLMResponce:
    setup_environment()
    client = OpenAI()
    attempts = 0
    print("Initiating LLM response")
    while attempts < max_retries:
        try:
            # Generate the interaction prompt
            interaction = PromptManager.get_prompt("io", **IOarg)

            # Make API call
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_role},
                    {"role": "user", "content": interaction},
                ], temperature=0.2
            )

            # Extract and parse response
            response_text = response.choices[0].message.content

            parsed_content = json.loads(response_text)

            # Validate response format
            structured_response = ResponceFormat(**parsed_content)
            return structured_response

        except json.JSONDecodeError:
            print(f"Attempt {attempts + 1}: Response is not in JSON format. Retrying...")
        except Exception as e:
            print(f"Unexpected Error: {e}")

        attempts += 1

    raise ValueError("Max retries exceeded. Could not parse response as JSON.")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_connections: List[WebSocket] = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            print("Received data:", data)
            user_message = json.loads(data).get("user_response")

            if user_message:
                # Create disorder request and process it
                disorder = user_message
                disorder_request = DisorderRequest(disorder=disorder)

                # Process the diagnostic operation
                
                diagnosis_result = await primary_diagnostic_operator(disorder_request, websocket)
                print("Diagnosis result:", diagnosis_result)
                
                # if diagnosis_result and disorder == "Depression" or disorder == "Anxiety":
                #     await send_to_frontend({
                #         "question": "Initiating Secondary Diagnostics for further confirmation",
                #         "skip_allowed": True
                #     }, websocket)
                #     await secondary_diagnostic_operator(disorder, websocket)
                # elif diagnosis_result and disorder != "Depression" or disorder != "Anxiety":
                #     await send_to_frontend({
                #         "question": """As of now I can Diagnose only following Secondary Disorders:\n 
                #         1. Depression\n
                #         2. Anxiety\n
                #         """,
                #         "skip_allowed": True
                #     }, websocket)

    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print("Client disconnected")
    except Exception as e:
        print(f"Error in websocket connection: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

async def send_to_frontend(data: dict, websocket: WebSocket):
    message = data.get("question")
    skip_allowed = data.get("skip_allowed")
    
    try:
        await websocket.send_text(
            json.dumps({
                "AIresponce": {
                    "question": message,
                    "skip_allowed": skip_allowed
                }
            })
        )
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)

async def get_user_response_from_frontend(websocket: WebSocket):
    try:
        data = await websocket.receive_text()
        user_response = json.loads(data).get("user_response")
        return user_response if user_response else None

    except WebSocketDisconnect:
        print("WebSocket connection disconnected")
        return None

@app.post("/ws")
async def primary_diagnostic_operator(request: DisorderRequest, websocket: WebSocket):
    try:
        disorder = request.disorder

        system_role = PromptManager.get_prompt("diagnostics_itr2", section="ALL", low=0.2, high=0.8)
        questionnaire = load_json("prompts_files/Diagnostics/Pre-diagnosis_ques.json")

        diagnose = False

        for ques in questionnaire[disorder]["questions"]:
            chat = []
            system_ques = ques["text"]
            chat.append(f"Question: {system_ques}")

            # Send question to frontend
            await send_to_frontend({ "question": system_ques,"skip_allowed": False}, websocket)
            user_response = await get_user_response_from_frontend(websocket)
            chat.append(f"User Response: {user_response}")

            chat_count = 0
            while True:
                kwarg_dict = {"ques": system_ques,"chat": chat,}
                print("kwarg_dict", kwarg_dict)
                msg = llmChatResponse(ChatAnalysisLLMResponce, system_role, **kwarg_dict)
                print("reasoning", msg.reasoning)
                print("concluding_prompt", msg.concluding_prompt)
                print("clarification_guidance", msg.clarification_guidance)

                skip_allowed = False
                system_ques = msg.concluding_prompt

                if msg.clarity_score >= 0.4:
                    if (msg.positive_score >= 0.8):
                        chat_count += 1
                        skip_allowed = True
                        print("Chat count increasses to:", chat_count)
                    elif (msg.positive_score <= 0.2):
                        skip_allowed = True
                    print("Skip allowed is", skip_allowed)

                else:
                    system_ques = system_ques +" || "+ msg.clarification_guidance

                user_response = None
                if abs(chat_count) < 3:
                    print(f"Chat count: {chat_count} is less than 3")
                    await send_to_frontend({ "question": f"{system_ques} [clarity : {msg.clarity_score}, affirmative: {msg.positive_score}]","skip_allowed": skip_allowed}, websocket)
                    user_response = await get_user_response_from_frontend(websocket)
                
                chat.append(f"Psychiatrist: {system_ques}")
                chat.append(f"User: {user_response}")

                if user_response == None:
                    print("User response is None")
                    if msg.positive_score >= 0.7:
                        diagnose = True

                    await send_to_frontend({ "question": f"I m concluding your response for the {disorder} disorder to be {diagnose}","skip_allowed": True}, websocket)
                    break

        if diagnose:
            await send_to_frontend({
                "question": f"Primary Diagnosis for {disorder} disorder  is positive \n, Please initiate Secondary diagnostics for further confirmation",
                "skip_allowed": True
            }, websocket)

        else:
            await send_to_frontend({
                "question": f"Diagnosis for {disorder} disorder is negative",
                "skip_allowed": True
            }, websocket)

        return {"message": f"Received disorder: {disorder}"}

    except Exception as e:

        await send_to_frontend({
            "question": """As of now I can Diagnose only following Primary Disorders:\n 
            1. Depression\n 2. Anxiety\n 3. Bipolar\n 4. Trauma\n 5. Obsessions\n 6. Eating\n 7. Personality\n 8. Dissociation\n 9. Somatic\n 10. Sleep\n 11. Addiction\n 12. Elimination\n""",
            "skip_allowed": True
        }, websocket)
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)