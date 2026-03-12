import os
import sys
import json
import subprocess
import requests
from pathlib import Path
from openai import AzureOpenAI

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
            results[name] = {"url": url, "error": str(e)}

    return json.dumps(results, indent=2)


# -----------------------------
# Validate diff syntax
# -----------------------------
def is_valid_diff(diff):
    for line in diff.splitlines():
        if line.startswith("@@"):
            # Must match @@ -a,b +c,d @@
            if not ("@@" in line and "-" in line and "+" in line and "," in line):
                return False
            if any(word.isalpha() for word in line):
                return False
    return True


# -----------------------------
# Extract diff from LLM output
# -----------------------------
def extract_diff(output):
    if "```diff" not in output:
        return None
    diff = output.split("```diff")[1].split("```")[0].strip()
    return diff


# -----------------------------
# Apply patch
# -----------------------------
def apply_patch(diff):
    with open("ai_patch.diff", "w") as f:
        f.write(diff)

    try:
        subprocess.run(["git", "apply", "ai_patch.diff"], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


# -----------------------------
# Create fix-ai branch
# -----------------------------
def create_fix_branch():
    subprocess.run(["git", "checkout", "-b", "fix-ai"], check=False)
    subprocess.run(["git", "add", "."], check=False)
    subprocess.run(["git", "commit", "-m", "AI auto-fix"], check=False)
    subprocess.run(["git", "push", "-u", "origin", "fix-ai"], check=False)


# -----------------------------
# Ask LLM for a corrected diff
# -----------------------------
def regenerate_diff(bad_diff):
    prompt = f"""
The previous diff was invalid. Produce ONLY a valid unified diff.

Rules:
- NO English words in hunk headers.
- NO placeholders.
- ONLY valid unified diff format.
- Must apply cleanly with `git apply`.

Invalid diff:
{bad_diff}
"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": prompt}]
    )

    return extract_diff(response.choices[0].message.content)


# -----------------------------
# Main review
# -----------------------------
def run_review():
    files_text = read_files()
    live_api_results = test_endpoints()

    prompt = f"""
You are an expert API QA engineer.

Return:
1. PASS or FAIL
2. A valid unified diff patch (```diff) fixing all issues.
3. Diff MUST be valid and apply cleanly.
4. NO English words in hunk headers.

C# FILES:
{files_text}

LIVE API RESPONSES:
{live_api_results}
"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": prompt}]
    )

    output = response.choices[0].message.content
    print(output)

    diff = extract_diff(output)

    if not diff:
        print("No diff found. Failing.")
        sys.exit(1)

    if not is_valid_diff(diff):
        print("Invalid diff detected. Regenerating...")
        diff = regenerate_diff(diff)

    if not diff or not is_valid_diff(diff):
        print("Still invalid. Failing.")
        sys.exit(1)

    if apply_patch(diff):
        print("Patch applied.")
        create_fix_branch()
    else:
        print("Patch failed to apply.")
        sys.exit(1)

    if "FAIL" in output.upper():
        sys.exit(1)


if __name__ == "__main__":
    run_review()
