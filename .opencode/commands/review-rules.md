---
description: Review current worktree against repository standards
agent: rule-reviewer
subtask: true
---

Review the current repository changes against repository standards.

Use the following repository evidence as the primary review target.

## Worktree status
!`git status --short`

## Unstaged diff
!`git diff -- .`

## Staged diff
!`git diff --cached -- .`

Also read:
@standards/09_review_prompt.md
@standards/08_review_checklist.md

Focus on:
1. current worktree changes
2. the latest task in this conversation
3. compliance with repository standards
4. risks introduced by the current changes
5. whether any existing rule is too weak, too strong, or missing

Output exactly in the structure required by @standards/09_review_prompt.md.
If there are no meaningful code changes, say that explicitly.
