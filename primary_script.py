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


def weighted_avg(data, weights=[1, 2, 4]):
    # If no data is available, return None
    if not data:
        return None

    # Use only the last `n` elements based on data length
    n = min(len(data), len(weights))  # Handle cases with fewer elements
    values = data[-n:]  # Take the last `n` elements
    weights = weights[-n:]  # Take the corresponding weights

    # Calculate weighted average
    weighted_sum = sum(v * w for v, w in zip(values, weights))
    return weighted_sum / sum(weights)


@traceable
def llmResponse(ResponceFormat, system_role, max_retries=3, **IOarg) -> PrimaryDiagnosticsResponse:
    setup_environment()
    client = OpenAI()
    attempts = 0
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
            traceback.print_exc()
        
        attempts += 1

    raise ValueError("Max retries exceeded. Could not parse response as JSON.")


def primary_diagnostic_operator(disorder):
    system_role = PromptManager.get_prompt(
        "diagnostics", section="ALL", low=0.2, high=0.8
    )
    questionnaire = load_json("prompts_files/Diagnostics/Pre-diagnosis_ques.json")

    diagnose = False
    for ques in questionnaire[disorder]["questions"]:
        print("Question no", ques["id"], ques["text"])
        score = []
        system_ques = ques["text"]
        requests.post(
            "http://localhost:8000/api/ai_response",
            json={"AIresponce": system_ques, "SkipStatus": False},
        )

        # i want user responce here from the frontend

        while True:
            kwarg_dict = {"ques": system_ques, "chat": user}

            msg = llmResponse(PrimaryDiagnosticsResponse, system_role, **kwarg_dict)

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
            if user == "":
                break

    return diagnose


if __name__ == "__main__":
    setup_environment()
    diagnostics_list = ["Eating"]
    for disorder in diagnostics_list:
        print(
            f"You are eligible for Secondary diagnosis for {disorder if primary_diagnostic_operator(disorder) else 'No disorder'}"
        )
