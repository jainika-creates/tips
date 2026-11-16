import subprocess
import tempfile
from pathlib import Path


def run(repo, *args, check=True):
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=check
    )


def setup_fixture(root):
    bare = root / "remote.git"
    seed = root / "seed"

    bare.mkdir()
    subprocess.run(
        ["git", "init", "--bare", str(bare)],
        check=True, capture_output=True, text=True
    )

    seed.mkdir()
    run(seed, "init", "-b", "main")
    run(seed, "config", "user.name", "Course Student")
    run(seed, "config", "user.email", "student@example.invalid")

    (seed / "notes.txt").write_text("alpha\n")
    run(seed, "add", "notes.txt")
    run(seed, "commit", "-m", "A")

    (seed / "notes.txt").write_text("alpha\nbeta\n")
    run(seed, "add", "notes.txt")
    run(seed, "commit", "-m", "B")
    commit_b = run(seed, "rev-parse", "HEAD").stdout.strip()

    run(seed, "branch", "topic", commit_b)

    (seed / "todo.txt").write_text("one\n")
    run(seed, "add", "todo.txt")
    run(seed, "commit", "-m", "C")

    run(seed, "remote", "add", "origin", str(bare))
    run(seed, "push", "origin", "main")
    run(seed, "push", "origin", "topic")

    return bare, commit_b


def scenario(force_with_lease):
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        bare, commit_b = setup_fixture(root)

        local = root / "local"
        other = root / "other"

        subprocess.run(
            ["git", "clone", str(bare), str(local)],
            check=True, capture_output=True, text=True
        )
        subprocess.run(
            ["git", "clone", str(bare), str(other)],
            check=True, capture_output=True, text=True
        )

        for repo in (local, other):
            run(repo, "config", "user.name", "Course Student")
            run(repo, "config", "user.email", "student@example.invalid")

        # Both clones start topic at B.
        run(local, "switch", "topic")
        run(other, "switch", "topic")
        assert run(local, "rev-parse", "HEAD").stdout.strip() == commit_b

        # The collaborator advances the remote topic branch.
        (other / "collaborator.txt").write_text("other work\n")
        run(other, "add", "collaborator.txt")
        run(other, "commit", "-m", "Collaborator update")
        run(other, "push", "origin", "topic")

        remote_before = run(
            local, "ls-remote", "origin", "refs/heads/topic"
        ).stdout.split()[0]

        # Local topic gets a different commit based on B.
        (local / "local.txt").write_text("local work\n")
        run(local, "add", "local.txt")
        run(local, "commit", "-m", "Local rewritten work")

        option = "--force-with-lease" if force_with_lease else "--force"
        result = run(
            local, "push", option, "origin", "topic", check=False
        )

        remote_after = run(
            local, "ls-remote", "origin", "refs/heads/topic"
        ).stdout.split()[0]

        return result.returncode, remote_before, remote_after


lease_code, lease_before, lease_after = scenario(True)
force_code, force_before, force_after = scenario(False)

# Check 1: lease rejects the stale update.
assert lease_code != 0, "Expected force-with-lease to reject the push"

# Check 2: rejected lease push leaves remote unchanged.
assert lease_before == lease_after, "Remote changed after rejected lease push"

# Check 3: force push succeeds in the equivalent fixture.
assert force_code == 0, "Expected force push to succeed"

# Check 4: force push replaces the collaborator's remote commit.
assert force_before != force_after, "Remote was not overwritten by force push"

print("PASS: force-with-lease rejected the stale push.")
print("PASS: rejected push preserved the collaborator's remote commit.")
print("PASS: force push succeeded in the equivalent fixture.")
print("PASS: force push changed the remote branch.")
print("All R11-T036 checks passed.")
