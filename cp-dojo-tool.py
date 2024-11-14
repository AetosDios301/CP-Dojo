import os
import subprocess
import re
from datetime import datetime

# Define supported platforms and languages
platforms = ["AtCoder", "CodeChef", "Codeforces", "Leetcode"]
languages = {
    "C++": ".cpp",
    "Python": ".py",
    "Java": ".java",
    "JavaScript": ".js",
    "Go": ".go",
    "Kotlin": ".kt",
    "Rust": ".rs",
}

# Function to clear the terminal screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Function to get user input
def get_user_choice(prompt, choices):
    clear_screen()
    print(prompt)
    for i, choice in enumerate(choices, 1):
        print(f"{i}. {choice}")
    while True:
        try:
            choice = int(input("Enter the number of your choice: "))
            if 1 <= choice <= len(choices):
                return choices[choice - 1]
            else:
                print("Invalid choice. Please select a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

# Function to extract contest and problem codes from a URL
def extract_codes_from_link(link, platform):
    if platform == "Codeforces":
        match = re.search(r"/problemset/problem/(\d+)/([A-Za-z0-9]+)", link)
        if match:
            return match.group(1), match.group(2)
    elif platform == "Leetcode":
        match = re.search(r"/problems/([a-z0-9-]+)/", link)
        if match:
            return "leetcode", match.group(1).replace("-", "_")
    elif platform == "CodeChef":
        match = re.search(r"/([A-Z0-9]+)/problems/([A-Z0-9]+)", link)
        if match:
            return match.group(1), match.group(2)
    elif platform == "AtCoder":
        match = re.search(r"/contests/([a-z0-9]+)/tasks/([a-z0-9_]+)", link)
        if match:
            return match.group(1), match.group(2)
    print(f"Error: Could not extract contest and problem codes from the URL: {link}")
    return "unknown", "unknown"

# Function to update the daily log
def update_daily_log(platform, contest_code, problem_code, problem_link):
    log_filename = "daily_log.md"  # Define your log file name here
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = f"### {date_str}\n- **Platform**: {platform}\n- **Contest Code**: {contest_code}\n- **Problem Code**: {problem_code}\n- [Problem Link]({problem_link})\n\n"
    
    # Append the log entry to the file
    with open(log_filename, "a") as log_file:
        log_file.write(log_entry)
    
    print(f"Daily log updated with {problem_code}.")

# Function to create files and open VSCode
def create_files_and_open_vscode(platform, language, problem_link):
    # Extract contest and problem codes
    contest_code, problem_code = extract_codes_from_link(problem_link, platform)

    if contest_code == "unknown":
        print("Could not extract contest and problem codes. Exiting...")
        return

    # Define base paths
    base_dir = "My-CP-Dojo"
    solutions_dir = os.path.join(base_dir, "Solutions", platform)
    questions_dir = os.path.join(base_dir, "Practiced-Problems", platform, "Questions")
    thought_process_dir = os.path.join(base_dir, "Practiced-Problems", platform, "Thought-Process")
    
    # Create directories if they don't exist
    os.makedirs(solutions_dir, exist_ok=True)
    os.makedirs(questions_dir, exist_ok=True)
    os.makedirs(thought_process_dir, exist_ok=True)

    # Create the solution file
    solution_filename = f"solution-{contest_code}_{problem_code}{languages[language]}"
    solution_filepath = os.path.join(solutions_dir, solution_filename)
    with open(solution_filepath, "w") as f:
        f.write("// Your solution code goes here\n")

    # Create the question link file
    question_filename = f"{contest_code}_{problem_code}.txt"
    question_filepath = os.path.join(questions_dir, question_filename)
    with open(question_filepath, "w") as f:
        f.write(problem_link)

    # Create a thought process file
    thought_filename = f"{contest_code}_{problem_code}.md"
    thought_filepath = os.path.join(thought_process_dir, thought_filename)
    with open(thought_filepath, "w") as f:
        f.write("# Thought Process\n\nDescribe your approach and reasoning here.")

    # Update the daily log
    update_daily_log(platform, contest_code, problem_code, problem_link)

    # Open VSCode in the Solutions directory
    subprocess.run(["code", solutions_dir])

    print(f"Files created and VSCode opened in {solutions_dir}")

# Main function
def main():
    clear_screen()  # Clear the screen before starting the process
    print("Welcome to My-CP-Dojo CLI Tool!")

    # Get platform choice
    platform = get_user_choice("Select the platform you're using:", platforms)
    
    # Get language choice
    language = get_user_choice("Select the language you're using:", list(languages.keys()))
    
    # Get problem link
    problem_link = input("Paste the problem link: ").strip()
    
    # Create files and open VSCode
    create_files_and_open_vscode(platform, language, problem_link)

if __name__ == "__main__":
    main()
