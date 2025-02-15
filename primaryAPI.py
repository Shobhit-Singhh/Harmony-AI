from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.utils.object import *
from primary_script import *
import requests
import asyncio
import json
from typing import List
from pydantic import BaseModel
from langsmith import traceable

class DisorderRequest(BaseModel):
    disorder: str

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
                if diagnosis_result and disorder == "Depression" or disorder == "Anxiety":
                    await send_to_frontend({
                        "question": "Initiating Secondary Diagnostics for further confirmation",
                        "skip_allowed": True
                    }, websocket)
                    await secondary_diagnostic_operator(disorder, websocket)
                elif diagnosis_result and disorder != "Depression" or disorder != "Anxiety":
                    await send_to_frontend({
                        "question": """As of now I can Diagnose only following Secondary Disorders:\n 
                        1. Depression\n
                        2. Anxiety\n
                        """,
                        "skip_allowed": True
                    }, websocket)

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
        
        system_role = PromptManager.get_prompt("diagnostics", section="ALL", low=0.2, high=0.8)
        questionnaire = load_json("prompts_files/Diagnostics/Pre-diagnosis_ques.json")

        diagnose = False
        question_text = ""

        for ques in questionnaire[disorder]["questions"]:

            system_ques = ques["text"]
            question_text = system_ques
            score = []

            # Send question to frontend
            await send_to_frontend({ "question": system_ques,"skip_allowed": False}, websocket)
            user_response = await get_user_response_from_frontend(websocket)

            chat = []
            chat.append({"role": "user", "content": user_response})
            chat_count = 2
            while chat_count > 0:
                kwarg_dict = {"ques": system_ques,"chat": chat,}
                print("Question:", chat)
                msg = llmResponse(PrimaryDiagnosticsResponse, system_role, **kwarg_dict)
                print("Confidence score:", msg.confidence_score)
                print("Concluding prompt:", msg.concluding_prompt)
                print("Clarification guidance:", msg.clarification_guidance)
                
                skip_allowed = False
                system_ques = msg.concluding_prompt
                if msg.confidence_score > 0.7: # Yes: Response 
                    diagnose = True
                    
                if (msg.confidence_score > 0.7 or msg.confidence_score < 0.3):
                    skip_allowed = True
                    chat_count -= 1
                else: # Ambiguous response
                    system_ques = system_ques + msg.clarification_guidance
                await send_to_frontend({"question": f"{system_ques} [{msg.confidence_score}]","skip_allowed": skip_allowed}, websocket)
                if chat_count > 0:
                    user_response = await get_user_response_from_frontend(websocket)
                
                chat.append({"role": "system", "content": system_ques})
                chat.append({"role": "user", "content": user_response})

                if user_response == None:
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

@app.post("/ws")
async def secondary_diagnostic_operator(Majordisorder: str, websocket: WebSocket):
    try:
        system_role = PromptManager.get_prompt("diagnostics", section="ALL", low=0.2, high=0.8)
        questionnaire = load_json("prompts_files/Diagnostics/Secondary-diagnosis_ques.json")

        for disorder_name, disorder_details in questionnaire[Majordisorder].items():
            await send_to_frontend({"question": f"\nStarting questionnaire for: {disorder_name}","skip_allowed": False}, websocket)

            core_symptoms_count = disorder_details["CoreSymptomsCount"]
            print("Core symptoms count:", core_symptoms_count)
            core_symptoms_yes_count = 0
            for symptom in disorder_details["CoreSymptoms"]:
                chat = []
                ques = symptom["question"]
                print("Core symptom question:", ques)
                await send_to_frontend({"question": ques,"skip_allowed": False}, websocket)
                responce = await get_user_response_from_frontend(websocket)
                chat.append({"role": "system", "content": ques})
                chat.append({"role": "user", "content": responce})
                skip_allowed = False
                while True:
                    kwarg_dict = {
                        "ques": ques,
                        "chat": chat,
                    }
                    
                    ques = ""
                    
                    msg = llmResponse(PrimaryDiagnosticsResponse, system_role, **kwarg_dict)
                    # msg = SimpleNamespace(
                    #     confidence_score = float(input("Confidence score: ")),
                    #     concluding_prompt="*********************************",
                    #     clarification_guidance="@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
                    # )

                    skip_allowed = False

                    ques = msg.concluding_prompt
                    if msg.confidence_score < 0.7:
                        ques = ques + " " + msg.clarification_guidance
                    if msg.confidence_score < 0.3 or msg.confidence_score > 0.7:
                        skip_allowed = True  

                    chat.append({"role": "system", "content": ques})
                    
                    await send_to_frontend({"question": ques,"skip_allowed": skip_allowed}, websocket)
                    response = await get_user_response_from_frontend(websocket)
                    if response == None:
                        if msg.confidence_score > 0.7:
                            core_symptoms_yes_count += 1
                        break

                    chat.append({"role": "user", "content": response}) 

                if core_symptoms_yes_count >= core_symptoms_count:
                    break

            if core_symptoms_yes_count < core_symptoms_count:
                await send_to_frontend({"question": f"\n{disorder_name}: Insufficient core symptoms. Your diagnosis is negative.","skip_allowed": False}, websocket) 
                continue

            associated_symptoms_count = disorder_details["AssociatedSymptomsCount"]
            associated_symptoms_yes_count = 0

            for symptom in disorder_details["AssociatedSymptoms"]:
                chat = []
                ques = symptom["question"]
                await send_to_frontend({"question": ques,"skip_allowed": False}, websocket)
                responce = await get_user_response_from_frontend(websocket)
                chat.append({"role": "system", "content": ques})
                chat.append({"role": "user", "content": responce})
                skip_allowed = False
                while True:
                    kwarg_dict = {
                        "ques": ques,
                        "chat": chat,
                    }
                    
                    ques = ""
                    msg = llmResponse(PrimaryDiagnosticsResponse, system_role, **kwarg_dict)
                    
                    # msg = SimpleNamespace(
                    #     confidence_score = float(input("Confidence score: ")),
                    #     concluding_prompt="*********************************",
                    #     clarification_guidance="@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
                    # )
                    skip_allowed = False

                    ques = msg.concluding_prompt
                    if msg.confidence_score < 0.7:
                        ques = ques + " " + msg.clarification_guidance
                    if msg.confidence_score < 0.3 or msg.confidence_score > 0.7:
                        skip_allowed = True
                        
                    chat.append({"role": "system", "content": ques})
                    
                    await send_to_frontend({"question": ques,"skip_allowed": skip_allowed}, websocket)
                    response = await get_user_response_from_frontend(websocket)
                    if response == None:
                        if msg.confidence_score > 0.7:
                            associated_symptoms_yes_count += 1
                        break

                    chat.append({"role": "user", "content": response}) 

                if associated_symptoms_yes_count >= associated_symptoms_count:
                    break

            if associated_symptoms_yes_count >= associated_symptoms_count:
                await send_to_frontend({"question": f"\n{disorder_name}: Criteria met for diagnosis. {disorder_name} is confirmed.","skip_allowed": False}, websocket)
                break
            else:
                await send_to_frontend({"question": f"\n{disorder_name}: Criteria not met for diagnosis. Moving to the next disorder.","skip_allowed": False}, websocket)
                continue
        await send_to_frontend({"question": "Secondary diagnostics completed","skip_allowed": True}, websocket)
        return {"message": "Secondary diagnostics completed"}
    except Exception as e:
        print(f"Error in secondary diagnostic operation: {e}")
        await send_to_frontend({"question": "Error in secondary diagnostic operation","skip_allowed": True}, websocket)
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)