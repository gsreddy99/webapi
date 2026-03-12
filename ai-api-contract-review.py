import os
import sys
import json
import subprocess
import requests
from pathlib import Path
from openai import AzureOpenAI

# -----------------------------
# Azure OpenAI Client
# -----------------------------
client = AzureOpenAI(
    api_key=os.environ["AOAI_KEY"],
    azure_endpoint=os.environ["AOAI_ENDPOINT"],
    api_version="2024-12-01-preview"
)

deployment = os.environ["AOAI_DEPLOYMENT"]

ROOT = Path(".")
PATTERNS = ["**/*.cs"]
API_BASE = os.environ.get("API_BASE", "http://localhost:5196")


# -----------------------------
# Read all C# files
# -----------------------------
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


# -----------------------------
# Call API endpoints
# -----------------------------
def test_endpoints():
    results = {}

    endpoints = {
        "root": f"{API_BASE}/",
        "health": f"{API_BASE}/health",
        "test": f"{API_BASE}/api/test",
        "sales": f"{API_BASE}/api/sales/summary?date=2025-02-15",
        "calc": f"{API_BASE}/api/calc?a=10&b=5&op=add"
    }

    for name, url in endpoints.items():
        try:
            r = requests.get(url, timeout=5)
            results[name] = {
                "url": url,
                "status": r.status_code,
                "body": r.text
            }
        except Exception as e:
            results[name] = {
                "url": url,
                "error": str(e)
            }

    return json.dumps(results, indent=2)


# -----------------------------
# Apply diff patch to repo
# -----------------------------
def apply_patch(patch_text):
    patch_file = "ai_patch.diff"
    with open(patch_file, "w") as f:
        f.write(patch_text)

    try:
        subprocess.run(["git", "apply", patch_file], check=True)
        return True
    except subprocess.CalledProcessError:
        print("Patch failed to apply.")
        return False


# -----------------------------
# Create fix-ai branch + commit + push
# -----------------------------
def create_fix_branch():
    subprocess.run(["git", "checkout", "-b", "fix-ai"], check=False)
    subprocess.run(["git", "add", "."], check=False)
    subprocess.run(["git", "commit", "-m", "AI auto-fix from contract review"], check=False)
    subprocess.run(["git", "push", "-u", "origin", "fix-ai"], check=False)


# -----------------------------
# Main AI Contract Review
# -----------------------------
def run_review():
    files_text = read_files()
    live_api_results = test_endpoints()

    prompt = f"""
You are an expert API QA engineer and senior .NET backend engineer.

You will receive:
1. The C# controller code
2. Live API responses from the running service

Your tasks:

1. Validate API contract correctness.
2. Identify mismatches between code and live behavior.
3. Return PASS or FAIL.
4. Provide a unified diff patch (```diff) that fixes all issues.
5. Provide a rewritten controller if needed.

==========================
C# CONTROLLER FILES:
{files_text}

==========================
LIVE API RESPONSES:
{live_api_results}
"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "You are an expert API QA reviewer and senior backend engineer."},
            {"role": "user", "content": prompt}
        ]
    )

    output = response.choices[0].message.content

    print("\n===== AI CONTRACT REVIEW OUTPUT =====\n")
    print(output)
    print("\n===== END OF REVIEW =====\n")

    # Extract diff patch
    if "```diff" in output:
        patch = output.split("```diff")[1].split("```")[0].strip()
        print("\n===== APPLYING PATCH =====\n")
        if apply_patch(patch):
            print("Patch applied successfully.")
            create_fix_branch()
            print("fix-ai branch created and pushed.")
        else:
            print("Patch could not be applied.")
            sys.exit(1)

    # Fail CI if FAIL detected
    if "FAIL" in output.upper():
        sys.exit(1)


if __name__ == "__main__":
    run_review()
