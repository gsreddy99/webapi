import os
import glob
import openai

# Load Azure OpenAI configuration from environment variables
endpoint = os.getenv("AOAI_ENDPOINT")
api_key = os.getenv("AOAI_KEY")
deployment = os.getenv("AOAI_DEPLOYMENT")

# Azure OpenAI client configuration
openai.api_type = "azure"
openai.api_base = endpoint
openai.api_key = api_key
openai.api_version = "2024-02-01"

def read_files(patterns):
    """Reads all files matching the given glob patterns."""
    content = ""
    for pattern in patterns:
        for file in glob.glob(pattern):
            try:
                with open(file, "r") as f:
                    content += f"\n\n===== FILE: {file} =====\n"
                    content += f.read()
            except Exception as e:
                content += f"\n\n===== FILE: {file} (ERROR READING FILE: {e}) =====\n"
    return content

# Files to review
files_to_review = [
    "calculator-api/k8s/*.yaml",
    "calculator-api/docker/Dockerfile",
    ".github/workflows/*.yml"
]

content = read_files(files_to_review)

prompt = f"""
You are an expert DevOps reviewer.

Review the following configuration files for:
- Kubernetes best practices
- AKS-specific issues
- Security misconfigurations
- YAML schema issues
- Dockerfile optimization
- GitHub Actions workflow improvements

Provide a clear, structured report with:
1. Summary
2. Issues found
3. Severity (High / Medium / Low)
4. Recommended fixes
5. Best practice suggestions

Files:
{content}
"""

response = openai.ChatCompletion.create(
    engine=deployment,
    messages=[{"role": "user", "content": prompt}],
    max_tokens=2000,
    temperature=0.2
)

print("\n\n===== AI REVIEW REPORT =====\n")
print(response["choices"][0]["message"]["content"])
print("\n===== END OF REPORT =====\n")