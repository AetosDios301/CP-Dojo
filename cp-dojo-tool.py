import os
import subprocess
import re
from datetime import datetime
from typing import Optional, Tuple, Dict
from dataclasses import dataclass
import logging
from pathlib import Path

@dataclass
class ProblemInfo:
    platform: str
    contest_code: str
    problem_code: str
    problem_link: str

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

class CPDojoTool:
    def __init__(self):
        self._setup_logging()
        self._ensure_base_directory()
    
    def _setup_logging(self):
        logging.basicConfig(
            filename=CPDojoConfig.LOG_FILE,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('CPDojo')
    
    def _ensure_base_directory(self):
        CPDojoConfig.BASE_DIR.mkdir(exist_ok=True)
        
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
            f"- [Problem Link]({problem_info.problem_link})\n\n"
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
        # Solution file
        solution_file = directories['solutions'] / f"solution-{problem_info.contest_code}_{problem_info.problem_code}{CPDojoConfig.LANGUAGES[language]}"
        solution_file.write_text("// Your solution code goes here\n")
        
        # Question link file
        question_file = directories['questions'] / f"{problem_info.contest_code}_{problem_info.problem_code}.txt"
        question_file.write_text(problem_info.problem_link)
        
        # Thought process file
        thought_file = directories['thought_process'] / f"{problem_info.contest_code}_{problem_info.problem_code}.md"
        thought_file.write_text("# Thought Process\n\nDescribe your approach and reasoning here.")
        
        self.logger.info(f"Created files for problem {problem_info.problem_code}")
        
    def open_vscode(self, directory: Path):
        try:
            subprocess.run(["code", str(directory)], check=True)
            self.logger.info(f"Opened VSCode in {directory}")
        except subprocess.CalledProcessError:
            self.logger.error("Failed to open VSCode")
            print("Error: Could not open VSCode. Please make sure it's installed and 'code' command is available.")
    
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
            
        problem_info = ProblemInfo(platform, contest_code, problem_code, problem_link)
        directories = self.create_problem_directories(problem_info, language)
        
        self.create_problem_files(problem_info, language, directories)
        self.update_daily_log(problem_info)
        self.open_vscode(directories['solutions'])
        
        print(f"Files created and VSCode opened in {directories['solutions']}")

if __name__ == "__main__":
    tool = CPDojoTool()
    tool.run()