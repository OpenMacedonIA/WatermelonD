import sys
import os
import logging
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Mock dependencies
sys.modules['modules.utils'] = MagicMock()
sys.modules['modules.logger'] = MagicMock()

# Mock load_json_data to return some dummy intents
def mock_load_json_data(path, key):
    if 'intents' in path:
        return [{'triggers': ['hola', 'buenos dias'], 'action': 'greet'}]
    return []

sys.modules['modules.utils'].load_json_data = mock_load_json_data

from modules.intent_manager import IntentManager

def test_intent_manager():
    print("--- Testing IntentManager Fix ---")
    
    config_mock = MagicMock()
    config_mock.get.return_value = {}
    
    manager = IntentManager(config_mock)
    
    # Test exact match
    print("Testing 'hola'...")
    result = manager.find_best_intent("hola")
    if result and result['action'] == 'greet':
        print("PASS: Exact match found.")
    else:
        print(f"FAIL: Exact match not found. Result: {result}")

    # Test fuzzy match (should trigger the fixed code path)
    print("Testing 'hola que tal'...")
    try:
        result = manager.find_best_intent("hola que tal")
        print(f"PASS: Fuzzy match executed without error. Result: {result}")
    except NameError as e:
        print(f"FAIL: NameError detected: {e}")
    except Exception as e:
        print(f"FAIL: Exception detected: {e}")

if __name__ == "__main__":
    test_intent_manager()
