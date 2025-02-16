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
    follow_up: Optional[str] = None
    reasoning: Optional[List[str]] = None  
    chat_summary: Optional[str] = None

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

async def chat_analysis(system_ques, user_response, chat, disorder, diagnose, websocket):
    print("Inside chat_analysis function")
    system_role = PromptManager.get_prompt("diagnostics_itr4", section="ALL", low=0.2, high=0.8)
    chat_count = 0
    while True:
        kwarg_dict = {"ques": system_ques,"chat": chat,}
        msg = llmChatResponse(ChatAnalysisLLMResponce, system_role, **kwarg_dict)
        # msg = SimpleNamespace(
        #     clarity_score=float(1.0),
        #     positive_score=float(0.8),
        #     concluding_prompt="Concluding Prompt Concluding Prompt",
        #     follow_up="Follow up Follow up Follow up Follow up",
        #     reasoning=["reasoning", "reasoning", "reasoning"],
        #     chat_summary="Summary Summary Summary Summary Summary"
        # )
        
        skip_allowed = False
        system_ques = msg.concluding_prompt

        if msg.clarity_score >= 0.7:
            if (msg.positive_score >= 0.7):
                print("Positive score is greater than 0.8")
                chat_count += 1
            elif (msg.positive_score <= 0.3):
                print("Positive score is less than 0.2")
                chat_count -= 1
            else:
                system_ques = system_ques +  msg.follow_up
        else:
            system_ques =  msg.follow_up
        print("[Reasoning]",msg.reasoning)
        print(f"Concluding Prompt: {msg.concluding_prompt}")
        print(f"Follow Up: {msg.follow_up}")

        if((msg.positive_score >= 0.8 or msg.positive_score <= 0.2)and msg.clarity_score >= 0.7):
            skip_allowed = True

        user_response = None
        if abs(chat_count) > 0:
            print("Chat count is exceeding 0")
            if chat_count > 0:
                if not diagnose: 
                    diagnose = True
                print("Diagnose is True")
            break
        
        # Reattempt the same question for more clear response 
        else:
            await send_to_frontend({ "question": f"{system_ques} [clarity : {msg.clarity_score}, affirmative: {msg.positive_score}]","skip_allowed": skip_allowed, "log" : [reasoning, ]}, websocket)
            user_response = await get_user_response_from_frontend(websocket)

        chat["Chat History"] = msg.chat_summary
        chat["Conversation"]["Psychiatrist"] = system_ques
        chat["Conversation"]["User"] = user_response

        # If user from there end skips the question then break the loop with a rough diagnosis 
        if user_response == None:
            print("User response is None")
            if msg.positive_score >= 0.7:
                if not diagnose: 
                    diagnose = True

            await send_to_frontend({ "question": f"I m concluding your response for the {disorder} disorder to be {diagnose}","skip_allowed": True}, websocket)
            break
    return diagnose

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
async def secondary_diagnostic_operator(Majordisorder: str, websocket: WebSocket):
    try:
        questionnaire = load_json("prompts_files/Diagnostics/Secondary-diagnosis_ques.json")
        if Majordisorder not in questionnaire:
            await send_to_frontend({"question": f"I am sorry, as of now I can't diagnose {Majordisorder} disorder for secondary diagnostics","skip_allowed": True}, websocket)
            return {"error": f"I am sorry, as of now I can't diagnose {Majordisorder} disorder"}

        for disorder_name, disorder_details in questionnaire[Majordisorder].items():
            await send_to_frontend({"question": f"\nStarting questionnaire for: {disorder_name}","skip_allowed": False}, websocket)
            
            core_symptoms_threshold = disorder_details["CoreSymptomsCount"]
            print("Core symptoms count:", core_symptoms_threshold)
            core_symptoms_count = 0
            for symptom in disorder_details["CoreSymptoms"]:
                chat = {
                    "Question": "",
                    "Chat History": "No History.",
                    "Conversation": {
                        "Psychiatrist": "",
                        "User": ""
                    }
                } 
                system_ques = symptom["question"]
                chat["Question"] = system_ques
                await send_to_frontend({ "question": system_ques,"skip_allowed": False}, websocket)
                print(system_ques)
                user_response = await get_user_response_from_frontend(websocket)
                # user_response = "Yes"
                # user_response = "No"

                if user_response is not None:
                    chat["Conversation"]["Psychiatrist"] = system_ques
                    chat["Conversation"]["User"] = user_response
                    print("calling secondary chat_analysis function")
                    if await chat_analysis(system_ques, user_response, chat, Majordisorder, False, websocket):
                        core_symptoms_count += 1
                else:
                    await send_to_frontend({"question": "I assume you dont want to answer this question, I am concluding your response for the disorder to be negative","skip_allowed": True}, websocket)   
                    continue

            if core_symptoms_count >= core_symptoms_threshold:
                await send_to_frontend({"question": f"Core Symptoms for {disorder_name} disorder are positive","skip_allowed": True}, websocket)
                associated_symptoms_threshold = disorder_details["AssociatedSymptomsCount"]
                associated_symptoms_count = 0
                for symptom in disorder_details["AssociatedSymptoms"]:
                    chat = {
                        "Question": "",
                        "Chat History": "No History.",
                        "Conversation": {
                            "Psychiatrist": "",
                            "User": ""
                        }
                    } 
                    system_ques = symptom["question"]
                    chat["Question"] = system_ques
                    await send_to_frontend({ "question": system_ques,"skip_allowed": False}, websocket)
                    print(system_ques)
                    user_response = await get_user_response_from_frontend(websocket)
                    # user_response = "Yes"
                    # user_response = "No"


                    if user_response is not None:
                        chat["Conversation"]["Psychiatrist"] = system_ques
                        chat["Conversation"]["User"] = user_response
                        print("calling secondary chat_analysis function")
                        if await chat_analysis(system_ques, user_response, chat, Majordisorder, False, websocket):
                            associated_symptoms_count += 1

                        if associated_symptoms_count >= associated_symptoms_threshold:
                            await send_to_frontend({"question": f"\n{disorder_name}: Criteria met for diagnosis. {disorder_name} is confirmed.","skip_allowed": False}, websocket)
                            break
                    else:
                        await send_to_frontend({"question": "I assume you dont want to answer this question, I am concluding your response for the disorder to be negative","skip_allowed": True}, websocket)
                        continue
                        
            await send_to_frontend({"question": "Secondary diagnostics completed","skip_allowed": True}, websocket)
            return {"message": "Secondary diagnostics completed"}

    except Exception as e:
        print(f"Error in secondary diagnostic operation: {e}")
        await send_to_frontend({"question": "Error in secondary diagnostic operation","skip_allowed": True}, websocket)
        return {"error": str(e)}

@app.post("/ws")
async def primary_diagnostic_operator(request: DisorderRequest, websocket: WebSocket):
    try:
        disorder = request.disorder

        questionnaire = load_json("prompts_files/Diagnostics/Pre-diagnosis_ques.json")

        diagnose = False

        for ques in questionnaire[disorder]["questions"]:
            chat = {
                "Question": "",
                "Chat History": "No History.",
                "Conversation": {
                    "Psychiatrist": "",
                    "User": ""
                }
            } 
            system_ques = ques["text"]
            chat["Question"] = system_ques
            await send_to_frontend({ "question": system_ques,"skip_allowed": False}, websocket)
            user_response = await get_user_response_from_frontend(websocket)
            # user_response = "Yes"
            # user_response = "No"
            

            if user_response is not None:
                chat["Conversation"]["Psychiatrist"] = system_ques
                chat["Conversation"]["User"] = user_response
                print("calling chat_analysis function")
                diagnose = await chat_analysis(system_ques, user_response, chat, disorder, diagnose, websocket)
                

        if diagnose:
            await send_to_frontend({
                "question": f"Primary Diagnosis for {disorder} disorder  is positive \n, Please initiate Secondary diagnostics for further confirmation",
                "skip_allowed": True
            }, websocket)
            await secondary_diagnostic_operator(disorder, websocket)

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