# Assignment R11-T032: Forcefully Remove Untracked Directory (`git clean -f -d`)

A comprehensive guide demonstrating the Git state transition for forcefully removing untracked directories and files using `git clean -f -d`.

---

## 1. Command Overview: `git clean -f -d`

In Git, untracked files and directories are items in the working tree that have never been staged or committed, and are not matched by `.gitignore` rules.

- **`-f` (`--force`)**: Git includes a safety configuration guard (`clean.requireForce = true`). By default, Git refuses to delete untracked working-tree files unless `-f` (force) is provided.
- **`-d`**: By default, `git clean` only removes untracked *files*. Passing `-d` instructs Git to also recurse into whole untracked *directories* and remove them.
- **Combined (`-f -d` or `-fd`)**: Recursively and forcefully deletes all untracked files and untracked directories from the working tree.

---

## 2. Reproducible Repository Setup

To verify the state transition deterministically, initialize a temporary repository with the required commit ancestry and branch structure:

```sh
# Initialize repository with default branch 'main'
git init -b main
git config user.name "Course Student"
git config user.email "student@example.invalid"

# Commit A: create notes.txt containing 'alpha\n'
echo "alpha" > notes.txt
git add notes.txt
git commit -m "Commit A: create notes.txt with alpha"

# Commit B: append 'beta\n' to notes.txt
echo "beta" >> notes.txt
git add notes.txt
git commit -m "Commit B: append beta to notes.txt"

# Create branch 'topic' at commit B
git branch topic

# Commit C: create todo.txt containing 'one\n'
echo "one" > todo.txt
git add todo.txt
git commit -m "Commit C: create todo.txt with one"

# Create untracked working-tree files and directories
echo "scratch notes" > scratch.txt
mkdir untracked_dir
echo "log data inside untracked directory" > untracked_dir/temp.log
```

---

## 3. Dynamic Git Object IDs

All object IDs in Git are calculated dynamically based on their content and headers using SHA-1. They should never be hardcoded:

```sh
# Dynamic capture commands:
COMMIT_A=$(git rev-parse main~1)
COMMIT_B=$(git rev-parse topic)
COMMIT_C=$(git rev-parse main)

TREE_A=$(git rev-parse main~1^{tree})
TREE_B=$(git rev-parse topic^{tree})
TREE_C=$(git rev-parse main^{tree})

BLOB_NOTES_A=$(git rev-parse main~1:notes.txt)
BLOB_NOTES_B=$(git rev-parse topic:notes.txt)
BLOB_TODO_C=$(git rev-parse main:todo.txt)
```

| Entity | Dynamic Command | Role |
| :--- | :--- | :--- |
| **Commit A** | `git rev-parse main~1` | Root commit containing `notes.txt` (`alpha\n`) |
| **Commit B** | `git rev-parse topic` | Intermediate commit; base of branch `topic` |
| **Commit C** | `git rev-parse main` | Active commit at `HEAD` |
| **Tree C** | `git rev-parse main^{tree}` | Root tree pointing to `notes.txt` and `todo.txt` |
| **Blob `notes.txt`** | `git rev-parse topic:notes.txt` | Staged content (`alpha\nbeta\n`) |
| **Blob `todo.txt`** | `git rev-parse main:todo.txt` | Staged content (`one\n`) |

---

## 4. Git State Transition Diagram

```
================================================================================
BEFORE RUNNING: git clean -f -d
================================================================================
  HEAD Reference:
    HEAD ────────────────────────► refs/heads/main

  Branch References:
    refs/heads/main ─────────────► Commit C [$(git rev-parse main)]
                                     └── parent: Commit B [$(git rev-parse topic)]
    refs/heads/topic ────────────► Commit B [$(git rev-parse topic)]
                                     └── parent: Commit A [$(git rev-parse main~1)]

  Index / Staging Area (.git/index):
    notes.txt  [blob $(git rev-parse topic:notes.txt)]  (mode 100644)
    todo.txt   [blob $(git rev-parse main:todo.txt)]   (mode 100644)

  Working-Tree Status:
    Tracked files (clean, match index):
      notes.txt  ("alpha\nbeta\n")
      todo.txt   ("one\n")
    Untracked files & directories (git status porcelain: '??'):
      ?? scratch.txt
      ?? untracked_dir/
         └── temp.log

================================================================================
COMMAND: git clean -f -d
Execution Output:
  Removing scratch.txt
  Removing untracked_dir/
================================================================================

AFTER RUNNING: git clean -f -d
================================================================================
  HEAD Reference: [UNCHANGED]
    HEAD ────────────────────────► refs/heads/main

  Branch References: [UNCHANGED]
    refs/heads/main ─────────────► Commit C (unchanged)
    refs/heads/topic ────────────► Commit B (unchanged)

  Commit Ancestry / DAG: [UNCHANGED]
    Commit A ◄── Commit B ◄── Commit C

  Index / Staging Area (.git/index): [UNCHANGED]
    notes.txt  [blob $(git rev-parse topic:notes.txt)]
    todo.txt   [blob $(git rev-parse main:todo.txt)]

  Working-Tree Status: [TRANSITIONED]
    Tracked files (PRESERVED):
      notes.txt  ("alpha\nbeta\n")
      todo.txt   ("one\n")
    Untracked files & directories:
      [PERMANENTLY DELETED] scratch.txt
      [PERMANENTLY DELETED] untracked_dir/
    Result: Clean working tree ('nothing to commit, working tree clean')
================================================================================
```

---

## 5. Detailed Effect on Git Components

1. **Refs (`refs/heads/*`, `HEAD`, tags)**:
   - `git clean` **does not alter any references**.
   - `HEAD` continues pointing to the current branch (`refs/heads/main`).
   - Branch pointers `main` and `topic` remain strictly at their respective commit hashes.

2. **Commit Ancestry (DAG)**:
   - `git clean` **never touches commit or tree objects**.
   - The commit graph `Commit A ◄── Commit B ◄── Commit C` and its parent links are entirely intact.

3. **Index (Staging Area)**:
   - The index (`.git/index`) stores the tracked snapshot.
   - `git clean` **does not touch staged or tracked entries**.
   - Staged files, staged unstaged diffs, and index cache trees are preserved.

4. **Untracked Working-Tree Directories**:
   - Because `-d` is provided, Git traverses into whole untracked directories (`untracked_dir/`) and deletes them alongside standalone untracked files (`scratch.txt`).
   - Any files inside untracked directories (`untracked_dir/temp.log`) are permanently removed from the filesystem.

---

## 6. Verification Script

The verification script [check.py](./check.py) automates the entire sequence in an isolated temporary directory, capturing all dynamic object IDs and asserting all facts:

```sh
python3 work/R11-T032/check.py
```
