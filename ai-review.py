import os
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

deployment = os.environ["AOAI_DEPLOYMENT"]  # e.g., "o4-mini"

# -----------------------------
# File scanning configuration
# -----------------------------
ROOT = Path(".")
PATTERNS = [
    "Dockerfile",
    "docker/Dockerfile",
    "**/*.yml",
    "**/*.yaml",
    "**/*.json",
    "**/*.py",
    "**/*.cs",
]

MAX_BYTES = 200_000  # 200 KB safety limit


def is_binary(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            chunk = f.read(2048)
            return b"\0" in chunk
    except Exception:
        return True


def read_files():
    contents = []

    for pattern in PATTERNS:
        for path in ROOT.glob(pattern):
            if not path.is_file():
                continue

            if is_binary(path):
                contents.append(f"\n\n===== FILE: {path} (SKIPPED: binary) =====")
                continue

            if path.stat().st_size > MAX_BYTES:
                contents.append(f"\n\n===== FILE: {path} (SKIPPED: too large) =====")
                continue

            try:
                text = path.read_text(errors="ignore")
                contents.append(f"\n\n===== FILE: {path} =====\n{text}")
            except Exception as e:
                contents.append(f"\n\n===== FILE: {path} (ERROR READING) =====\n{e}")

    return "\n".join(contents)


# -----------------------------
# Review logic
# -----------------------------
def run_review():
    files_text = read_files()

    prompt = f"""
You are an expert DevOps and cloud reviewer.

IMPORTANT RULE:
Only comment on things that actually appear in the FILES section.
If something is missing (e.g., no Dockerfile, no Kubernetes manifests, no GitHub Actions),
explicitly say: "Not found in provided files."

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
    print(response.choices[0].message.content)
    print("\n===== END OF REVIEW =====\n")


if __name__ == "__main__":
    run_review()
