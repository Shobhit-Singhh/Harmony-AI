from primary_script import *
from secondary_script import *
from src.utils.env import *


def report():
    setup_environment()
    disorder_list = ["Eating", "Dissociation"]
    diagnostics_list = {dis: False for dis in disorder_list}

    for disorder in diagnostics_list:
        if diagnostic_operator(disorder):  # Check if the disorder is eligible for secondary diagnosis
            diagnostics_list[disorder] = True
            
    for disorder in diagnostics_list:
        print(f"You are eligible for Secondary diagnosis for {disorder if diagnostics_list[disorder] else 'No disorder'} disorder")
        
    # print("You are diagnosed with", [disorder for disorder in diagnostics_list if diagnostics_list[disorder]])
    
    print()
    print()
    
    print(diagnostics_list)

if __name__ == "__main__":
    report()