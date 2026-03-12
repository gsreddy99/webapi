import os
import sys
import subprocess
import re
from pathlib import Path
from openai import AzureOpenAI

# ---------------------------------------------------------
# Azure OpenAI Client
# ---------------------------------------------------------
client = AzureOpenAI(
    api_key=os.environ["AOAI_KEY"],
    azure_endpoint=os.environ["AOAI_ENDPOINT"],
    api_version="2024-12-01-preview"
)

deployment = os.environ["AOAI_DEPLOYMENT"]

# ---------------------------------------------------------
# Target file allowed for modification
# ---------------------------------------------------------
TARGET_FILE = (
    Path(__file__).parent
    / "calculator-api"
    / "src"
    / "Controllers"
    / "CalcController.cs"
).resolve()

FILE_PATH = "calculator-api/src/Controllers/CalcController.cs"

print("Loading controller from:", TARGET_FILE)
print("Exists:", TARGET_FILE.exists())

if not TARGET_FILE.exists():
    print("ERROR: CalcController.cs not found.")
    sys.exit(1)

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def read_file():
    return TARGET_FILE.read_text(errors="ignore")


def extract_diff(output):
    if "```diff" not in output:
        return None
    return output.split("```diff")[1].split("```")[0].strip()


def normalize_diff(diff):
    """
    Ensure git headers exist.
    """
    if not diff.startswith("diff --git"):
        header = f"""diff --git a/{FILE_PATH} b/{FILE_PATH}
--- a/{FILE_PATH}
+++ b/{FILE_PATH}
"""
        diff = header + diff

    return diff


def is_valid_diff(diff):

    if diff.count("diff --git") != 1:
        print("Invalid diff header")
        return False

    if FILE_PATH not in diff:
        print("Patch modifies unauthorized files")
        return False

    for line in diff.splitlines():
        if line.startswith("@@"):
            if not re.match(r"^@@ -\d+(,\d+)? \+\d+(,\d+)? @@", line):
                print("Invalid hunk header:", line)
                return False

    return True


def apply_patch(diff):

    patch_file = "ai_contract_patch.diff"

    with open(patch_file, "w") as f:
        f.write(diff)

    try:
        subprocess.run(
            ["git", "apply", "--whitespace=fix", patch_file],
            check=True
        )
        return True

    except subprocess.CalledProcessError:
        print("Patch failed to apply")
        subprocess.run(["git", "apply", "--stat", patch_file])
        return False


def commit_fix():

    subprocess.run(["git", "checkout", "-b", "fix-api-contract"], check=False)

    subprocess.run(["git", "add", FILE_PATH], check=False)

    subprocess.run(
        ["git", "commit", "-m", "AI API contract fix"],
        check=False
    )

    subprocess.run(
        ["git", "push", "-u", "origin", "fix-api-contract"],
        check=False
    )


# ---------------------------------------------------------
# Main Review Logic
# ---------------------------------------------------------

def run_review():

    code = read_file()

    prompt = f"""
You are a senior .NET API architect performing an API contract review.

File under review:
{FILE_PATH}

Your responsibilities:

Check for:
- invalid HTTP behavior
- missing validation
- unsafe API responses
- divide-by-zero cases
- incorrect status codes
- logging issues

You may ONLY modify this file.

CRITICAL OUTPUT RULES:

You MUST return a valid git unified diff.

Patch must begin with:

diff --git a/{FILE_PATH} b/{FILE_PATH}
--- a/{FILE_PATH}
+++ b/{FILE_PATH}

Rules:
- Modify ONLY this file
- Exactly ONE diff
- No explanations
- No additional text
- Output ONLY a ```diff block
- Patch must apply with `git apply`

FILE CONTENT:
{code}
"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "system",
                "content": "You are a senior .NET API engineer."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_completion_tokens=2000
    )

    output = response.choices[0].message.content

    print("\n===== AI OUTPUT =====\n")
    print(output)

    diff = extract_diff(output)

    if not diff:
        print("No diff returned by AI")
        sys.exit(1)

    diff = normalize_diff(diff)

    if not is_valid_diff(diff):
        print("Diff validation failed")
        sys.exit(1)

    if apply_patch(diff):
        print("Patch applied successfully")
        commit_fix()
    else:
        sys.exit(1)


# ---------------------------------------------------------
# Entry
# ---------------------------------------------------------

if __name__ == "__main__":
    run_review()