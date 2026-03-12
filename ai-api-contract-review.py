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
# Target file
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


def extract_diff(output: str):

    # Preferred format
    if "```diff" in output:
        return output.split("```diff")[1].split("```")[0].strip()

    # fallback if model skipped code block
    if "diff --git" in output:
        return output[output.index("diff --git"):].strip()

    return None


def normalize_diff(diff: str):

    if not diff.startswith("diff --git"):
        header = f"""diff --git a/{FILE_PATH} b/{FILE_PATH}
--- a/{FILE_PATH}
+++ b/{FILE_PATH}
"""
        diff = header + diff

    return diff


def is_valid_diff(diff: str):

    if diff.count("diff --git") != 1:
        print("Invalid diff header")
        return False

    if FILE_PATH not in diff:
        print("Patch attempts to modify unauthorized files")
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

Your job is to fix API contract problems such as:

- missing validation
- divide-by-zero risks
- incorrect HTTP responses
- unsafe error handling
- missing logging
- inconsistent API behavior

CRITICAL OUTPUT RULES

You MUST return ONLY a git patch.

Your entire response MUST be a single code block like:

```diff
diff --git a/{FILE_PATH} b/{FILE_PATH}
--- a/{FILE_PATH}
+++ b/{FILE_PATH}
@@ -line,line +line,line @@
PATCH