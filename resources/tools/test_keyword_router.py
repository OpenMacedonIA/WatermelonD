import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from modules.keyword_router import KeywordRouter

# Mock Logger
logging.basicConfig(level=logging.INFO)

def test_restart_nginx():
    print("--- Testing Restart Nginx ---")
    router = KeywordRouter()
    
    # Test Case 1: Exact match
    text = "Tío, reinicia el servicio de nginx"
    print(f"Input: '{text}'")
    result = router.process(text)
    print(f"Result: {result}")
    
    if "nginx" in str(result) and ("Éxito" in str(result) or "Error" in str(result) or "Permiso" in str(result)):
        print("PASS: Detected and attempted restart.")
    else:
        print("FAIL: Did not detect or attempt restart correctly.")

    # Test Case 2: No match
    text = "Hola, ¿qué tal?"
    print(f"\nInput: '{text}'")
    result = router.process(text)
    print(f"Result: {result}")
    
    if result is None:
        print("PASS: Correctly ignored non-keyword text.")
    else:
        print("FAIL: Should return None.")

    # Test Case 3: Different service
    text = "reinicia el servicio de apache2"
    print(f"\nInput: '{text}'")
    result = router.process(text)
    print(f"Result: {result}")
    
    if "apache2" in str(result):
         print("PASS: Detected apache2.")
    else:
         print("FAIL: Did not detect apache2.")

if __name__ == "__main__":
    test_restart_nginx()
