import os
import re

# Directory containing the project files
BASE_DIR = 'S:/Piprline-SourceCode'

# Define patterns to search for AWS credentials
aws_patterns = [
    r'(?i)AWS_ACCESS_KEY_ID[\s]*=[\s]*"?([A-Z0-9]+)"?',
    r'(?i)AWS_SECRET_ACCESS_KEY[\s]*=[\s]*"?([A-Za-z0-9/+=]+)"?',
    r'(?i)access_key[\s]*=[\s]*"?([A-Z0-9]+)"?',
    r'(?i)secret_key[\s]*=[\s]*"?([A-Za-z0-9/+=]+)"?',
    r'(?i)aws_access_key[\s]*=[\s]*"?([A-Z0-9]+)"?',
    r'(?i)aws_secret_key[\s]*=[\s]*"?([A-Za-z0-9/+=]+)"?'
]

replacement_code = """
import os
from dotenv import load_dotenv

load_dotenv()

os.getenv('AWS_ACCESS_KEY_ID').getenv('AWS_ACCESS_KEY_ID')
os.getenv('AWS_SECRET_ACCESS_KEY').getenv('AWS_SECRET_ACCESS_KEY')
"""

def clean_aws_credentials(base_dir):
    modified_files = []
    
    for subdir, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(subdir, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                original_content = content
                needs_env_import = False
                
                # Check for AWS keys in the file
                for pattern in aws_patterns:
                    if re.search(pattern, content):
                        needs_env_import = True
                        # Replace hardcoded keys with environment variables
                        content = re.sub(pattern, 
                                       lambda m: f"os.getenv('AWS_ACCESS_KEY_ID')" if 'ACCESS_KEY_ID' in m.group(0) 
                                       else f"os.getenv('AWS_SECRET_ACCESS_KEY')",
                                       content)
                
                if needs_env_import and original_content != content:
                    # Add imports at the top if they don't exist
                    if 'import os' not in content:
                        content = 'import os\nfrom dotenv import load_dotenv\n\nload_dotenv()\n\n' + content
                    modified_files.append(file_path)
                    
                    # Write back the modified content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                        print(f'Modified {file_path}')
    
    return modified_files

# Run the cleaning function
modified_files = clean_aws_credentials(BASE_DIR)

if modified_files:
    print("\nModified files (need to be committed):")
    for file in modified_files:
        print(f"- {file}")
    
    print("\nNext steps:")
    print("1. Create a .env file with your AWS credentials")
    print("2. Add .env to .gitignore if not already present")
    print("3. Review the modified files")
    print("4. Commit the changes")
else:
    print("No files containing AWS credentials were found.")
