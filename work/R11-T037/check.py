import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "work" / "R11-T037"
results = []

def record(name, passed, expected, actual):
    results.append({
        "check": name,
        "passed": passed,
        "expected": expected,
        "actual": actual
    })
    assert passed, f"FAILED: {name}: {actual}"

def run(args, cwd, env, check=True):
    return subprocess.run(
        args, cwd=cwd, env=env,
        text=True, capture_output=True, check=check
    )

with tempfile.TemporaryDirectory(prefix="R11-T037-") as temp:
    base = Path(temp)
    repo = base / "repo"
    home = base / "home"
    repo.mkdir()
    home.mkdir()

    env = os.environ.copy()
    env["HOME"] = str(home)
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env.pop("GIT_CONFIG_GLOBAL", None)
    env["GIT_AUTHOR_NAME"] = "Course Student"
    env["GIT_AUTHOR_EMAIL"] = "student@example.invalid"
    env["GIT_COMMITTER_NAME"] = "Course Student"
    env["GIT_COMMITTER_EMAIL"] = "student@example.invalid"

    run(["git", "init", "-b", "main"], repo, env)

    (repo / "notes.txt").write_text("alpha\n")
    run(["git", "add", "notes.txt"], repo, env)
    run(["git", "commit", "-m", "A: create notes"], repo, env)
    commit_a = run(
        ["git", "rev-parse", "HEAD"], repo, env
    ).stdout.strip()

    with (repo / "notes.txt").open("a") as f:
        f.write("beta\n")
    run(["git", "add", "notes.txt"], repo, env)
    run(["git", "commit", "-m", "B: append beta"], repo, env)
    commit_b = run(
        ["git", "rev-parse", "HEAD"], repo, env
    ).stdout.strip()

    run(["git", "branch", "topic", commit_b], repo, env)

    (repo / "todo.txt").write_text("one\n")
    run(["git", "add", "todo.txt"], repo, env)
    run(["git", "commit", "-m", "C: add todo"], repo, env)
    commit_c = run(
        ["git", "rev-parse", "HEAD"], repo, env
    ).stdout.strip()

    main_head = run(
        ["git", "rev-parse", "main"], repo, env
    ).stdout.strip()
    topic_head = run(
        ["git", "rev-parse", "topic"], repo, env
    ).stdout.strip()

    record("main points to commit C", main_head == commit_c,
           commit_c, main_head)
    record("topic points to commit B", topic_head == commit_b,
           commit_b, topic_head)
    record("three commits have distinct IDs",
           len({commit_a, commit_b, commit_c}) == 3,
           "3 distinct commit IDs",
           [commit_a, commit_b, commit_c])

    record("notes contains alpha and beta",
           (repo / "notes.txt").read_text() == "alpha\nbeta\n",
           "alpha\\nbeta\\n",
           repr((repo / "notes.txt").read_text()))
    record("todo exists on main",
           (repo / "todo.txt").read_text() == "one\n",
           "one\\n", repr((repo / "todo.txt").read_text()))

    # Make the global config directory non-writable.
    os.chmod(home, 0o555)
    failed = run(
        ["git", "config", "--global", "core.ignorecase", "false"],
        repo, env, check=False
    )
    record("global command fails with unwritable HOME",
           failed.returncode != 0,
           "non-zero exit status",
           {"returncode": failed.returncode,
            "stderr": failed.stderr.strip()})

    os.chmod(home, 0o755)

    repaired = run(
        ["git", "config", "--global", "core.ignorecase", "false"],
        repo, env, check=False
    )
    record("global command succeeds after permission repair",
           repaired.returncode == 0,
           "exit status 0",
           {"returncode": repaired.returncode,
            "stderr": repaired.stderr.strip()})

    value = run(
        ["git", "config", "--global", "--get", "core.ignorecase"],
        repo, env
    ).stdout.strip()
    record("global setting is false", value == "false",
           "false", value)

    version = run(["git", "--version"], repo, env).stdout.strip()

    (EVIDENCE / "inputs.txt").write_text(
        "Repository: temporary Git repository\n"
        "Initial branch: main\n"
        "Author: Course Student <student@example.invalid>\n"
        "Commit A: notes.txt contains alpha\\n\n"
        "Commit B: append beta\\n to notes.txt\n"
        "Branch topic: created at commit B\n"
        "Commit C: todo.txt contains one\\n\n"
        "Failure condition: HOME directory mode 0555\n"
        "Repair: restore HOME directory mode 0755\n"
        "Command: git config --global core.ignorecase false\n"
    )

    (EVIDENCE / "expected.txt").write_text(
        "Three distinct commits; main at C; topic at B.\n"
        "Global configuration fails while HOME is not writable.\n"
        "The same command succeeds after write permission is restored.\n"
        "core.ignorecase reads false.\n"
    )

    (EVIDENCE / "versions.txt").write_text(
        f"{version}\nPython {os.sys.version}\n"
    )

(EVIDENCE / "results.json").write_text(
    json.dumps(results, indent=2) + "\n"
)

print(json.dumps(results, indent=2))
print(f"\nAll {len(results)} checks passed.")
