#!/usr/bin/env python3
"""
Verification script for Assignment R11-T032 (git clean -f -d).

Requirements:
1. Temporary Git repository with:
   - Branch 'main'
   - Author: Course Student <student@example.invalid>
   - Commit A: create notes.txt containing 'alpha\\n'
   - Commit B: append 'beta\\n' to notes.txt
   - Commit C: create todo.txt containing 'one\\n'
   - Branch 'topic' created at commit B
2. Demonstrate before-and-after Git state transition for forcefully removing an untracked directory:
   - Untracked directory (untracked_dir/) containing untracked files
   - Untracked file (scratch.txt)
   - Command: git clean -f -d
3. Capture object IDs dynamically using Git commands (never hardcode hashes).
4. Assert all Git state facts:
   - Refs and HEAD remain unchanged
   - Commit ancestry (DAG) remains unchanged
   - Index (staging area) remains unchanged
   - Untracked directory and untracked file are removed
   - Tracked files in working tree remain intact
"""

import os
import subprocess
import tempfile
import sys


def run_cmd(cmd, cwd, env=None):
    """Run command and return stripped stdout, raising if command fails."""
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


def verify_r11_t032(base_dir=None):
    """Execute complete reproducible setup and state transition verification."""
    with tempfile.TemporaryDirectory(dir=base_dir) as td:
        repo_dir = td

        # Deterministic author and committer environment
        env = os.environ.copy()
        env["GIT_AUTHOR_NAME"] = "Course Student"
        env["GIT_AUTHOR_EMAIL"] = "student@example.invalid"
        env["GIT_COMMITTER_NAME"] = "Course Student"
        env["GIT_COMMITTER_EMAIL"] = "student@example.invalid"

        # 1. Initialize repository with branch 'main'
        run_cmd(["git", "init", "-b", "main"], cwd=repo_dir, env=env)
        run_cmd(["git", "config", "user.name", "Course Student"], cwd=repo_dir, env=env)
        run_cmd(["git", "config", "user.email", "student@example.invalid"], cwd=repo_dir, env=env)

        # 2. Commit A: create notes.txt containing 'alpha\n'
        notes_path = os.path.join(repo_dir, "notes.txt")
        with open(notes_path, "w") as f:
            f.write("alpha\n")
        run_cmd(["git", "add", "notes.txt"], cwd=repo_dir, env=env)
        run_cmd(["git", "commit", "-m", "Commit A: create notes.txt with alpha"], cwd=repo_dir, env=env)

        # Dynamic capture of Commit A objects
        commit_a = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir, env=env)
        tree_a = run_cmd(["git", "rev-parse", "HEAD^{tree}"], cwd=repo_dir, env=env)
        blob_notes_a = run_cmd(["git", "rev-parse", "HEAD:notes.txt"], cwd=repo_dir, env=env)

        # 3. Commit B: append 'beta\n' to notes.txt
        with open(notes_path, "a") as f:
            f.write("beta\n")
        run_cmd(["git", "add", "notes.txt"], cwd=repo_dir, env=env)
        run_cmd(["git", "commit", "-m", "Commit B: append beta to notes.txt"], cwd=repo_dir, env=env)

        # Dynamic capture of Commit B objects
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

        # Dynamic capture of Commit C objects
        commit_c = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir, env=env)
        tree_c = run_cmd(["git", "rev-parse", "HEAD^{tree}"], cwd=repo_dir, env=env)
        blob_todo_c = run_cmd(["git", "rev-parse", "HEAD:todo.txt"], cwd=repo_dir, env=env)

        # 6. Create untracked working-tree directory and untracked file
        untracked_dir = os.path.join(repo_dir, "untracked_dir")
        os.makedirs(untracked_dir, exist_ok=True)
        untracked_file_inside = os.path.join(untracked_dir, "temp.log")
        with open(untracked_file_inside, "w") as f:
            f.write("log data inside untracked directory\n")

        scratch_path = os.path.join(repo_dir, "scratch.txt")
        with open(scratch_path, "w") as f:
            f.write("scratch notes\n")

        # ---------------------------------------------------------------------
        # PRE-TRANSITION STATE CAPTURE & ASSERTIONS
        # ---------------------------------------------------------------------
        head_before = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir, env=env)
        branch_main_before = run_cmd(["git", "rev-parse", "refs/heads/main"], cwd=repo_dir, env=env)
        branch_topic_before = run_cmd(["git", "rev-parse", "refs/heads/topic"], cwd=repo_dir, env=env)
        current_branch_before = run_cmd(["git", "branch", "--show-current"], cwd=repo_dir, env=env)
        index_ls_before = run_cmd(["git", "ls-files", "--stage"], cwd=repo_dir, env=env)
        status_before = run_cmd(["git", "status", "--porcelain"], cwd=repo_dir, env=env)

        # Verify pre-clean state assertions
        assert current_branch_before == "main", f"Expected active branch 'main', got {current_branch_before}"
        assert head_before == commit_c, "HEAD does not match Commit C before clean"
        assert branch_main_before == commit_c, "Branch 'main' does not match Commit C before clean"
        assert branch_topic_before == commit_b, "Branch 'topic' does not match Commit B before clean"
        assert os.path.isdir(untracked_dir), "untracked_dir should exist before clean"
        assert os.path.isfile(scratch_path), "scratch.txt should exist before clean"
        assert "?? scratch.txt" in status_before, "scratch.txt not reported untracked"
        assert "?? untracked_dir/" in status_before, "untracked_dir/ not reported untracked"

        # ---------------------------------------------------------------------
        # EXECUTE COMMAND: git clean -f -d
        # ---------------------------------------------------------------------
        clean_stdout, clean_stderr, clean_rc = run_cmd_raw(["git", "clean", "-f", "-d"], cwd=repo_dir, env=env)
        assert clean_rc == 0, f"git clean -f -d failed: {clean_stderr}"

        # ---------------------------------------------------------------------
        # POST-TRANSITION STATE CAPTURE & ASSERTIONS
        # ---------------------------------------------------------------------
        head_after = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir, env=env)
        branch_main_after = run_cmd(["git", "rev-parse", "refs/heads/main"], cwd=repo_dir, env=env)
        branch_topic_after = run_cmd(["git", "rev-parse", "refs/heads/topic"], cwd=repo_dir, env=env)
        current_branch_after = run_cmd(["git", "branch", "--show-current"], cwd=repo_dir, env=env)
        index_ls_after = run_cmd(["git", "ls-files", "--stage"], cwd=repo_dir, env=env)
        status_after = run_cmd(["git", "status", "--porcelain"], cwd=repo_dir, env=env)

        # Fact 1: HEAD reference is completely unaffected
        assert head_after == head_before == commit_c, (
            f"HEAD reference changed unexpectedly: {head_after} != {head_before}"
        )
        assert current_branch_after == "main", "Current branch changed unexpectedly"

        # Fact 2: Branch references ('main', 'topic') are completely unaffected
        assert branch_main_after == branch_main_before == commit_c, (
            "Branch 'main' reference changed unexpectedly"
        )
        assert branch_topic_after == branch_topic_before == commit_b, (
            "Branch 'topic' reference changed unexpectedly"
        )

        # Fact 3: Commit ancestry / DAG is completely unaffected
        commit_c_parents = run_cmd(["git", "rev-list", "--parents", "-n", "1", commit_c], cwd=repo_dir, env=env).split()
        assert commit_c_parents == [commit_c, commit_b], f"Commit C parent mismatch: {commit_c_parents}"
        commit_b_parents = run_cmd(["git", "rev-list", "--parents", "-n", "1", commit_b], cwd=repo_dir, env=env).split()
        assert commit_b_parents == [commit_b, commit_a], f"Commit B parent mismatch: {commit_b_parents}"

        # Fact 4: Index (staging area) is completely unaffected
        assert index_ls_after == index_ls_before, "Index files changed unexpectedly"
        assert blob_notes_b in index_ls_after, "Blob for notes.txt missing from index"
        assert blob_todo_c in index_ls_after, "Blob for todo.txt missing from index"

        # Fact 5: Tracked working tree files are completely preserved
        assert os.path.isfile(notes_path), "Tracked notes.txt missing after clean"
        with open(notes_path) as f:
            assert f.read() == "alpha\nbeta\n", "Content of tracked notes.txt altered"
        assert os.path.isfile(todo_path), "Tracked todo.txt missing after clean"
        with open(todo_path) as f:
            assert f.read() == "one\n", "Content of tracked todo.txt altered"

        # Fact 6: Untracked directory and untracked file are forcefully removed
        assert not os.path.exists(untracked_dir), "untracked_dir was NOT removed by git clean -f -d"
        assert not os.path.exists(untracked_file_inside), "untracked file inside directory was NOT removed"
        assert not os.path.exists(scratch_path), "scratch.txt was NOT removed by git clean -f -d"

        # Fact 7: Working tree is now completely clean
        assert status_after == "", f"Working tree is not clean after git clean -f -d:\n{status_after}"

        # Build state transition diagram and data
        data = {
            "commit_a": commit_a,
            "tree_a": tree_a,
            "blob_notes_a": blob_notes_a,
            "commit_b": commit_b,
            "tree_b": tree_b,
            "blob_notes_b": blob_notes_b,
            "commit_c": commit_c,
            "tree_c": tree_c,
            "blob_todo_c": blob_todo_c,
            "clean_output": clean_stdout.strip(),
            "status_before": status_before,
            "status_after": status_after,
            "index_ls": index_ls_after,
        }

        return data


def format_diagram(data):
    """Format a compact diagram of the before-and-after Git state."""
    return f"""================================================================================
GIT STATE TRANSITION: git clean -f -d
================================================================================

[BEFORE COMMAND EXECUTION]
  HEAD Pointer:
    HEAD ────────────────────────► refs/heads/main

  Branch References:
    refs/heads/main ─────────────► {data['commit_c']} (Commit C: todo.txt containing 'one')
                                     └── parent: {data['commit_b']}
    refs/heads/topic ────────────► {data['commit_b']} (Commit B: notes.txt containing 'alpha\\nbeta')
                                     └── parent: {data['commit_a']}

  Staged Files in Index (.git/index):
    notes.txt  [blob {data['blob_notes_b']}]  (mode 100644)
    todo.txt   [blob {data['blob_todo_c']}]  (mode 100644)

  Working-Tree Status:
    Tracked files:
      notes.txt  (clean, matches index)
      todo.txt   (clean, matches index)
    Untracked files & directories (porcelain: ??):
      ?? scratch.txt
      ?? untracked_dir/
         └── temp.log

--------------------------------------------------------------------------------
COMMAND EXECUTED: git clean -f -d
Output:
{data['clean_output']}
--------------------------------------------------------------------------------

[AFTER COMMAND EXECUTION]
  HEAD Pointer: [UNCHANGED]
    HEAD ────────────────────────► refs/heads/main

  Branch References: [UNCHANGED]
    refs/heads/main ─────────────► {data['commit_c']}
    refs/heads/topic ────────────► {data['commit_b']}

  Commit Ancestry / DAG: [UNCHANGED]
    Commit A ({data['commit_a'][:7]}) ◄── Commit B ({data['commit_b'][:7]}) ◄── Commit C ({data['commit_c'][:7]})

  Staged Files in Index (.git/index): [UNCHANGED]
    notes.txt  [blob {data['blob_notes_b']}]
    todo.txt   [blob {data['blob_todo_c']}]

  Working-Tree Status: [TRANSITIONED]
    Tracked files:
      notes.txt  (preserved, content: "alpha\\nbeta\\n")
      todo.txt   (preserved, content: "one\\n")
    Untracked files & directories:
      [REMOVED] scratch.txt
      [REMOVED] untracked_dir/ (and all contents)
    Status: Clean (working tree clean, nothing to commit)
================================================================================
"""


def main():
    print("Running verification for Assignment R11-T032 (git clean -f -d)...")
    data = verify_r11_t032()
    print("All assertions passed successfully!")
    print("\nDynamic Git Object IDs Captured:")
    print(f"  Commit A: {data['commit_a']} (Tree: {data['tree_a']}, Blob notes.txt: {data['blob_notes_a']})")
    print(f"  Commit B: {data['commit_b']} (Tree: {data['tree_b']}, Blob notes.txt: {data['blob_notes_b']})")
    print(f"  Commit C: {data['commit_c']} (Tree: {data['tree_c']}, Blob todo.txt: {data['blob_todo_c']})")
    print("\nGenerated State Transition Diagram:")
    print(format_diagram(data))


if __name__ == "__main__":
    main()
