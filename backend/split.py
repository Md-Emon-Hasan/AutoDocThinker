import os
import re

TEST_DIR = r"c:\Users\emon1\Desktop\final\AutoDocThinker\backend\tests"

def split_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Match class definitions
    # A class might have methods. We will split by `class Test...:`
    classes = re.split(r'^(class Test\w+:)', content, flags=re.MULTILINE)
    header = classes[0]
    
    # Imports might need to be copied to all files.
    # We will just write each class to a new file, including the header (imports, fixtures).
    
    folder = os.path.dirname(filepath)
    
    for i in range(1, len(classes), 2):
        class_name_match = re.match(r'^class (Test\w+):', classes[i])
        if not class_name_match:
            continue
        
        class_name = class_name_match.group(1)
        # Convert CamelCase to snake_case
        snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
        new_filename = f"{snake_case}.py"
        if not new_filename.startswith("test_"):
            new_filename = "test_" + new_filename
        
        new_filepath = os.path.join(folder, new_filename)
        
        with open(new_filepath, 'w', encoding='utf-8') as f:
            f.write(header.strip() + "\n\n\n" + classes[i] + classes[i+1].rstrip() + "\n")
            
        print(f"Created {new_filepath}")

    # Remove the monolithic file
    os.remove(filepath)
    print(f"Removed {filepath}")


for root, dirs, files in os.walk(TEST_DIR):
    for file in files:
        if file.startswith("test_") and file.endswith(".py") and file != "test_helpers.py":
            split_file(os.path.join(root, file))

