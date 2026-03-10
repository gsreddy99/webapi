import os
from pathlib import Path
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=os.environ["AOAI_KEY"],
    azure_endpoint=os.environ["AOAI_ENDPOINT"],
    api_version="2024-12-01-preview"
)

deployment = os.environ["AOAI_DEPLOYMENT"]  # e.g., "o4-mini"

ROOT = Path(".")
PATTERNS = ["**/*.cs"]


def read_files():
    contents = []
    for pattern in PATTERNS:
        for path in ROOT.glob(pattern):
            if not path.is_file():
                continue
            try:
                text = path.read_text(errors="ignore")
                contents.append(f"\n\n===== FILE: {path} =====\n{text}")
            except Exception as e:
                contents.append(f"\n\n===== FILE: {path} (ERROR READING) =====\n{e}")
    return "\n".join(contents)


def run_review():
    files_text = read_files()

    prompt = f"""
You are an expert API QA engineer and senior .NET backend engineer.

Analyze ONLY the API controllers in the provided C# files and evaluate:

1. Route correctness and consistency
2. HTTP method correctness
3. Query parameter validation (types, required fields, defaults)
4. Error handling behavior (invalid input, divide-by-zero, missing params)
5. Response contract correctness (shape, fields, status codes)
6. REST semantics (idempotency, naming, resource structure)
7. Logging correctness and completeness
8. Missing edge cases or validation rules
9. Security considerations (input sanitization, error exposure)
10. Recommendations for improving API contract quality

AFTER the review, produce the following additional sections:

### CODE FIXES (MANDATORY)
Provide a unified diff patch (```diff) showing EXACT code changes needed to fix issues.

### REWRITTEN CONTROLLER (MANDATORY)
Provide a fully corrected and improved version of the controller code in C#.

### IMPROVED API CONTRACT (OPTIONAL)
If applicable, propose an improved API contract or OpenAPI snippet.

IMPORTANT:
- Base your analysis ONLY on the provided code.
- If something is missing (e.g., no OpenAPI spec), explicitly say: "Not found in provided files."

FILES:
{files_text}
"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "You are an expert API QA reviewer and senior backend engineer."},
            {"role": "user", "content": prompt}
        ]
    )

    print("\n\n===== API CONTRACT REVIEW OUTPUT =====\n")
    print(response.choices[0].message.content)
    print("\n===== END OF REVIEW =====\n")


if __name__ == "__main__":
    run_review()
