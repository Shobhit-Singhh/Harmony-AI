from openai import OpenAI
import json
from langsmith import traceable
from src.utils.env import *
from src.utils.loader import *
from src.utils.object import *
from pydantic import ValidationError
import requests


# <<-------------------------------------------------------
import random
from types import SimpleNamespace


# # --------------------------------------------------------------------------
#             msg = SimpleNamespace(
#                 confidence_score = float(input("Confidence score: ")),
#                 concluding_prompt="#################################",
#                 clarification_guidance="&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&"
#             )
# 
def primary_diagnostic_operator(disorder):
    system_role = PromptManager.get_prompt("diagnostics", section = "ALL", low = 0.2, high = 0.8)
    questionnaire = load_json("prompts_files/Diagnostics/Pre-diagnosis_ques.json")

    diagnose = False
    for ques in questionnaire[disorder]["questions"]:
        print("Question no", ques["id"], ques["text"])
        score = []
        system_ques = ques["text"]
        requests.post("http://localhost:8000/api/ai_response", json={"AIresponce": system_ques, "SkipStatus": False})
        
        # i want user responce here from the frontend

        while True:
            kwarg_dict = {
                "ques": system_ques,
                "chat": user
            }
            
            msg = llmResponse(PrimaryDiagnosticsResponce, system_role, **kwarg_dict)
            

            score.append(msg.confidence_score)

            print("your score is: ", weighted_avg(score))
            skip_allowed = False

            if weighted_avg(score) > 0.7 or weighted_avg(score) < 0.3:
                system_ques = msg.concluding_prompt
                skip_allowed = True
                
            else:
                system_ques = msg.concluding_prompt + " " + msg.clarification_guidance
            
            if weighted_avg(score) > 0.7:
                diagnose = True


            
            # i want to send the backend respnse {system_ques, skip_allowed} to the frontend and get the user response
            if user == "": break

    return diagnose

