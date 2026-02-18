import os
import glob
from openai import AzureOpenAI

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=os.environ["AOAI_KEY"],
    azure_endpoint=os.environ["AOAI_ENDPOINT"],
    api_version="2024-12-01-preview"
)

deployment = os.environ["AOAI_DEPLOYMENT"]  # "o4-mini"

# Files you want to review
FILES_TO_REVIEW = [
    "Dockerfile",
    "*.yml",
    "*.yaml",
    "*.json",
    "*.py"
]

def read_files():
    contents = []
    for pattern in FILES_TO_REVIEW:
        for file in glob.glob(pattern, recursive=True):
            try:
                with open(file, "r") as f:
                    contents.append(f"\n\n===== FILE: {file} =====\n{f.read()}")
            except Exception as e:
                contents.append(f"\n\n===== FILE: {file} (ERROR READING) =====\n{e}")
    return "\n".join(contents)

def run_review():
    files_text = read_files()

    prompt = f"""
You are an expert DevOps and cloud reviewer.
Review the following project files and provide:

1. Kubernetes issues
2. Dockerfile issues
3. GitHub Actions issues
4. Security risks
5. Best practices
6. Fix suggestions

Be concise but clear.

FILES:
{files_text}
"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "You are an expert DevOps reviewer."},
            {"role": "user", "content": prompt}
        ]
    )

    print("\n\n===== AI REVIEW OUTPUT =====\n")
    print(response.choices[0].message["content"])
    print("\n===== END OF REVIEW =====\n")

if __name__ == "__main__":
    run_review()
