import os
import sys
import subprocess
from pathlib import Path
from openai import AzureOpenAI

# Azure OpenAI client
client = AzureOpenAI(
    api_key=os.environ["AOAI_KEY"],
    azure_endpoint=os.environ["AOAI_ENDPOINT"],
    api_version="2024-12-01-preview"
)

deployment = os.environ["AOAI_DEPLOYMENT"]

# The ONLY file the AI is allowed to modify
TARGET_FILE = Path("calculator-api/src/Controllers/CalcController.cs")


def read_calc_controller():
    if not TARGET_FILE.exists():
        print(f"ERROR: {TARGET_FILE} not found.")
        sys.exit(1)
    return TARGET_FILE.read_text()


def extract_diff(output):
    if "```diff" not in output:
        return None
    return output.split("```diff")[1].split("```")[0].strip()


def is_valid_diff(diff):
    # Must contain exactly one diff header
    if diff.count("diff --git") != 1:
        return False

    # Must reference ONLY the target file
    if TARGET_FILE.name not in diff:
        return False

    # Validate hunk headers
    for line in diff.splitlines():
        if line.startswith("@@"):
            header = line.replace("@", "").replace("-", "").replace("+", "").replace(",", "").replace(" ", "")
            if not header.isdigit():
                return False

    return True


def apply_patch(diff):
    patch_file = "ai_patch.diff"
    with open(patch_file, "w") as f:
        f.write(diff)

    try:
        subprocess.run(["git", "apply", patch_file], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def create_fix_branch():
    subprocess.run(["git", "checkout", "-b", "fix-ai"], check=False)
    subprocess.run(["git", "add", "."], check=False)
    subprocess.run(["git", "commit", "-m", "AI auto-fix"], check=False)
    subprocess.run(["git", "push", "-u", "origin", "fix-ai"], check=False)


def run_review():
    controller_code = read_calc_controller()

    prompt = f"""
You are an expert .NET API engineer.

You will receive ONE file only:
CalcController.cs

Your job:
- Identify issues in THIS file only.
- Fix ONLY this file.
- Produce a unified diff patch for THIS file only.
- NO multi-file diffs.
- NO new files.
- NO deletions.
- NO renames.
- Hunk headers MUST be numeric (e.g., @@ -1,5 +1,10 @@).
- Patch MUST apply cleanly with `git apply`.

===== FILE: CalcController.cs =====
{controller_code}
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
        print("Invalid diff. Failing.")
        sys.exit(1)

    if apply_patch(diff):
        print("Patch applied.")
        create_fix_branch()
    else:
        print("Patch failed to apply.")
        sys.exit(1)


if __name__ == "__main__":
    run_review()
