from pathlib import Path
import subprocess
import tempfile
import sys
import shlex

OUT = Path(__file__).parent
LOG = []

(OUT / "inputs.txt").write_text(
    "Temporary Git repository\n"
    "Branch: main\n"
    "Author: Course Student\n"
    "Email: student@example.invalid\n"
    "Commit A: notes.txt contains alpha\\n\n"
    "Commit B: notes.txt appends beta\\n\n"
    "Create topic branch at B\n"
    "Commit C: todo.txt contains one\\n\n"
    "Test paths: release notes.txt and sample data/\n"
    "Operation: git stash push --keep-index\n"
)

(OUT / "expected.txt").write_text(
    "1. Exactly three initial commits A, B and C.\n"
    "2. topic points to commit B.\n"
    "3. Staged changes remain staged after the stash.\n"
    "4. Unstaged changes in the selected paths are stashed.\n"
    "5. Unselected todo.txt modification remains unstashed.\n"
    "6. Stash contains the unstaged changes.\n"
)

def run_git(repo, *args):
    command = ["git", *args]
    result = subprocess.run(
        command,
        cwd=repo,
        check=True,
        text=True,
        capture_output=True
    )
    LOG.append(
        "$ " + shlex.join(command) + "\n"
        + result.stdout
        + result.stderr
    )
    return result.stdout

def expect(condition, message):
    if not condition:
        raise AssertionError(message)
    LOG.append("PASS: " + message)

try:
    with tempfile.TemporaryDirectory(prefix="R11-T035-") as temp:
        repo = Path(temp)

        run_git(repo, "init", "-b", "main")
        run_git(repo, "config", "user.name", "Course Student")
        run_git(repo, "config", "user.email", "student@example.invalid")

        # Commit A
        (repo / "notes.txt").write_text("alpha\n")
        (repo / "release notes.txt").write_text("release base\n")
        (repo / "sample data").mkdir()
        (repo / "sample data" / "guide.txt").write_text("directory base\n")

        run_git(
            repo, "add", "--",
            "notes.txt", "release notes.txt", "sample data/guide.txt"
        )
        run_git(repo, "commit", "-m", "A: create notes")

        # Commit B
        with (repo / "notes.txt").open("a") as f:
            f.write("beta\n")

        run_git(repo, "add", "--", "notes.txt")
        run_git(repo, "commit", "-m", "B: append beta")
        commit_b = run_git(repo, "rev-parse", "HEAD").strip()

        # Create topic at B
        run_git(repo, "branch", "topic")

        # Commit C on main
        (repo / "todo.txt").write_text("one\n")
        run_git(repo, "add", "--", "todo.txt")
        run_git(repo, "commit", "-m", "C: add todo")

        commit_count = len(
            run_git(repo, "rev-list", "--count", "main").strip()
        ) if False else len(
            run_git(repo, "rev-list", "--reverse", "main").splitlines()
        )

        expect(commit_count == 3, "Main has exactly three initial commits A, B and C.")

        topic = run_git(repo, "rev-parse", "topic").strip()
        expect(topic == commit_b, "topic points to commit B.")

        # Stage one change.
        (repo / "release notes.txt").write_text(
            "release base\nstaged line\n"
        )
        run_git(repo, "add", "--", "release notes.txt")

        # Add further unstaged changes.
        with (repo / "release notes.txt").open("a") as f:
            f.write("unstaged line\n")

        with (repo / "sample data" / "guide.txt").open("a") as f:
            f.write("directory unstaged line\n")

        # This change is outside the requested pathspecs.
        with (repo / "todo.txt").open("a") as f:
            f.write("outside path line\n")

        # The exact operation being tested.
        run_git(
            repo, "stash", "push", "--keep-index", "--",
            "release notes.txt", "sample data"
        )

        staged = run_git(repo, "diff", "--cached", "--", "release notes.txt")
        unstaged = run_git(repo, "diff", "--", "release notes.txt")
        todo_diff = run_git(repo, "diff", "--", "todo.txt")
        stash_patch = run_git(repo, "stash", "show", "-p", "stash@{0}")

        guide = (repo / "sample data" / "guide.txt").read_text()

        expect(
            "staged line" in staged,
            "Staged changes in release notes.txt remain staged."
        )

        expect(
            unstaged == "",
            "Unstaged changes in release notes.txt were removed from the working tree."
        )

        expect(
            guide == "directory base\n",
            "Unstaged changes in the sample data directory were stashed."
        )

        expect(
            "outside path line" in todo_diff,
            "Changes outside the selected paths remain unstashed."
        )

        expect(
            "unstaged line" in stash_patch
            and "directory unstaged line" in stash_patch,
            "The stash contains both selected unstaged changes."
        )

        expect(
            bool(run_git(repo, "stash", "list").strip()),
            "A stash entry was created."
        )

        LOG.append(
            "\nCommit A/B/C IDs:\n"
            + run_git(repo, "log", "--reverse", "--format=%H %s", "main")
            + "\nTopic commit: " + topic + "\n"
        )

    LOG.append("\nALL CHECKS PASSED.\n")

except Exception as error:
    LOG.append("\nFAILED: " + repr(error) + "\n")
    (OUT / "actual.txt").write_text("\n".join(LOG))
    print("\n".join(LOG))
    raise

(OUT / "actual.txt").write_text("\n".join(LOG))
print("\n".join(LOG))
print("\nSUCCESS: All R11-T035 checks passed.")
