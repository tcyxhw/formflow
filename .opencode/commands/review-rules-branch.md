---
description: Review all branch changes against a specified base branch before push
agent: rule-reviewer
subtask: true
---

Review the current branch changes against the specified base branch before push.

The base branch/ref is: $ARGUMENTS

Use the merge-base diff as the primary review target.

## Worktree status
!`git status --short`

## Branch diff against base
!`git diff $ARGUMENTS...HEAD -- .`

## Commit summary on this branch relative to base
!`git log --oneline $ARGUMENTS..HEAD`

Also read:
@standards/09_review_prompt.md
@standards/08_review_checklist.md

Focus on:
1. the complete branch delta against $ARGUMENTS
2. compliance with repository standards
3. structural risks across the whole feature branch
4. whether any existing rule is too weak, too strong, or missing

Output exactly in the structure required by @standards/09_review_prompt.md.
If there are no meaningful branch changes against $ARGUMENTS, say that explicitly.
