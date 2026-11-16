import os
import subprocess
import tempfile
from pathlib import Path


def run(command, cwd, env=None):
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=True
    ).stdout.strip()


with tempfile.TemporaryDirectory() as temp:
    repo = Path(temp)

    env = os.environ.copy()
    env.update({
        "GIT_AUTHOR_NAME": "Test User",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test User",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    })

    run(["git", "init", "-b", "main"], repo, env)
    run(["git", "config", "user.name", "Test User"], repo, env)
    run(["git", "config", "user.email", "test@example.com"], repo, env)

    (repo / "notes.txt").write_text("alpha\n")
    run(["git", "add", "notes.txt"], repo, env)
    run(["git", "commit", "-m", "A"], repo, env)
    commit_a = run(["git", "rev-parse", "HEAD"], repo, env)

    with (repo / "notes.txt").open("a") as f:
        f.write("beta\n")
    run(["git", "add", "notes.txt"], repo, env)
    run(["git", "commit", "-m", "B"], repo, env)
    commit_b = run(["git", "rev-parse", "HEAD"], repo, env)

    run(["git", "branch", "topic"], repo, env)

    (repo / "todo.txt").write_text("one\n")
    run(["git", "add", "todo.txt"], repo, env)
    run(["git", "commit", "-m", "C"], repo, env)
    commit_c = run(["git", "rev-parse", "HEAD"], repo, env)

    run(["git", "switch", "topic"], repo, env)
    run(["git", "tag", "topic-at-B"], repo, env)
    run(["git", "tag", "main-at-C", "main"], repo, env)

    tag_b = run(["git", "rev-parse", "refs/tags/topic-at-B"], repo, env)
    tag_c = run(["git", "rev-parse", "refs/tags/main-at-C"], repo, env)
    main = run(["git", "rev-parse", "refs/heads/main"], repo, env)
    topic = run(["git", "rev-parse", "refs/heads/topic"], repo, env)
    current = run(["git", "branch", "--show-current"], repo, env)
    remotes = run(["git", "remote"], repo, env)

    assert tag_b == commit_b, "topic-at-B must point to commit B"
    assert tag_c == commit_c, "main-at-C must point to commit C"
    assert main == commit_c, "The main branch must remain at commit C"
    assert topic == commit_b, "The topic branch must remain at commit B"
    assert current == "topic", "The current branch should be topic"
    assert remotes == "", "The test repository should have no remote"

    Path("work/R11-T034").mkdir(parents=True, exist_ok=True)
    Path("work/R11-T034/inputs.txt").write_text(
        f"A={commit_a}\nB={commit_b}\nC={commit_c}\n"
    )
    Path("work/R11-T034/expected.txt").write_text(
        "topic-at-B points to B\n"
        "main-at-C points to C\n"
        "main remains at C\n"
        "topic remains at B\n"
        "current branch is topic\n"
        "no remote is configured\n"
    )
    Path("work/R11-T034/actual.txt").write_text(
        f"topic-at-B={tag_b}\n"
        f"main-at-C={tag_c}\n"
        f"main={main}\n"
        f"topic={topic}\n"
        f"current={current}\n"
        f"remotes={remotes or '(none)'}\n"
    )
    Path("work/R11-T034/tool-versions.txt").write_text(
        run(["git", "--version"], repo, env) + "\n"
    )

    print("PASS: All local tag checks succeeded.")
