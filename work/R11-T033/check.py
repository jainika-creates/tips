#!/usr/bin/env python3
"""
Verification script for Assignment R11-T033 (Find out branches containing commit-hash).

Requirements:
1. Temporary Git repository with:
   - Branch 'main'
   - Author: Course Student <student@example.invalid>
   - Commit A: create notes.txt with 'alpha\\n'
   - Commit B: append 'beta\\n' to notes.txt
   - Commit C: create todo.txt with 'one\\n'
   - Branch 'topic' created at commit B
   - Second local bare repository acting as remote via file:// URL
2. Demonstrate branch containment commands:
   - git branch --contains <commit>
   - git branch -a --contains <commit>
3. Demonstrate a reversible mistake and recovery:
   - Mistake 1: Accidental deletion of branch 'topic'
   - Recovery 1: Recreate branch 'topic' from commit hash
   - Mistake 2: Accidental hard reset of 'main' to Commit A
   - Recovery 2: Reset back using reflog (HEAD@{1} or commit C hash)
4. Dynamic capture of all object IDs (never hardcoded).
5. Assertions verifying meaningful Git state facts, branch containment, and recovery tree restoration.
"""

import os
import subprocess
import tempfile
import sys


def run_cmd(cmd, cwd, env=None):
    """Run command and return stripped stdout with check=True."""
    res = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=True
    )
    return res.stdout.strip()


def run_cmd_raw(cmd, cwd, env=None):
    """Run command and return (stdout, stderr, returncode)."""
    res = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True
    )
    return res.stdout, res.stderr, res.returncode


def verify_r11_t033(base_dir=None):
    """Execute complete reproducible experiment and assertions."""
    with tempfile.TemporaryDirectory(dir=base_dir) as td, \
         tempfile.TemporaryDirectory(dir=base_dir) as bare_td:

        repo_dir = td
        remote_bare_dir = bare_td

        # Deterministic author and committer environment
        env = os.environ.copy()
        env["GIT_AUTHOR_NAME"] = "Course Student"
        env["GIT_AUTHOR_EMAIL"] = "student@example.invalid"
        env["GIT_COMMITTER_NAME"] = "Course Student"
        env["GIT_COMMITTER_EMAIL"] = "student@example.invalid"

        # 0. Initialize local bare remote
        run_cmd(["git", "init", "--bare"], cwd=remote_bare_dir, env=env)

        # 1. Initialize repository with default branch 'main'
        run_cmd(["git", "init", "-b", "main"], cwd=repo_dir, env=env)
        run_cmd(["git", "config", "user.name", "Course Student"], cwd=repo_dir, env=env)
        run_cmd(["git", "config", "user.email", "student@example.invalid"], cwd=repo_dir, env=env)

        # 2. Commit A: create notes.txt containing 'alpha\n'
        notes_path = os.path.join(repo_dir, "notes.txt")
        with open(notes_path, "w") as f:
            f.write("alpha\n")
        run_cmd(["git", "add", "notes.txt"], cwd=repo_dir, env=env)
        run_cmd(["git", "commit", "-m", "Commit A: create notes.txt with alpha"], cwd=repo_dir, env=env)

        commit_a = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir, env=env)
        tree_a = run_cmd(["git", "rev-parse", "HEAD^{tree}"], cwd=repo_dir, env=env)
        blob_notes_a = run_cmd(["git", "rev-parse", "HEAD:notes.txt"], cwd=repo_dir, env=env)

        # 3. Commit B: append 'beta\n' to notes.txt
        with open(notes_path, "a") as f:
            f.write("beta\n")
        run_cmd(["git", "add", "notes.txt"], cwd=repo_dir, env=env)
        run_cmd(["git", "commit", "-m", "Commit B: append beta to notes.txt"], cwd=repo_dir, env=env)

        commit_b = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir, env=env)
        tree_b = run_cmd(["git", "rev-parse", "HEAD^{tree}"], cwd=repo_dir, env=env)
        blob_notes_b = run_cmd(["git", "rev-parse", "HEAD:notes.txt"], cwd=repo_dir, env=env)

        # 4. Create branch 'topic' at commit B
        run_cmd(["git", "branch", "topic"], cwd=repo_dir, env=env)

        # 5. Commit C: create todo.txt containing 'one\n'
        todo_path = os.path.join(repo_dir, "todo.txt")
        with open(todo_path, "w") as f:
            f.write("one\n")
        run_cmd(["git", "add", "todo.txt"], cwd=repo_dir, env=env)
        run_cmd(["git", "commit", "-m", "Commit C: create todo.txt with one"], cwd=repo_dir, env=env)

        commit_c = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir, env=env)
        tree_c = run_cmd(["git", "rev-parse", "HEAD^{tree}"], cwd=repo_dir, env=env)
        blob_todo_c = run_cmd(["git", "rev-parse", "HEAD:todo.txt"], cwd=repo_dir, env=env)

        # 6. Set up local bare remote via file:// and push branches
        remote_url = f"file://{remote_bare_dir}"
        run_cmd(["git", "remote", "add", "origin", remote_url], cwd=repo_dir, env=env)
        run_cmd(["git", "push", "origin", "main", "topic"], cwd=repo_dir, env=env)

        # ---------------------------------------------------------------------
        # ASSERTIONS: State Facts & Branch Containment
        # ---------------------------------------------------------------------
        # Fact 1: Active branch is 'main'
        current_branch = run_cmd(["git", "branch", "--show-current"], cwd=repo_dir, env=env)
        assert current_branch == "main", f"Expected active branch 'main', got {current_branch}"

        # Fact 2: Author of all commits is 'Course Student <student@example.invalid>'
        authors = run_cmd(["git", "log", "--format=%an <%ae>"], cwd=repo_dir, env=env).splitlines()
        assert len(authors) == 3, f"Expected 3 commits on main, got {len(authors)}"
        for author in authors:
            assert author == "Course Student <student@example.invalid>", f"Unexpected author: {author}"

        # Fact 3: Branch 'topic' points to Commit B
        topic_hash = run_cmd(["git", "rev-parse", "topic"], cwd=repo_dir, env=env)
        assert topic_hash == commit_b, f"topic branch points to {topic_hash}, expected {commit_b}"

        # Fact 4: Branch containment for Commit A (in both 'main' and 'topic')
        branches_contains_a = run_cmd(["git", "branch", "--contains", commit_a], cwd=repo_dir, env=env).split()
        assert "main" in branches_contains_a, f"Commit A should be in 'main': {branches_contains_a}"
        assert "topic" in branches_contains_a, f"Commit A should be in 'topic': {branches_contains_a}"

        # Fact 5: Branch containment for Commit B (in both 'main' and 'topic')
        branches_contains_b = run_cmd(["git", "branch", "--contains", commit_b], cwd=repo_dir, env=env).split()
        assert "main" in branches_contains_b, f"Commit B should be in 'main': {branches_contains_b}"
        assert "topic" in branches_contains_b, f"Commit B should be in 'topic': {branches_contains_b}"

        # Fact 6: Branch containment for Commit C (in 'main' only, NOT in 'topic')
        branches_contains_c = run_cmd(["git", "branch", "--contains", commit_c], cwd=repo_dir, env=env).split()
        assert "main" in branches_contains_c, f"Commit C should be in 'main': {branches_contains_c}"
        assert "topic" not in branches_contains_c, f"Commit C should NOT be in 'topic': {branches_contains_c}"

        # Fact 7: Remote branch containment with -a for Commit C
        branches_contains_a_c = run_cmd(["git", "branch", "-a", "--contains", commit_c], cwd=repo_dir, env=env).split()
        assert "main" in branches_contains_a_c, f"Local 'main' missing in -a: {branches_contains_a_c}"
        assert "remotes/origin/main" in branches_contains_a_c, f"Remote 'origin/main' missing in -a: {branches_contains_a_c}"
        assert "remotes/origin/topic" not in branches_contains_a_c, f"Remote 'origin/topic' should not contain Commit C: {branches_contains_a_c}"

        # ---------------------------------------------------------------------
        # REVERSIBLE MISTAKE & RECOVERY 1: Accidental Branch Deletion
        # ---------------------------------------------------------------------
        # Pre-mistake tree of topic:
        saved_topic_tree = run_cmd(["git", "rev-parse", "topic^{tree}"], cwd=repo_dir, env=env)
        assert saved_topic_tree == tree_b, "Saved topic tree mismatch"

        # Destructive action: delete branch 'topic'
        del_out, del_err, del_rc = run_cmd_raw(["git", "branch", "-D", "topic"], cwd=repo_dir, env=env)
        assert del_rc == 0, f"git branch -D topic failed: {del_err}"
        current_branches = run_cmd(["git", "branch"], cwd=repo_dir, env=env).split()
        assert "topic" not in current_branches, "Branch 'topic' should have been deleted"

        # Recovery 1: Recreate branch 'topic' at commit B hash
        rec_out, rec_err, rec_rc = run_cmd_raw(["git", "branch", "topic", commit_b], cwd=repo_dir, env=env)
        assert rec_rc == 0, f"git branch topic recovery failed: {rec_err}"
        recovered_topic_commit = run_cmd(["git", "rev-parse", "topic"], cwd=repo_dir, env=env)
        recovered_topic_tree = run_cmd(["git", "rev-parse", "topic^{tree}"], cwd=repo_dir, env=env)
        assert recovered_topic_commit == commit_b, "Recovered topic commit mismatch"
        assert recovered_topic_tree == saved_topic_tree, "Recovered topic tree hash mismatch"

        # ---------------------------------------------------------------------
        # REVERSIBLE MISTAKE & RECOVERY 2: Accidental Hard Reset on main
        # ---------------------------------------------------------------------
        # Pre-mistake tree of main (HEAD):
        saved_main_tree = run_cmd(["git", "rev-parse", "HEAD^{tree}"], cwd=repo_dir, env=env)
        assert saved_main_tree == tree_c, "Saved main tree mismatch"

        # Destructive action: accidental hard reset to Commit A
        reset_out, reset_err, reset_rc = run_cmd_raw(["git", "reset", "--hard", commit_a], cwd=repo_dir, env=env)
        assert reset_rc == 0, f"git reset --hard failed: {reset_err}"
        assert not os.path.exists(todo_path), "todo.txt should have been removed by hard reset"
        current_head_after_reset = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir, env=env)
        assert current_head_after_reset == commit_a, "HEAD should point to Commit A after reset"

        # Recovery 2: Recover using reflog (HEAD@{1} or commit C)
        reflog_first = run_cmd(["git", "rev-parse", "HEAD@{1}"], cwd=repo_dir, env=env)
        assert reflog_first == commit_c, f"HEAD@{{1}} is {reflog_first}, expected {commit_c}"
        rec2_out, rec2_err, rec2_rc = run_cmd_raw(["git", "reset", "--hard", "HEAD@{1}"], cwd=repo_dir, env=env)
        assert rec2_rc == 0, f"Recovery via reflog failed: {rec2_err}"

        # Verification of Recovery 2:
        recovered_head = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir, env=env)
        recovered_tree = run_cmd(["git", "rev-parse", "HEAD^{tree}"], cwd=repo_dir, env=env)
        assert recovered_head == commit_c, f"Recovered HEAD {recovered_head} does not match {commit_c}"
        assert recovered_tree == saved_main_tree, f"Recovered tree {recovered_tree} does not match {saved_main_tree}"
        assert os.path.exists(todo_path), "todo.txt was not restored after recovery"
        with open(todo_path) as f:
            assert f.read() == "one\n", "todo.txt content altered after recovery"
        with open(notes_path) as f:
            assert f.read() == "alpha\nbeta\n", "notes.txt content altered after recovery"

        status_clean = run_cmd(["git", "status", "--porcelain"], cwd=repo_dir, env=env)
        assert status_clean == "", f"Working tree not clean after recovery:\n{status_clean}"

        # Collect results
        return {
            "commit_a": commit_a,
            "tree_a": tree_a,
            "blob_notes_a": blob_notes_a,
            "commit_b": commit_b,
            "tree_b": tree_b,
            "blob_notes_b": blob_notes_b,
            "commit_c": commit_c,
            "tree_c": tree_c,
            "blob_todo_c": blob_todo_c,
            "branches_contains_a": run_cmd(["git", "branch", "--contains", commit_a], cwd=repo_dir, env=env),
            "branches_contains_b": run_cmd(["git", "branch", "--contains", commit_b], cwd=repo_dir, env=env),
            "branches_contains_c": run_cmd(["git", "branch", "--contains", commit_c], cwd=repo_dir, env=env),
            "branches_contains_all_c": run_cmd(["git", "branch", "-a", "--contains", commit_c], cwd=repo_dir, env=env),
            "reflog_output": run_cmd(["git", "reflog", "-n", "5"], cwd=repo_dir, env=env),
        }


def main():
    print("Running verification for Assignment R11-T033 (Find out branches containing commit-hash)...")
    data = verify_r11_t033()
    print("All assertions passed successfully!")
    print("\n[Dynamic Commit Hashes]")
    print(f"  Commit A: {data['commit_a']}")
    print(f"  Commit B: {data['commit_b']}")
    print(f"  Commit C: {data['commit_c']}")
    print("\n[Branch Containment for Commit C (local)]:")
    print(data["branches_contains_c"])
    print("\n[Branch Containment for Commit C (local + remote -a)]:")
    print(data["branches_contains_all_c"])
    print("\n[Recent Reflog Entries]:")
    print(data["reflog_output"])


if __name__ == "__main__":
    main()
