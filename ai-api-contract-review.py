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
# The ONLY file the AI is allowed to modify
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
def read_calc_controller():
    return TARGET_FILE.read_text(errors="ignore")


def extract_diff(output: str):
    """
    Extract diff block from AI response.
    """
    if "```diff" not in output:
        return None

    diff = output.split("```diff")[1].split("```")[0]
    return diff.strip()


def normalize_diff(diff: str):
    """
    Ensures the diff contains git headers required by git apply.
    """
    if not diff.startswith("diff --git"):
        header = f"""diff --git a/{FILE_PATH} b/{FILE_PATH}
--- a/{FILE_PATH}
+++ b/{FILE_PATH}
"""
        diff = header + diff

    return diff


def is_valid_diff(diff: str):
    """
    Strict validation to prevent malicious or malformed patches.
    """

    # Must contain exactly one diff header
    if diff.count("diff --git") != 1:
        print("Invalid: diff header missing.")
        return False

    # Only allowed file
    if FILE_PATH not in diff:
        print("Invalid: patch touches other files.")
        return False

    # Validate hunk headers
    for line in diff.splitlines():
        if line.startswith("@@"):
            if not re.match(r"^@@ -\d+(,\d+)? \+\d+(,\d+)? @@", line):
                print("Invalid hunk header:", line)
                return False

    return True


def apply_patch(diff: str):
    """
    Applies patch safely.
    """

    patch_file = "ai_patch.diff"

    with open(patch_file, "w") as f:
        f.write(diff)

    try:
        subprocess.run(
            ["git", "apply", "--whitespace=fix", patch_file],
            check=True
        )
        return True

    except subprocess.CalledProcessError as e:
        print("git apply failed.")
        subprocess.run(["git", "apply", "--stat", patch_file])
        return False


def create_fix_branch():
    """
    Commit and push AI fix branch.
    """

    subprocess.run(["git", "checkout", "-b", "fix-ai"], check=False)
    subprocess.run(["git", "add", FILE_PATH], check=False)

    subprocess.run(
        ["git", "commit", "-m", "AI auto-fix CalcController"],
        check=False
    )

    subprocess.run(
        ["git", "push", "-u", "origin", "fix-ai"],
        check=False
    )


# ---------------------------------------------------------
# Main Review Logic
# ---------------------------------------------------------
def run_review():
    controller_code = read_calc_controller()

    prompt = f"""
You are a senior .NET API engineer.

You will receive ONE file only.

File:
{FILE_PATH}

Your task:
Identify issues and produce a git patch fixing them.

CRITICAL RULES:

You MUST output a FULL git unified diff.

The patch MUST start exactly with:

diff --git a/{FILE_PATH} b/{FILE_PATH}
--- a/{FILE_PATH}
+++ b/{FILE_PATH}

Rules:
- Modify ONLY this file
- Exactly ONE diff
- No new files
- No renames
- No deletions
- Patch MUST apply with `git apply`
- Hunk headers must be numeric

Return ONLY the diff inside a ```diff block.

FILE CONTENT:
{controller_code}
"""

    response = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    output = response.choices[0].message.content

    print("\n===== AI OUTPUT =====\n")
    print(output)

    diff = extract_diff(output)

    if not diff:
        print("No diff found.")
        sys.exit(1)

    diff = normalize_diff(diff)

    if not is_valid_diff(diff):
        print("Diff validation failed.")
        sys.exit(1)

    if apply_patch(diff):
        print("Patch applied successfully.")
        create_fix_branch()
    else:
        print("Patch failed.")
        sys.exit(1)


# ---------------------------------------------------------
# Entry
# ---------------------------------------------------------
if __name__ == "__main__":
    run_review()