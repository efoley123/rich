import subprocess
import requests
import os
import sys
import logging
import json
from pathlib import Path
from requests.exceptions import RequestException
from typing import List, Optional, Dict, Any
import re

# Set up logging
logging.basicConfig(
 level=logging.INFO,
 format='%(asctime)s - %(levelname)s - %(message)s'
)

class TestGenerator:
 def __init__(self):
     self.api_key = os.getenv('OPENAI_API_KEY')
     self.model = os.getenv('OPENAI_MODEL', 'o1-preview')
     
     try:
         self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
     except ValueError:
         logging.error("Invalid value for OPENAI_MAX_TOKENS. Using default value: 2000")
         self.max_tokens = 2000

     if not self.api_key:
         raise ValueError("OPENAI_API_KEY environment variable is not set")

 def get_changed_files(self) -> List[str]:
     """Retrieve list of changed files passed as command-line arguments."""
     if len(sys.argv) <= 1:
         return []
     return [f.strip() for f in sys.argv[1].split() if f.strip()]

 def detect_language(self, file_name: str) -> str:
     """Detect programming language based on file extension."""
     extensions = {
         '.py': 'Python',
         '.js': 'JavaScript',
         '.ts': 'TypeScript',
         '.java': 'Java',
         '.cpp':'C++',
         '.cs': 'C#',
         '.go':'Go'
     }
     _, ext = os.path.splitext(file_name)
     return extensions.get(ext.lower(), 'Unknown')

 def get_test_framework(self, language: str) -> str:
     """Get the appropriate test framework based on language."""
     frameworks = {
         'Python': 'pytest',
         'JavaScript': 'jest',
         'TypeScript': 'jest',
         'Java': 'JUnit',
         'C++': 'Google Test',
         'C#': 'NUnit',
         'Go':'testing'
     }
     return frameworks.get(language, 'unknown')
 
 def get_related_files(self, language: str, file_name: str) -> List[str]:
    """Identify related files based on import statements or includes."""
    related_files = []
    file_directory = Path(file_name).parent  # Get the directory of the current file for relative paths

    try:
        if language in {"Python", "JavaScript", "TypeScript"}:
            with open(file_name, 'r') as f:
                for line in f:
                    if 'import ' in line or 'from ' in line or 'require(' in line:
                        parts = line.split()
                        
                        # Detects relative imports like `from .file_name import ...`
                        if 'from' in parts:
                            index = parts.index('from')
                            module_path = parts[index + 1]
                            if module_path.startswith("."):  # Handles relative import
                                relative_path = module_path.replace(".", "").replace("_", "").replace(".", "/")
                                for ext in ('.py', '.js', '.ts'):
                                    potential_file = file_directory / f"{relative_path}{ext}"
                                    if potential_file.exists():
                                        related_files.append(str(potential_file))
                                        break
                        
                        for part in parts:
                            # Check for relative imports with single dot, without `from`
                            if len(part) > 1 and part[0] == "." and part[1] != ".":
                                path = part.replace(".", "").replace("_", "").replace(".", "/")
                                for ext in ('.py', '.js', '.ts'):
                                    potential_file = file_directory / f"{path}{ext}"
                                    if potential_file.exists():
                                        related_files.append(str(potential_file))
                                        break
                            elif '.' in part:
                                path = part.replace(".", "/")
                                for ext in ('.py', '.js', '.ts'):
                                    potential_file = f"{path}{ext}"
                                    if Path(potential_file).exists():
                                        related_files.append(str(potential_file))
                                        break
                            else:
                                if part.endswith(('.py', '.js', '.ts')) and Path(part).exists():
                                    related_files.append(part)
                                elif part.isidentifier():  # Valid class/module names
                                    base_name = part.lower()
                                    for ext in ('.py', '.js', '.ts'):
                                        potential_file = f"{base_name}{ext}"
                                        if Path(potential_file).exists():
                                            related_files.append(potential_file)
                                            break
                        
        elif language == 'C++':
            return []  # Placeholder for C++ support
        elif language == 'C#':
            return []  # Placeholder for C# support

    except Exception as e:
        logging.error(f"Error identifying related files in {file_name}: {e}")

    return related_files

 def get_related_test_files(self, language: str, file_name: str) -> List[str]:
      related_test_files = []#Identify related files based on import statements or includes.
      #print("ENTERED TEST RELATED FILES\n\n")
      try:
          if (language=="Python"):
              directory = Path(os.path.dirname(os.path.abspath(__file__)))
              #need to look at the directory for python test files
              #print("this is the directory"+str(directory)+"\n")
              #just going to look in current directory
              test_files =  list(directory.rglob("tests.py")) + list(directory.rglob("test.py")) + list(directory.rglob("test_*.py")) + list(directory.rglob("*_test.py"))
              #print("\n related TEST FILES HERE "+ ', '.join(str(file) for file in test_files) + "\n")
              #print("print statement above\n")
              for file in test_files:
                  with open(file, 'r') as f:
                      for line in f:
                          if 'from ' in line:
                              #going to now check each word in the line
                              parts = line.split()
                              for part in parts:
                                  for part in parts:
                                      # Check for file extensions
                                      if len(part) > 1 and part[0]=="." and part[1] != ".":
                                          path = part.replace(".","")
                                          for ext in ('.py', '.js', '.ts'):
                                              potential_file = f"{path}{ext}"
                                              stringPotentialFile = str(potential_file)
                                              #print("result of "+ str(file_name) +" in "+ stringPotentialFile +"  is this "+ str(stringPotentialFile in str(file_name))+ "")
                                              #print(str(Path(potential_file).exists()) + "<-- this is saying whether it exsists and this is potential_file "+str(potential_file)+"\n")
                                              if (Path(file_name).exists() and (stringPotentialFile in str(file_name))):
                                                  related_test_files.append(str(file))
                                                  break  #
                                      elif '.' in part:
                                          path = part.replace(".","/")
                                          for ext in ('.py', '.js', '.ts'):
                                              potential_file = f"{path}{ext}"
                                          #print(potential_file + "<-- from . \n")
                                              stringPotentialFile = str(potential_file)
                                              if Path(file_name).exists() and (stringPotentialFile in str(file_name)):
                                                  related_test_files.append(str(file))
                                                  break  #
                                      else:
                                          if part.endswith(('.py', '.js', '.ts')) and Path(part).exists() and ((str(file_name)) in str(part)):
                                              related_test_files.append(str(file))
                                          # Check for class/module names without extensions
                                          elif part.isidentifier():  # Checks if part is a valid identifier
                                          # Construct potential file names
                                              base_name = part.lower()  # Assuming file names are in lowercase
                                              for ext in ('.py', '.js', '.ts','.js'):
                                                  potential_file = f"{base_name}{ext}"
                                                  #print(potential_file + "<-- from regular \n")
                                                  stringPotentialFile = str(potential_file)
                                                  if Path(file_name).exists() and (stringPotentialFile in str(file_name)):
                                                      related_test_files.append(file)
                                                      break  # Found a related file, no need to check further extensions
      except Exception as e:
          logging.error(f"Error identifying related test files in {file_name}: {e}")
     #print("related FILES HERE "+ ', '.join(related_files) + "\n")
      limited_test_files = related_test_files[:1]# List
      return limited_test_files  # List
 
 def all_test_files_before(self, language: str, file_name: str) -> str:
     #run coverage run
     #know if there is an ini file probably won't work
     #if it generates an error don't pass it in
     #.....
     #if the file is 100% coverage probably don't want test cases for it
    coverageRunResult = ""
    file_name_path= Path(file_name)
    report_file = f"{file_name_path.stem}_coverage_report.txt" #make a file temporarily
    try:
        if (language=='Python'):
            #python
            subprocess.run(["coverage","run","-m","pytest"])
            #subprocess.run(["coverage","report", "-m"],stdout=coverageRunResult,check=True)
            subprocess.run(["coverage","report", "-m"],stdout=open(report_file, "a"),check=True)
            with open(report_file, "r") as file:
                coverageRunResult = file.read()
            os.remove(report_file) # deleting it now



            # Find the line that starts with "calculator.py"
            match = re.search(r"^"+file_name_path.stem+"\.py\s+.*", coverageRunResult, re.MULTILINE)

            # Extract the matched line
            if match:
                calculator_line = match.group(0)
                coverageRunResult = calculator_line
                match = re.search(r"%\s+(.*)", calculator_line)
                coverageRunResult = match.group(0)
                print(calculator_line)

            else:
                print("Line for 'calculator.py' not found.")

                
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Error generating the all test files coverage report for {file_name}: {e}")
    if (coverageRunResult==""):
        coverageRunResult = "The coverageReportDidNotHappen"
    elif ("Error" in coverageRunResult or "error" in coverageRunResult):
        coverageRunResult = "There was an error somewhere in the result"
    return coverageRunResult
    

 def generate_coverage_beforehand(self, test_file:Path, file_name:str, language: str):
       if (language=="Python"):
            try:
                report_file = test_file.parent / f"{test_file.stem}_coverage_report.txt"
                subprocess.run(["coverage","erase"])
                subprocess.run(["coverage","run","-m","pytest"])
                subprocess.run(["coverage","report", "-m"],stdout=open(report_file, "a"),check=True)
                #self.generate_coverage_report(file_name,test_file,language) #generating the coverage report

            except subprocess.CalledProcessError as e:
                logging.error(f"Error generating the before coverage report for {test_file}: {e}")
            logging.info("made the before test case generation  :" + str(test_file))
            
        
       
       
 
 def generate_coverage_report(self, file_name:str, test_file: Path, language: str):
       """Generate a code coverage report and save it as a text file."""
       report_file = test_file.parent / f"{test_file.stem}_coverage_report.txt"
       if language == "Python":
          # Get the full path of the base file and replace slashes with dots
          current_path = str(os.path.dirname(os.path.abspath(__file__)))  + "/"
          base_name = Path(file_name).resolve()

          base_name = str(base_name).replace(current_path,'').replace('/', '.')
          
          base_name = base_name.replace(file_name,"").replace(".py","") #if (base_name) should still have .
          if (base_name==""):
              base_name="."
       else:
          # For other languages, the base_name remains the stem of the file
          base_name = Path(file_name).stem

       try:
           # Run tests with coverage based on language
           if language == "Python":
               subprocess.run(
                   ["pytest", str(test_file), "--cov="+str(base_name), "--cov-report=term-missing"],
                   stdout=open(report_file, "a"),
                   check=True
               )
           elif language == "JavaScript":
               # Example for JavaScript - replace with the specific coverage tool and command
               subprocess.run(
                   ["jest", "--coverage", "--config=path/to/jest.config.js"],
                   stdout=open(report_file, "a"),
                   check=True
               )
           # Add additional commands for other languages here

           logging.info(f"Code coverage report saved to {report_file}")

       except subprocess.CalledProcessError as e:
           logging.error(f"Error generating coverage report for {test_file}: {e}")

 def ensure_coverage_installed(self, language: str):
       """
       Ensures that the appropriate coverage tool for the given programming language is installed.
       Logs messages for each step.
       """
       try:
           if language.lower() == 'python':
               # Check if 'coverage' is installed for Python
               subprocess.check_call([sys.executable, '-m','pip','install', 'coverage'])
               subprocess.check_call([sys.executable, '-m','pip','install', 'coverage','pytest'])#pip install coverage pytest
               subprocess.check_call([sys.executable, '-m','pip','install', 'pytest-cov'])
               subprocess.check_call([sys.executable, '-m','coverage','erase'])#coverage erase
               logging.info(f"Coverage tool for Python is already installed.")
           elif language.lower() == 'javascript':
               # Check if 'jest' coverage is available for JavaScript
               subprocess.check_call(['npm', 'list', 'jest'])
               logging.info(f"Coverage tool for JavaScript (jest) is already installed.")
           elif language.lower() == 'java':
               # Check if 'jacoco' is available for Java (typically part of the build process)
               logging.info("Make sure Jacoco is configured in your Maven/Gradle build.")
               # Optionally you can add a check for specific build tool (Maven/Gradle) commands here
           elif language.lower() == 'ruby':
               # Check if 'simplecov' is installed for Ruby
               subprocess.check_call(['gem', 'list', 'simplecov'])
               logging.info(f"Coverage tool for Ruby (simplecov) is already installed.")
           else:
               logging.warning(f"Coverage tool check is not configured for {language}. Please add it manually.")
               return

       except subprocess.CalledProcessError:
           logging.error(f"Coverage tool for {language} is not installed. Installing...")

           try:
               if language.lower() == 'python':
                   subprocess.check_call([sys.executable, '-m','pip','install', 'pytest-cov'])
                   logging.info(f"Coverage tool for Python has been installed.")
               elif language.lower() == 'javascript':
                   subprocess.check_call(['npm', 'install', 'jest'])
                   logging.info(f"Coverage tool for JavaScript (jest) has been installed.")
               elif language.lower() == 'ruby':
                   subprocess.check_call(['gem', 'install', 'simplecov'])
                   logging.info(f"Coverage tool for Ruby (simplecov) has been installed.")
               else:
                   logging.error(f"Could not install coverage tool for {language} automatically. Please install manually.")
           except subprocess.CalledProcessError:
               logging.error(f"Failed to install the coverage tool for {language}. Please install it manually.")

     

 def create_prompt(self, file_name: str, language: str) -> Optional[str]:
      """Create a language-specific prompt for test generation with accurate module and import names in related content."""
      try:
          with open(file_name, 'r') as f:
              code_content = f.read()
      except Exception as e:
          logging.error(f"Error reading file {file_name}: {e}")
          return None

      # Gather related files and embed imports in each file's content
      related_files = self.get_related_files(language, file_name)
      related_content = ""

      # Log related files to confirm detection
      if related_files:
          logging.info(f"Related files for {file_name}: {related_files}")
      else:
          logging.info(f"No related files found for {file_name} to reference")
      for related_file in related_files:
          try:
              with open(related_file, 'r') as rf:
                  file_content = rf.read()
                  
                  # Generate the correct module path for import statements
                  module_path = str(Path(related_file).with_suffix('')).replace('/', '.')
                  import_statement = f"import {module_path}"
                  
                  # Append file content with embedded import statement
                  related_content += f"\n\n// Module: {module_path}\n{import_statement}\n{file_content}"
                  logging.info(f"Included content from related file: {related_file} as module {module_path}")
          except Exception as e:
              logging.error(f"Error reading related file {related_file}: {e}")

      # Gather additional context from related test files
      
      related_test_files = self.get_related_test_files(language, file_name)
      related_test_content = ""
      # Log related files to confirm detection
      if related_test_files:
          logging.info(f"Related Test files for {file_name}: {related_test_files}")
      else:
          logging.info(f"No related test files found for {file_name} to reference")
      for related_test_file in related_test_files:
          try:
              with open(related_test_file, 'r') as rf:
                  file_content = rf.read()
                  related_test_content += f"\n\n// Related test file: {related_test_file}\n{file_content}"
                  logging.info(f"Included content from related test file: {related_test_file}")
          except Exception as e:
              logging.error(f"Error reading related test file {related_test_file}: {e}")

      
      try:
        allCoverageReport = self.all_test_files_before(language,file_name)
      except Exception as e:
          logging.error(f"Error with doing the allCoverageReport:{e}")
          allCoverageReport = "Was not able to get the coverage of the file beforehand"
     
      logging.info("Processing all test files before :) ")

      # Add the file name at the top of the prompt
      framework = self.get_test_framework(language)
      prompt = f"""Generate comprehensive unit tests for the following {language} file: {file_name} using {framework}.

      Requirements:
      1. Include edge cases, normal cases, and error cases.
      2. Use mocking where appropriate for external dependencies.
      3. Include setup and teardown if needed.
      4. Add descriptive test names and docstrings.
      5. Follow {framework} best practices.
      6. Ensure high code coverage.
      7. Test both success and failure scenarios.

      Code to test (File: {file_name}):

      {code_content}

      Related context:

      {related_content}

      Related test cases:
      {related_test_content}

      Here are the uncovered lines in the file to make test cases for:
      {allCoverageReport.strip()}

      Generate only the test code without any explanations or notes."""

      logging.info(f"Created prompt for {file_name} with length {len(prompt)} characters")
      return prompt


 def call_openai_api(self, prompt: str) -> Optional[str]:
     """Call OpenAI API to generate test cases."""
     headers = {
         'Content-Type': 'application/json',
         'Authorization': f'Bearer {self.api_key}'
     }
     
     data = {
         'model': self.model,
         'messages': [
             {
                 "role": "system",
                 "content": "You are a senior software engineer specialized in writing comprehensive test suites."
             },
             {
                 "role": "user",
                 "content": prompt
             }
         ],
         'max_tokens': self.max_tokens,
         'temperature': 0.7
     }

     try:
         response = requests.post(
             'https://api.openai.com/v1/chat/completions',
             headers=headers,
             json=data,
             timeout=60
         )
         response.raise_for_status()
         generated_text = response.json()['choices'][0]['message']['content']
         normalized_text = generated_text.replace('“', '"').replace('”', '"').replace("‘", "'").replace("’", "'")
         if normalized_text.startswith('```'):
             first_newline_index = normalized_text.find('\n', 3)
             if first_newline_index != -1:
                 normalized_text = normalized_text[first_newline_index+1:]
             else:
                 normalized_text = normalized_text[3:]
             if normalized_text.endswith('```'):
                 normalized_text = normalized_text[:-3]
         return normalized_text.strip()
     except RequestException as e:
         logging.error(f"API request failed: {e}")
         return None
     
 def make_test_file(self, file_name: str, language: str) -> Path:
     """Save generated test cases to appropriate directory structure."""
     tests_dir = Path('generated_tests')
     tests_dir.mkdir(exist_ok=True)
     lang_dir = tests_dir / language.lower()
     lang_dir.mkdir(exist_ok=True)
     base_name = Path(file_name).stem
     if not base_name.startswith("test_"):
         base_name = f"test_{base_name}"
     extension = '.js' if language == 'JavaScript' else Path(file_name).suffix
     test_file = lang_dir / f"{base_name}{extension}"

     header = ""
     if language.lower() == 'python':
         logging.info("will write python specific header")
         header = (
               "import sys\n"
               "import os\n"
               "sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), \"../..\")))\n\n"
           )
     elif language.lower() == 'go':
         #add stuff for go
         logging.info("go unwritten code for save_test_cases")
   
     try:
         with open(test_file, 'w', encoding='utf-8') as f:
             f.write(header)
             logging.info("wrote header in test file")
             f.close
     except Exception as e:
         logging.error(f"Error adding header to {test_file}: {e}")
       
     return test_file
 
 def save_tests_created(self, test_file: Path,test_cases:str,language:str):
   
     try:
         with open(test_file, 'a', encoding='utf-8') as f:
             f.write(test_cases)
         logging.info(f"Test cases saved to {test_file}")
     except Exception as e:
         logging.error(f"Error saving test cases to {test_file}: {e}")

     if test_file.exists():
         logging.info(f"File {test_file} exists with size {test_file.stat().st_size} bytes.")
     else:
         logging.error(f"File {test_file} was not created.")
     return test_file

     

 def run(self):
     """Main execution method."""
     changed_files = self.get_changed_files()
     if not changed_files:
         logging.info("No files changed.")
         return

     for file_name in changed_files:
         if (file_name!="generate_tests.py"):
          try:
              language = self.detect_language(file_name)
              if language == 'Unknown':
                  logging.warning(f"Unsupported file type: {file_name}")
                  continue

              logging.info(f"Processing {file_name} ({language})")
              prompt = self.create_prompt(file_name, language)
              
              if prompt:
                  
                  #test_cases = self.call_openai_api(prompt)
                  #logging.info(prompt+ "\n\n\n")
                  logging.info("this is test_cases result"+ test_cases)
                  if test_cases:
                      test_cases = test_cases.replace("“", '"').replace("”", '"')

                      self.ensure_coverage_installed(language)

                      test_file_path = self.make_test_file(file_name,language)

                      self.generate_coverage_beforehand(test_file_path,file_name,language)
                      test_file = self.save_tests_created(test_file_path,test_cases, language)
                      self.generate_coverage_report(file_name, test_file, language)
                  else:
                      logging.error(f"Failed to generate test cases for {file_name}")
          except Exception as e:
              logging.error(f"Error processing {file_name}: {e}")

if __name__ == '__main__':
 try:
     generator = TestGenerator()
     generator.run()
 except Exception as e:
     logging.error(f"Fatal error: {e}")
     sys.exit(1)