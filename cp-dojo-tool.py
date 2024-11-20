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
        "Codeforces": {
            "pattern": r"codeforces\.com/(?:contest|group|problemset/problem)/([^/]+)/(?:problem/)?([A-Za-z0-9]+)",
            "extract": lambda match: (match.group(1), match.group(2))  # Returns (contest_id/problem_number, problem_code)
        },
        "Leetcode": {
            "pattern": r"leetcode\.com/(?:problems|contest)/([a-zA-Z0-9-]+)(?:/problems/([a-zA-Z0-9-]+))?",
            "extract": lambda match: ("leetcode", match.group(2) if match.group(2) else match.group(1))
        },
        "CodeChef": {
            "pattern": r"codechef\.com/(?:[^/]+/)?(?:problems/)?([A-Z0-9]+)",
            "extract": lambda match: ("codechef", match.group(1))
        },
        "AtCoder": {
            "pattern": r"atcoder\.jp/contests/([^/]+)/tasks/([^/]+)",
            "extract": lambda match: (match.group(1), match.group(2).split('_')[-1])
        }
    }
    
    BASE_DIR = Path("My-CP-Dojo")
    LOG_FILE = BASE_DIR / "cp_dojo.log"

class CPDojoTemplate:
    @staticmethod
    def generate_metadata_comment(problem_info: ProblemInfo, language: str) -> str:
        tags = ", ".join(problem_info.tags) if problem_info.tags else "None"
        created_date = problem_info.created_date.strftime('%Y-%m-%d %H:%M:%S') if problem_info.created_date else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        comment_styles = {
            "Python": {
                "start": "# ",
                "multi_start": "'''",
                "multi_end": "'''"
            },
            "C++": {
                "start": "// ",
                "multi_start": "/*",
                "multi_end": "*/"
            },
            "Java": {
                "start": "// ",
                "multi_start": "/*",
                "multi_end": "*/"
            },
            "JavaScript": {
                "start": "// ",
                "multi_start": "/*",
                "multi_end": "*/"
            },
            "Go": {
                "start": "// ",
                "multi_start": "/*",
                "multi_end": "*/"
            },
            "Kotlin": {
                "start": "// ",
                "multi_start": "/*",
                "multi_end": "*/"
            },
            "Rust": {
                "start": "// ",
                "multi_start": "/*",
                "multi_end": "*/"
            }
        }

        style = comment_styles.get(language, comment_styles["Python"])
        
        return f"""{style['multi_start']}
Problem Code: {problem_info.problem_code}
Platform: {problem_info.platform}
Contest Code: {problem_info.contest_code}
Link: {problem_info.problem_link}
Difficulty: {problem_info.difficulty or 'Unknown'}
Tags: {tags}
Created: {created_date}
{style['multi_end']}
"""

    @staticmethod
    def get_language_template(language: str, problem_info: ProblemInfo) -> str:
        metadata = CPDojoTemplate.generate_metadata_comment(problem_info, language)
        templates = {
            "Python": f"""{metadata}

def solve():
    # TODO: Implement your solution here
    pass

def main():
    # Read input
    T = int(input())  # Number of test cases
    for _ in range(T):
        solve()

if __name__ == "__main__":
    main()""",
            
            "C++": f"""{metadata}
#include <bits/stdc++.h>
using namespace std;

void solve() {{
    // TODO: Implement your solution here
}}

int main() {{
    ios::sync_with_stdio(0);
    cin.tie(0);
    
    int T;
    cin >> T;
    while(T--) {{
        solve();
    }}
    return 0;
}}"""
            # Add other language templates as needed
        }
        return templates.get(language, "")

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
        platform_info = CPDojoConfig.PLATFORM_REGEX.get(platform)
        if not platform_info:
            raise ValueError(f"Unsupported platform: {platform}")
        
        match = re.search(platform_info["pattern"], link)
        if not match:
            raise ValueError(f"Could not extract codes from link: {link}")
        
        return platform_info["extract"](match)

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

    @staticmethod
    def generate_filename(problem_info: ProblemInfo, language: str, file_type: str = "solution") -> str:
        """Generate consistent filename for different file types."""
        platform_id = problem_info.platform.lower()
        contest_id = problem_info.contest_code.lower()
        problem_id = problem_info.problem_code
        
        if file_type == "solution":
            return f"{platform_id}_{contest_id}_{problem_id}{CPDojoConfig.LANGUAGES[language]}"
        elif file_type == "thought":
            return f"{platform_id}_{contest_id}_{problem_id}.md"
        elif file_type == "link":
            return f"{platform_id}_{contest_id}_{problem_id}.txt"
        
        raise ValueError(f"Unknown file type: {file_type}")

    def create_problem_files(self, problem_info: ProblemInfo, language: str, directories: Dict[str, Path]):
        # Generate solution file
        solution_filename = self.generate_filename(problem_info, language, "solution")
        solution_file = directories['solutions'] / solution_filename
        solution_template = CPDojoTemplate.get_language_template(language, problem_info)
        solution_file.write_text(solution_template)

        # Generate link file
        link_filename = self.generate_filename(problem_info, language, "link")
        link_file = directories['solutions'] / link_filename
        link_file.write_text(problem_info.problem_link)

        # Generate thought process file
        thought_filename = self.generate_filename(problem_info, language, "thought")
        thought_file = directories['thought_process'] / thought_filename
        thought_template = self._get_thought_template(problem_info)
        thought_file.write_text(thought_template)

        return solution_filename, link_filename, thought_filename

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

    def _get_thought_template(self, problem_info: ProblemInfo) -> str:
        """Generate template for documenting thought process."""
        return f"""# {problem_info.platform} - Problem {problem_info.problem_code}

## Problem Link
{problem_info.problem_link}

## Initial Thoughts
- [ ] First approach
- [ ] Edge cases to consider
- [ ] Possible optimizations

## Approach
1. Describe your approach here

## Complexity Analysis
- Time Complexity: 
- Space Complexity: 

## Key Learnings
- What did you learn from this problem?
- Any specific techniques or patterns used?

## Tags
{', '.join(problem_info.tags) if problem_info.tags else 'None'}
"""

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
        difficulty = input("Enter problem difficulty (optional): ").strip()
        tags_input = input("Enter problem tags (comma-separated, optional): ").strip()
        tags = [tag.strip() for tag in tags_input.split(',')] if tags_input else []

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
        solution_file, link_file, thought_file = self.create_problem_files(problem_info, language, directories)
        self.update_daily_log(problem_info)
        self.store_problem_info(problem_info)
        self.open_vscode(directories['solutions'])
        
        print(f"\nSetup complete! Files created in {directories['solutions']}")
        print("\nCreated files:")
        print(f"1. Solution template: {solution_file}")
        print(f"2. Problem link: {link_file}")
        print(f"3. Thought process: {thought_file}")
        print("\nYou can now start solving the problem in VSCode!")

if __name__ == "__main__":
    tool = CPDojoTool()
    tool.run()