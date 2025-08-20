---
mode: agent
description: Review changes in the git worktree and make a commit with appropriate staging and messaging.
---

**Task Definition:**
Review the current changes in this git worktree and make a commit with appropriate staging and messaging.

**Requirements:**
- Analyze all modified, added, and deleted files
- Review actual code/content changes through diffs
- Generate appropriate commit message following conventional commit format
- Stage and commit appropriate changes

**Constraints:**
- Only commit changes that are ready and coherent
- Exclude any files that shouldn't be committed (temporary files, secrets, etc.)
- Follow conventional commit practices
- Ensure commit message accurately reflects the changes
  - The type should be chosen based on the nature of the changes (e.g., feat, fix, docs, style, refactor, test, chore)
  - The body should provide additional context if necessary
  - An optional footer can be included for co-authors or issue references
- Ask for clarification on ambiguous or potentially problematic changes

**Success Criteria:**
- All appropriate changes are staged and committed
- Commit message is clear, descriptive, and follows good practices
- No inappropriate files are included in the commit
- Repository is left in a clean, consistent state

**Process Steps:**

1. **Analyze the current state:**
   - Check what files have been modified, added, or deleted
   - Review the actual changes (diffs) to understand what was modified
   - Identify any staged vs unstaged changes

2. **Review the changes:**
   - Summarize what changes were made and why they might be significant
   - Check for any obvious issues, inconsistencies, or potential problems
   - Verify that the changes align with good coding practices for this project type

3. **Prepare for commit:**
   - Suggest whether all changes should be included or if some should be staged separately
   - If there are unstaged changes, advise whether to stage them
   - Recommend if any files should be excluded from the commit

4. **Generate commit message:**
   - Create a clear, descriptive commit message following conventional commit format
   - Include both a concise summary and detailed description if needed
   - Ensure the message accurately reflects the scope and impact of changes

5. **Execute the commit:**
   - Stage the appropriate files if needed
   - Make the commit with the generated message
   - Confirm the commit was successful


**Commit Message Format:**
```<type>(<scope>): <subject>

<body>

<optional_footer>
```

**Types (in order of preference):**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code change that neither fixes bug nor adds feature
- `test`: Adding missing tests
- `chore`: Changes to build process or auxiliary tools

**Example Commit Messages:**
```feat: Implement new feature X

- Added functionality to handle feature X
- Updated documentation to reflect changes
- Fixed minor bugs related to feature X

Co-Authored-By: Contributor
```

```fix: Resolve issue with Y

- Fixed bug causing Y to fail under certain conditions
- Added unit tests to cover the fix
```

```feat(tests): Add unit tests for feature Z 

- Implemented unit tests for feature Z
- Ensured all tests pass successfully
- Updated test documentation
- Added additional test cases for edge scenarios
```

Please be thorough in your review and ask for clarification if any changes seem unclear or potentially problematic before proceeding with the commit.