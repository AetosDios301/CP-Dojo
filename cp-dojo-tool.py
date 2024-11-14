import os
import subprocess
import re
from datetime import datetime
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
import logging
from pathlib import Path
import json
import sqlite3

@dataclass
class ProblemInfo:
    platform: str
    contest_code: str
    problem_code: str
    problem_link: str
    difficulty: Optional[str] = None
    tags: List[str] = None
    created_date: Optional[datetime] = None

class CPDojoConfig:
    PLATFORMS = ["AtCoder", "CodeChef", "Codeforces", "Leetcode"]
    LANGUAGES = {
        "C++": ".cpp",
        "Python": ".py",
        "Java": ".java",
        "JavaScript": ".js",
        "Go": ".go",
        "Kotlin": ".kt",
        "Rust": ".rs",
    }
    
    PLATFORM_REGEX = {
        "Codeforces": r"/problemset/problem/(\d+)/([A-Za-z0-9]+)",
        "Leetcode": r"/problems/([a-z0-9-]+)/",
        "CodeChef": r"/([A-Z0-9]+)/problems/([A-Z0-9]+)",
        "AtCoder": r"/contests/([a-z0-9]+)/tasks/([a-z0-9_]+)"
    }
    
    BASE_DIR = Path("My-CP-Dojo")
    LOG_FILE = BASE_DIR / "cp_dojo.log"

class CPDojoTemplate:
    @staticmethod
    def get_language_template(language: str, problem_info: ProblemInfo) -> str:
        templates = {
            "Python": f"""# Problem: {problem_info.problem_code}
# Platform: {problem_info.platform}
# Link: {problem_info.problem_link}
# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

def solve():
    # TODO: Implement your solution here
    pass

def main():
    # Read input
    T = int(input())  # Number of test cases
    for _ in range(T):
        # Process each test case
        solve()

if __name__ == "__main__":
    main()
""",
            "C++": f"""// Problem: {problem_info.problem_code}
// Platform: {problem_info.platform}
// Link: {problem_info.problem_link}
// Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

#include <bits/stdc++.h>
using namespace std;

void solve() {{
    // TODO: Implement your solution here
}}

int main() {{
    ios::sync_with_stdio(0);
    cin.tie(0);
    
    int t;
    cin >> t;
    while(t--) {{
        solve();
    }}
    return 0;
}}
""",
            # Add templates for other languages...
        }
        return templates.get(language, f"// Problem: {problem_info.problem_code}\n// Link: {problem_info.problem_link}\n")

class CPDojoTool:
    def __init__(self):
        self._setup_logging()
        self._ensure_base_directory()
        self._setup_database()

    def _setup_logging(self):
        logging.basicConfig(
            filename=CPDojoConfig.LOG_FILE,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('CPDojo')

    def _ensure_base_directory(self):
        CPDojoConfig.BASE_DIR.mkdir(exist_ok=True)

    def _setup_database(self):
        db_path = CPDojoConfig.BASE_DIR / "problems.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS problems (
                    id INTEGER PRIMARY KEY,
                    platform TEXT,
                    contest_code TEXT,
                    problem_code TEXT,
                    problem_link TEXT,
                    difficulty TEXT,
                    tags TEXT,
                    created_date TIMESTAMP,
                    status TEXT DEFAULT 'PENDING'
                )
            """)

    @staticmethod
    def clear_screen():
        os.system('cls' if os.name == 'nt' else 'clear')

    def get_user_choice(self, prompt: str, choices: list) -> str:
        self.clear_screen()
        print(prompt)
        for i, choice in enumerate(choices, 1):
            print(f"{i}. {choice}")
            
        while True:
            try:
                choice = int(input("Enter the number of your choice: "))
                if 1 <= choice <= len(choices):
                    return choices[choice - 1]
                print("Invalid choice. Please select a valid number.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def extract_codes_from_link(self, link: str, platform: str) -> Tuple[str, str]:
        if platform not in CPDojoConfig.PLATFORM_REGEX:
            self.logger.error(f"Unsupported platform: {platform}")
            return "unknown", "unknown"
            
        match = re.search(CPDojoConfig.PLATFORM_REGEX[platform], link)
        if not match:
            self.logger.error(f"Could not extract codes from link: {link}")
            return "unknown", "unknown"
            
        if platform == "Leetcode":
            return "leetcode", match.group(1).replace("-", "_")
        return match.group(1), match.group(2)

    def update_daily_log(self, problem_info: ProblemInfo):
        log_path = CPDojoConfig.BASE_DIR / "daily_log.md"
        date_str = datetime.now().strftime("%Y-%m-%d|%H:%M:%S")
        
        log_entry = (
            f"### {date_str}\n"
            f"- **Platform**: {problem_info.platform}\n"
            f"- **Contest Code**: {problem_info.contest_code}\n"
            f"- **Problem Code**: {problem_info.problem_code}\n"
            f"- [Problem Link]({problem_info.problem_link})\n"
            f"- **Tags**: {', '.join(problem_info.tags) if problem_info.tags else 'None'}\n"
            f"- **Difficulty**: {problem_info.difficulty or 'Not specified'}\n\n"
        )
        
        with open(log_path, "a") as log_file:
            log_file.write(log_entry)
        
        self.logger.info(f"Daily log updated with {problem_info.problem_code}")

    def create_problem_directories(self, problem_info: ProblemInfo, language: str) -> Dict[str, Path]:
        dirs = {
            'solutions': CPDojoConfig.BASE_DIR / "Solutions" / problem_info.platform,
            'questions': CPDojoConfig.BASE_DIR / "Practiced-Problems" / problem_info.platform / "Questions",
            'thought_process': CPDojoConfig.BASE_DIR / "Practiced-Problems" / problem_info.platform / "Thought-Process"
        }
        
        for dir_path in dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
            
        return dirs

    def create_problem_files(self, problem_info: ProblemInfo, language: str, directories: Dict[str, Path]):
        # Solution file with template
        solution_file = directories['solutions'] / f"solution-{problem_info.contest_code}_{problem_info.problem_code}{CPDojoConfig.LANGUAGES[language]}"
        solution_file.write_text(CPDojoTemplate.get_language_template(language, problem_info))
        
        # Question link file
        question_file = directories['questions'] / f"{problem_info.contest_code}_{problem_info.problem_code}.txt"
        question_file.write_text(problem_info.problem_link)
        
        # Thought process template
        thought_file = directories['thought_process'] / f"{problem_info.contest_code}_{problem_info.problem_code}.md"
        thought_template = f"""# Problem Analysis: {problem_info.problem_code}

## Problem Link
{problem_info.problem_link}

## Initial Thoughts
- What are the key constraints?
- What's the input size?
- Any edge cases to consider?

## Approach
1. First approach considerations
   - Time complexity:
   - Space complexity:

## Implementation Details
- Key data structures used:
- Important algorithms/techniques:

## Learning Points
- What did you learn from this problem?
- Any particular tricks or patterns worth remembering?

## Similar Problems
- List similar problems you've solved
"""
        thought_file.write_text(thought_template)
        
        self.logger.info(f"Created files for problem {problem_info.problem_code}")

    def open_vscode(self, directory: Path):
        try:
            subprocess.run(["code", str(directory)], check=True)
            self.logger.info(f"Opened VSCode in {directory}")
        except subprocess.CalledProcessError:
            self.logger.error("Failed to open VSCode")
            print("Error: Could not open VSCode. Please make sure it's installed and 'code' command is available.")

    def store_problem_info(self, problem_info: ProblemInfo):
        db_path = CPDojoConfig.BASE_DIR / "problems.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                INSERT INTO problems 
                (platform, contest_code, problem_code, problem_link, difficulty, tags, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                problem_info.platform,
                problem_info.contest_code,
                problem_info.problem_code,
                problem_info.problem_link,
                problem_info.difficulty,
                json.dumps(problem_info.tags),
                datetime.now().isoformat()
            ))

    def run(self):
        self.clear_screen()
        print("Welcome to My-CP-Dojo CLI Tool!")
        
        platform = self.get_user_choice("Select the platform you're using:", CPDojoConfig.PLATFORMS)
        language = self.get_user_choice("Select the language you're using:", list(CPDojoConfig.LANGUAGES.keys()))
        problem_link = input("Paste the problem link: ").strip()
        
        contest_code, problem_code = self.extract_codes_from_link(problem_link, platform)
        if contest_code == "unknown":
            print("Could not extract contest and problem codes. Exiting...")
            return

        # Optional metadata
        difficulty = input("Enter problem difficulty (optional): ").strip() or None
        tags = input("Enter problem tags (comma-separated, optional): ").strip()
        tags = [tag.strip() for tag in tags.split(",")] if tags else []
        
        problem_info = ProblemInfo(
            platform=platform,
            contest_code=contest_code,
            problem_code=problem_code,
            problem_link=problem_link,
            difficulty=difficulty,
            tags=tags,
            created_date=datetime.now()
        )
        
        directories = self.create_problem_directories(problem_info, language)
        self.create_problem_files(problem_info, language, directories)
        self.update_daily_log(problem_info)
        self.store_problem_info(problem_info)
        self.open_vscode(directories['solutions'])
        
        print(f"\nSetup complete! Files created in {directories['solutions']}")
        print("\nCreated files:")
        print(f"1. Solution template: solution-{problem_code}{CPDojoConfig.LANGUAGES[language]}")
        print(f"2. Problem link: {problem_code}.txt")
        print(f"3. Thought process template: {problem_code}.md")
        print("\nYou can now start solving the problem in VSCode!")

if __name__ == "__main__":
    tool = CPDojoTool()
    tool.run()