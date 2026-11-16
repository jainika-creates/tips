# Assignment R11-T033: Find Out Branches Containing Commit-Hash & Recovery Guide

A comprehensive guide demonstrating Git branch containment commands (`git branch --contains` and `git branch -a --contains`), along with recovery mechanisms from reversible mistakes associated with branch operations.

---

## 1. Command Overview

- **`git branch --contains <commit-ish>`**: Lists all local branches in the repository that contain `<commit-ish>` in their ancestry/history.
- **`git branch -a --contains <commit-ish>`**: Lists both local and remote-tracking branches containing `<commit-ish>`.

---

## 2. Reproducible Repository Setup

To demonstrate branch containment deterministically, a temporary repository is constructed with branch `main`, author `Course Student <student@example.invalid>`, and a local bare remote using a `file://` URL:

```sh
# 1. Initialize local bare remote repository
mkdir remote_repo.git && cd remote_repo.git
git init --bare
cd ..

# 2. Initialize working repository with branch main
mkdir local_repo && cd local_repo
git init -b main
git config user.name "Course Student"
git config user.email "student@example.invalid"

# 3. Commit A: create notes.txt containing alpha
echo "alpha" > notes.txt
git add notes.txt
git commit -m "Commit A: create notes.txt with alpha"

# 4. Commit B: append beta to notes.txt
echo "beta" >> notes.txt
git add notes.txt
git commit -m "Commit B: append beta to notes.txt"

# 5. Create branch topic at commit B
git branch topic

# 6. Commit C: create todo.txt containing one
echo "one" > todo.txt
git add todo.txt
git commit -m "Commit C: create todo.txt with one"

# 7. Add local bare remote via file:// and push branches
git remote add origin file://$(pwd)/../remote_repo.git
git push origin main topic
```

---

## 3. Dynamic Git Object IDs & Containment Results

All hashes are captured dynamically via `git rev-parse`:

| Entity | Hash | Description | Contained In Branches |
| :--- | :--- | :--- | :--- |
| **Commit A** | `689c20134f3ef9f49a54500751f8b48042a1f4d8` | Created `notes.txt` (`alpha\n`) | `main`, `topic`, `remotes/origin/main`, `remotes/origin/topic` |
| **Commit B** | `4c564ef0dcc07580a68222b120ce5c357d7686bd` | Appended `beta\n`; base of `topic` | `main`, `topic`, `remotes/origin/main`, `remotes/origin/topic` |
| **Commit C** | `c8e864d86b97b97653b54c73423a1647e54d8eb3` | Created `todo.txt` (`one\n`) | `main`, `remotes/origin/main` |

### Containment Output Verification:

```sh
# Checking Commit A (ancestor of both topic and main):
git branch --contains 689c20134f3ef9f49a54500751f8b48042a1f4d8
# Output:
# * main
#   topic

# Checking Commit B (head of topic, parent of main):
git branch --contains 4c564ef0dcc07580a68222b120ce5c357d7686bd
# Output:
# * main
#   topic

# Checking Commit C (tip of main only):
git branch --contains c8e864d86b97b97653b54c73423a1647e54d8eb3
# Output:
# * main

# Checking Commit C across all branches (local + remote):
git branch -a --contains c8e864d86b97b97653b54c73423a1647e54d8eb3
# Output:
# * main
#   remotes/origin/main
```

---

## 4. Reversible Mistake & Recovery Guide

When managing branches using containment inspection, two common mistakes occur:
1. Accidental branch deletion (e.g. running `git branch -D topic` thinking it was fully merged).
2. Accidental hard reset (e.g. running `git reset --hard` to an earlier commit hash).

### Scenario 1: Accidental Branch Deletion

#### Mistake:
```sh
git branch -D topic
# Output: Deleted branch topic (was 4c564ef).
```

#### Recovery:
1. **Recovery Point**: The commit hash `4c564ef0dcc07580a68222b120ce5c357d7686bd` recorded in the deletion confirmation or `git reflog`.
2. **Commands Used**:
   ```sh
   git branch topic 4c564ef0dcc07580a68222b120ce5c357d7686bd
   ```
3. **Verification Steps**:
   ```sh
   git rev-parse topic
   # Output: 4c564ef0dcc07580a68222b120ce5c357d7686bd
   git rev-parse topic^{tree}
   # Output: f85b72cccab2aab0cfca333f78ab1ff302be5f7b
   ```

---

### Scenario 2: Accidental Hard Reset

#### Mistake:
```sh
git reset --hard 689c20134f3ef9f49a54500751f8b48042a1f4d8
# Output: HEAD is now at 689c201 Commit A: create notes.txt with alpha
# Notice: todo.txt is now missing from the working tree!
```

#### Recovery:
1. **Recovery Point**: Inspect `git reflog` to identify the pre-reset position (`HEAD@{1}` or commit `c8e864d86b97b97653b54c73423a1647e54d8eb3`):
   ```sh
   git reflog -n 5
   # c8e864d HEAD@{1}: commit: Commit C: create todo.txt with one
   ```
2. **Commands Used**:
   ```sh
   git reset --hard HEAD@{1}
   ```
3. **Verification Steps**:
   ```sh
   git rev-parse HEAD
   # Output: c8e864d86b97b97653b54c73423a1647e54d8eb3
   git rev-parse HEAD^{tree}
   # Output: 70d571a7a75867c09d38254b1252d5e2402adaa6
   test -f todo.txt && echo "todo.txt restored"
   git status --short
   # Working tree clean
   ```

---

## 5. What Can and Cannot Be Recovered

### What CAN be recovered:
- **Committed Snapshots**: Any commit created in the local repository remains stored in `.git/objects` and reachable through `git reflog`.
- **Branch Pointers**: A deleted branch can be instantly recovered as long as its tip commit hash is known or found in `git reflog`.
- **Reset Commits**: A commit discarded by `git reset --hard` can be recovered using the reflog pointer (`HEAD@{n}`).
- **Complete Tree State**: File contents, directory structures, and tree hashes of committed revisions are fully restorable.

### What CANNOT be recovered:
- **Uncommitted Modifications**: Changes in the working directory or staging area that were never committed prior to a destructive command (like `git reset --hard` or `git checkout -- <file>`) are permanently wiped out.
- **Expired Reflogs**: `git reflog` entries expire after a grace period (default 90 days for reachable commits, 30 days for unreachable commits). Once expired and pruned by `git gc` or `git prune`, unreferenced commits cannot be recovered.
- **Unfetched Remote Commits**: Commits created on other developers' machines or remote branches that were never fetched to your local repository.

---

## 6. Automated Verification

Run the checker script to verify all facts independently:

```sh
python3 work/R11-T033/check.py
```
