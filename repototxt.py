# repototext.py

import os
from github import Github
from tqdm import tqdm
from dotenv import load_dotenv
import json

load_dotenv()  # Load environment variables from .env file

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

def get_readme_content(repo):
    try:
        readme = repo.get_contents("README.md")
        return readme.decoded_content.decode('utf-8')
    except:
        return "README not found."

def traverse_repo_iteratively(repo):
    structure = ""
    dirs_to_visit = [("", repo.get_contents(""))]
    dirs_visited = set()

    while dirs_to_visit:
        path, contents = dirs_to_visit.pop()
        dirs_visited.add(path)
        for content in tqdm(contents, desc=f"Processing {path}", leave=False):
            if content.type == "dir":
                if content.path not in dirs_visited:
                    structure += f"{path}/{content.name}/\n"
                    dirs_to_visit.append((f"{path}/{content.name}", repo.get_contents(content.path)))
            else:
                structure += f"{path}/{content.name}\n"
    return structure

def get_file_contents(path, binary_extensions):
    file_contents = ""
    for root, _, files in os.walk(path):
        for name in files:
            if not is_binary(name, binary_extensions):
                file_path = os.path.join(root, name)
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    file_contents += f"File: /{os.path.relpath(file_path, path)}\nContent:\n{content}\n\n"
                except UnicodeDecodeError:
                    file_contents += f"File: /{os.path.relpath(file_path, path)}\nContent: Skipped due to encoding issue\n\n"
                except:
                    file_contents += f"File: /{os.path.relpath(file_path, path)}\nContent: Error reading file\n\n"
            else:
                file_contents += f"File: /{os.path.relpath(os.path.join(root, name), path)}\nContent: Skipped binary file\n\n"
    return file_contents

def get_binary_extensions():
    return [
        '.exe', '.dll', '.so', '.a', '.lib', '.dylib', '.o', '.obj', '.zip', '.tar', '.tar.gz', '.tgz', '.rar', '.7z', 
        '.bz2', '.gz', '.xz', '.z', '.lz', '.lzma', '.lzo', '.rz', '.sz', '.dz', '.pdf', '.doc', '.docx', '.xls', 
        '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp', '.png', '.jpg', '.jpeg', '.gif', '.mp3', '.mp4', '.wav', 
        '.flac', '.ogg', '.avi', '.mkv', '.mov', '.webm', '.wmv', '.m4a', '.aac', '.iso', '.vmdk', '.qcow2', '.vdi', 
        '.vhd', '.vhdx', '.ova', '.ovf', '.db', '.sqlite', '.mdb', '.accdb', '.frm', '.ibd', '.dbf', '.jar', '.class', 
        '.war', '.ear', '.jpi', '.pyc', '.pyo', '.pyd', '.egg', '.whl', '.deb', '.rpm', '.apk', '.msi', '.dmg', 
        '.pkg', '.bin', '.dat', '.data', '.dump', '.img', '.toast', '.vcd', '.crx', '.xpi', '.lockb', 'package-lock.json', 
        '.svg', '.eot', '.otf', '.ttf', '.woff', '.woff2', '.ico', '.icns', '.cur', '.cab', '.dmp', '.msp', '.msm', 
        '.keystore', '.jks', '.truststore', '.cer', '.crt', '.der', '.p7b', '.p7c', '.p12', '.pfx', '.pem', '.csr', 
        '.key', '.pub', '.sig', '.pgp', '.gpg', '.nupkg', '.snupkg', '.appx', '.msix', '.msp', '.msu', '.deb', 
        '.rpm', '.snap', '.flatpak', '.appimage', '.ko', '.sys', '.elf', '.swf', '.fla', '.swc', '.rlib', '.pdb', 
        '.idb', '.dbg', '.sdf', '.bak', '.tmp', '.temp', '.log', '.tlog', '.ilk', '.bpl', '.dcu', '.dcp', '.dcpil', 
        '.drc', '.aps', '.res', '.rsrc', '.rc', '.resx', '.prefs', '.properties', '.ini', '.cfg', '.config', '.conf', 
        '.DS_Store', '.localized', '.svn', '.git', '.gitignore', '.gitkeep'
    ]

def get_file_contents_iteratively(repo):
    file_contents = ""
    dirs_to_visit = [("", repo.get_contents(""))]
    dirs_visited = set()
    binary_extensions = get_binary_extensions()

    while dirs_to_visit:
        path, contents = dirs_to_visit.pop()
        dirs_visited.add(path)
        for content in tqdm(contents, desc=f"Downloading {path}", leave=False):
            if content.type == "dir":
                if content.path not in dirs_visited:
                    dirs_to_visit.append((f"{path}/{content.name}", repo.get_contents(content.path)))
            else:
                if any(content.name.endswith(ext) for ext in binary_extensions):
                    file_contents += f"File: {path}/{content.name}\nContent: Skipped binary file\n\n"
                else:
                    file_contents += f"File: {path}/{content.name}\n"
                    try:
                        decoded_content = content.decoded_content.decode('utf-8')
                        file_contents += f"Content:\n{decoded_content}\n\n"
                    except UnicodeDecodeError:
                        file_contents += "Content: Skipped due to encoding issue\n\n"
                    except:
                        file_contents += "Content: Error reading file\n\n"
    return file_contents

def is_binary(filename, binary_extensions):
    return any(filename.endswith(ext) for ext in binary_extensions)

def get_repo_contents(repo_url):
    repo_name = repo_url.split('/')[-1]
    if not GITHUB_TOKEN:
        raise ValueError("Please set the 'GITHUB_TOKEN' environment variable.")
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(repo_url.replace('https://github.com/', ''))
    print(f"Fetching README for: {repo_name}")
    readme_content = get_readme_content(repo)

    print(f"\nFetching repository structure for: {repo_name}")
    repo_structure = f"Repository Structure: {repo_name}\n"
    repo_structure += traverse_repo_iteratively(repo)

    print(f"\nFetching file contents for: {repo_name}")
    file_contents = get_file_contents_iteratively(repo)

    instructions = f"Prompt: Analyze the {repo_name} repository to understand its structure, purpose, and functionality. Follow these steps to study the codebase:\n\n"
    instructions += "1. Read the README file to gain an overview of the project, its goals, and any setup instructions.\n\n"
    instructions += "2. Examine the repository structure to understand how the files and directories are organized.\n\n"
    instructions += "3. Identify the main entry point of the application (e.g., main.py, app.py, index.js) and start analyzing the code flow from there.\n\n"
    instructions += "4. Study the dependencies and libraries used in the project to understand the external tools and frameworks being utilized.\n\n"
    instructions += "5. Analyze the core functionality of the project by examining the key modules, classes, and functions.\n\n"
    instructions += "6. Look for any configuration files (e.g., config.py, .env) to understand how the project is configured and what settings are available.\n\n"
    instructions += "7. Investigate any tests or test directories to see how the project ensures code quality and handles different scenarios.\n\n"
    instructions += "8. Review any documentation or inline comments to gather insights into the codebase and its intended behavior.\n\n"
    instructions += "9. Identify any potential areas for improvement, optimization, or further exploration based on your analysis.\n\n"
    instructions += "10. Provide a summary of your findings, including the project's purpose, key features, and any notable observations or recommendations.\n\n"
    instructions += "Use the files and contents provided below to complete this analysis:\n\n"

    return repo_name, instructions, readme_content, repo_structure, file_contents

def analyze_local_repo(path, binary_extensions):
    print(f"Analyzing local repository at: {path}")
    readme_content = get_readme_content(path)
    repo_structure = traverse_directory(path)
    file_contents = get_file_contents(path, binary_extensions)
    output_content = "README:\n" + readme_content + "\n\n" + repo_structure + "\n\n" + file_contents
    return output_content

def traverse_directory(path):
    structure = "Repository Structure:\n"
    for root, dirs, files in os.walk(path):
        relative_path = os.path.relpath(root, path)
        if relative_path == '.':
            relative_path = ''
        else:
            relative_path += '/'
        for name in dirs:
            structure += f"/{relative_path}{name}/\n"
        for name in files:
            structure += f"/{relative_path}{name}\n"
    return structure

def get_prompt(prompt_path):
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def main():
    while True:
        method = input("Do you want to analyze a local repository or a GitHub repository? (local/remote): ").strip().lower()
        if method in ["local", "remote"]:
            break
        print("Invalid input. Please enter 'local' or 'remote'.")

    if method == "local":
        repo_path = input("Enter the full path to the local repository: ").strip()
        binary_extensions = get_binary_extensions()
        analysis_result = analyze_local_repo(repo_path, binary_extensions)
        repo_name = os.path.basename(repo_path)
        output_filename = f"{repo_name}_contents.txt"
    elif method == "remote":
        repo_url = input("Enter the GitHub repository URL: ").strip()
        repo_name, instructions, readme_content, repo_structure, file_contents = get_repo_contents(repo_url)
        analysis_result = instructions + f"README:\n{readme_content}\n\n" + repo_structure + '\n\n' + file_contents
        output_filename = f'{repo_name}_contents.txt'

    prompt = get_prompt("prompt.txt")
    analysis_result = (prompt + analysis_result).replace("##REPO_NAME##", repo_name)
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(repo_name, instructions, readme_content, repo_structure, file_contents = get_repo_contents(repo_url)
        analysis_result = instructions + f"README:\n{readme_content}\n\n" + repo_structure + "\n\n" + file_contents
        output_filename = f"{repo_name}_contents.txt"

    prompt = get_prompt("prompt.txt")
    analysis_result = (prompt + analysis_result).replace("##REPO_NAME##", repo_name)
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(analysis_result)
    print(f"Repository contents saved to '{output_filename}'.")

if __name__ == '__main__':
    main()
