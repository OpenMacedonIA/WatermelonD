import sys
import os
import json
from rapidfuzz import process, fuzz

# Mock loading intents
def load_intents():
    try:
        with open("config/intents.json", "r") as f:
            data = json.load(f)
            return data.get('intents', [])
    except:
        return []

def test_matching():
    intents = load_intents()
    triggers = []
    for intent in intents:
        triggers.extend(intent.get('triggers', []))
    
    test_cases = [
        "cuál es la ip",
        "cuál es mi bebé",
        "hola",
        "qué día de la semana es"
    ]
    
    print(f"Loaded {len(triggers)} triggers.")
    
    for text in test_cases:
        print(f"\nTesting: '{text}'")
        
        # WRatio
        match = process.extractOne(text, triggers, scorer=fuzz.WRatio)
        if match:
            trigger, score, _ = match
            print(f"  WRatio: '{trigger}' ({score})")
            
        # TokenSet
        match_token = process.extractOne(text, triggers, scorer=fuzz.token_set_ratio)
        if match_token:
            trigger, score, _ = match_token
            print(f"  TokenSet: '{trigger}' ({score})")
            
        # PartialRatio
        match_partial = process.extractOne(text, triggers, scorer=fuzz.PartialRatio)
        if match_partial:
            trigger, score, _ = match_partial
            print(f"  PartialRatio: '{trigger}' ({score})")

if __name__ == "__main__":
    test_matching()
