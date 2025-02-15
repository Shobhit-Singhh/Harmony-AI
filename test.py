# from src.utils.loader import *
# def test_jinja_loader():
#     prompt = PromptManager.get_prompt("diagnostics", section = "ROLE TASK INPUTS" ,ques="How are you feeling today?")
#     print(prompt)
    
# test_jinja_loader()



# ----------------------------------------------------------------------------------------------------------------------------------------------------------------
# from src.utils.loader import *
# def test_load_yaml():
#     # write a function to call the yaml loader function and print the contents of the yaml file
#     data = load_yaml("Prompts/Elements/01_yaml_tags/CALIBRATION.yaml")
#     print(data['diagnostic'])
# test_load_yaml()

# ----------------------------------------------------------------------------------------------------------------------------------------------------------------
# from src.utils.loader import *
# def test_load_json():
#     data = load_json("prompts_files/Diagnostics/Pre-diagnosis_ques.json")
#     print(data["Dissociation"])
# test_load_json()



# # With System Resopnse
#     # if skip is allowed change the button colour to green
# print(system_ques)
# if skip_allowed:
#     print("you can move to next question")
    
# # Return type cantains the response of the user and button input
#         # if resonse is empty we will put the button to False
#         # if response is not empty we will push the responce to the LLM queue
# user = input("Your response: ")
# if user == "":
#     if input("Caution: Do you want to skip the question?") == "y":
#         break




# API testing script
from openai import OpenAI

# Replace with your actual API key
client = OpenAI(api_key="")

completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": "write a essay no mom."
        }
    ]
)

print(completion.choices[0].message)





















{% if 'EXAMPLES' in section or 'ALL' in section %}
### Examples:

#### Example 1: 
##### Input:
Question: "Do you often feel sad or anxious?"
User: "I’m not sure. I sometimes feel a little weird."
Psychiatrist: "Can you describe how you feel?"
User: "I don’t know... I just feel something, but it’s not exactly sad or anxious."
Psychiatrist: "When you feel this way, does it affect your daily activities?"
User: "I guess, sometimes."
Psychiatrist: "Could you give me more details about how it affects you?"
User: "I’m not sure."

##### Output (JSON):
{
  "clarity_score": 0.3,
  "positive_score": 0.5,
  "reasoning": [
    "<Step 1>: The conversation is on-topic, but the user’s responses are vague and unclear about their emotions.",
    "<Step 2>: The user’s responses are not specific enough to assess their emotional state clearly.",
    "<Step 3>: The conversation does not conclusively lead to a 'yes' or 'no' answer regarding feelings of sadness or anxiety.",
    "<Step 4>: Follow-up questions are needed to get a clearer understanding of the user’s emotional state."
  ],
  "concluding_prompt": "I need more details to understand if you’re experiencing sadness or anxiety.",
  "clarification_guidance": "Could you describe how you feel more specifically? Are you noticing any patterns in your mood?"
}

#### Example 2: 
##### Input:
Question: "Have you been feeling hopeless recently?"
User: "I’ve been feeling down for the past few weeks, and I don’t think things will get better."
Psychiatrist: "What has been making you feel this way?"
User: "It’s mostly work-related stress and personal problems."
Psychiatrist: "How do you usually cope with these feelings?"
User: "I try to ignore them, but they’re overwhelming."

##### Output (JSON):
{
  "clarity_score": 0.9,
  "positive_score": 0.8,
  "reasoning": [
    "<Step 1>: The conversation is on-topic, and the responses are clear and provide relevant information about the user’s emotional state.",
    "<Step 2>: The user’s answers are clear, the conversation provide a definite 'yes' or 'no' answer about hopelessness.",
    "<Step 3>: There is no direct confirmation of hopelessness, though the user shows signs of it. The conversation is leaning towards a possible indication of hopelessness.",
    "<Step 4>: More exploration is needed to conclude if hopelessness is present."
  ],
  "concluding_prompt": " You're experiencing feelings of hopelessness.",
  "clarification_guidance": "Can you share more about how your thoughts about the future are affecting your day-to-day life?"
}

#### Example 3: 
##### Input:
Question: "Are you experiencing any difficulty sleeping?"
User: "I guess I just wake up a lot."
Psychiatrist: "How often does this happen?"
User: "Almost every night."
Psychiatrist: "Do you feel rested when you wake up?"
User: "Not at all."

##### Output (JSON):
{
  "clarity_score": 0.5,
  "positive_score": 0.9,
  "reasoning": [
    "<Step 1>: The conversation stays on-topic, but the user’s responses are somewhat vague.",
    "<Step 2>: The responses are clear enough to identify that the user is having trouble with sleep, but not detailed enough to provide a full picture.",
    "<Step 3>: The conversation conclusively leads to difficulty sleeping due to frequent waking at night.",
    "<Step 4>: No further follow-up is needed, though the clarity score could be improved."
  ],
  "concluding_prompt": "Based on what you've shared, it seems you are experiencing difficulty sleeping due to frequent awakenings at night.",
  "clarification_guidance": "If possible, try to provide more details about how often you wake up and how it affects your daily life."
}

#### Example 4:
##### Input:
Question: "Have you been feeling depressed lately?"
User: "I’ve been feeling low and unmotivated. I don’t enjoy things I used to, and I often feel empty."
Psychiatrist: "How long have you been feeling this way?"
User: "For the past three months."
Psychiatrist: "Have you noticed any changes in your sleep or appetite?"
User: "Yes, I’ve been sleeping more but still feel tired. I don’t have much appetite."
Psychiatrist: "Do you find it difficult to perform your daily tasks?"
User: "Yes, I struggle with getting things done."

##### Output (JSON):
{
  "clarity_score": 1.0,
  "positive_score": 1.0,
  "reasoning": [
    "<Step 1>: The conversation is clearly on-topic, with the user providing detailed and relevant responses about their emotional state.",
    "<Step 2>: The responses are clear and specific, outlining symptoms that suggest depression.",
    "<Step 3>: The conversation clearly leads to a conclusion that the user is experiencing depression.",
    "<Step 4>: No follow-up questions are necessary as the responses are sufficient to conclude the situation."
  ],
  "concluding_prompt": "Based on your responses, it appears you are experiencing symptoms of depression. We can discuss possible treatment options or further steps.",
  "clarification_guidance": "If there are any other symptoms or concerns you'd like to discuss, feel free to share."
}


#### Example 5: 
##### Input:
Question: "Do you often feel sad or anxious?"
User: "I sometimes feel a little weird. But its not sadness or anxious"
Psychiatrist: "Can you describe how you feel?"
User: "I don’t know... I just feel something, but it’s not exactly sad or anxious."
Psychiatrist: "When you feel this way, does it affect your daily activities?"
User: "I guess, sometimes."
Psychiatrist: "Could you give me more details about how it affects you?"
User: "I’m not sure."

##### Output (JSON):
{
  "clarity_score": 0.8,
  "positive_score": 0.1,
  "reasoning": [
    "<Step 1>: The conversation is on-topic, but the user’s responses are vague and unclear about their emotions.",
    "<Step 2>: The user’s responses are not specific enough to assess their emotional state clearly.",
    "<Step 3>: The conversation does conclusively lead to a clear 'no' answer regarding feelings of sadness or anxiety.",
    "<Step 4>: Follow-up questions are needed to get a clearer understanding of the user’s emotional state."
  ],
  "concluding_prompt": "I need more details to understand if you’re experiencing sadness or anxiety.",
  "clarification_guidance": "Could you describe how you feel more specifically? Are you noticing any patterns in your mood?"
}
{% endif %}
