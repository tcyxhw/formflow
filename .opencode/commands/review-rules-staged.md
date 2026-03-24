---
description: Review staged changes against repository standards before commit
agent: rule-reviewer
subtask: true
---

Review the staged repository changes against repository standards.

## Worktree status
!`git status --short`

## Staged diff
!`git diff --cached -- .`

Also read:
@standards/09_review_prompt.md
@standards/08_review_checklist.md

Focus on:
1. staged changes only
2. compliance with repository standards
3. risks introduced by the staged changes
4. whether any existing rule is too weak, too strong, or missing

Output exactly in the structure required by @standards/09_review_prompt.md.
If there are no staged code changes, say that explicitly.
