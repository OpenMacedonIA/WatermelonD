import os
import re

DOCS_DIR = "/home/jrodriiguezg/Música/WatermelonD/docsMD"

REPLACEMENTS = {
    # Exact string replacements for paths and strict names
    r'web_client': 'TangerineUI',
    r'modules/skills': 'modules/BlueberrySkills',
    r'modules/extensions': 'modules/Watermelon-extras',
    
    # Case sensitive Name Replacements
    r'NeoCore\.py': 'NeoCore.py', # Preserve filename if specific, or maybe we want to change it? The prompt said "update documentation... no te dejes nada". I'll keep the file reference if it's code, but change the concept.
    # Actually, let's strictly replace the core concept names first
    r'NeoPapaya': 'WatermelonD',
    r'NeoCore': 'WatermelonD',
    r'COLEGA': 'WatermelonD',
    
    # Lowercase variations that might appear in text (be careful not to break urls/code if possible, but docs usually use code blocks)
    # We will use case-insensitive regex for some, or just specific variations found.
    
    # Contextual replacements
    # 'brain' is tricky because it's a common word. match "brain module", "the brain", or paths like "brain/"
    r'brain/': 'BrainNut/',
    r'brain\.py': 'BrainNut.py', # If that file exists? yes it does.
}

# More robust strategy:
# 1. Path/Code replacements (High confidence)
# 2. Proper Noun replacements (High confidence)

def apply_replacements(content):
    new_content = content
    
    # 1. Specific Path/Module Replacements
    new_content = new_content.replace('web_client', 'TangerineUI')
    new_content = new_content.replace('modules/skills', 'modules/BlueberrySkills')
    new_content = new_content.replace('modules/extensions', 'modules/Watermelon-extras')
    
    # 2. General Branding Content
    # We replace NeoCore but we might want to preserve NeoCore.py if the file hasn't changed name yet.
    # However, to be "updated", we likely want the docs to refer to the *System* as WatermelonD.
    # If the file is still NeoCore.py, we might have a mismatch, but the user asked to update "names, references etc".
    # I will replace NeoCore with WatermelonD.
    
    new_content = new_content.replace('NeoPapaya', 'WatermelonD')
    new_content = new_content.replace('NeoCore', 'WatermelonD') 
    new_content = new_content.replace('COLEGA', 'WatermelonD')
    new_content = new_content.replace('openkompai', 'WatermelonD') # Just in case
    
    # 3. Brain -> BrainNut
    # Use Regex to avoid replacing "brainstorm" etc.
    # Replace 'brain' when it is surrounded by whitespace, quotes, or path separators
    new_content = re.sub(r'\bbrain\b', 'BrainNut', new_content)
    
    return new_content

def main():
    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            if file.endswith('.md') or file.endswith('.txt'):
                file_path = os.path.join(root, file)
                print(f"Processing {file_path}...")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                updated_content = apply_replacements(content)
                
                if content != updated_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    print(f"Updated {file}")
                else:
                    print(f"No changes for {file}")

if __name__ == "__main__":
    main()
