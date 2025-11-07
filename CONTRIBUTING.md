# Contributing to Threat Hunting Playbooks

Thanks for your interest in improving the project! This guide explains how to get set up, propose changes, and collaborate with the community.

## 1. Get Set Up

1. **Fork** the repository and clone your fork.
2. Install dependencies:
   ```bash
   cd threat-hunting-playbooks/ui && npm install && cd ..
   cd api && pip install -e .[dev] && cd ..
   ```
3. Launch the stack for end-to-end verification:
   ```bash
   docker compose up --build
   ```

## 2. Pick an Issue

- Browse the [issue tracker](https://github.com/sr-857/threat-hunting-playbooks/issues) for `good first issue` or `help wanted` labels.
- If you have a new idea, open a GitHub Discussion or issue first so we can align on scope.

## 3. Create a Branch

Use a descriptive name such as `feature/linux-hunt` or `fix/auth-refresh`.

```bash
git checkout -b feature/your-change
```

## 4. Develop & Test

- **Backend**: run `pytest` from the `api/` directory.
- **Frontend**: run `npm run lint` from the `ui/` directory.
- **Docs**: keep screenshots and Markdown in `docs/`. Reference assets with relative paths.
- Ensure CI workflows (`api-tests`, `ui-lint`) pass locally before pushing.

### Coding Guidelines

- Follow existing code style and lint configurations (`ruff`, ESLint).
- Keep changes focused. Separate unrelated fixes into distinct PRs.
- Add or update tests when fixing bugs or adding features.
- Include doc updates when behaviour changes.

## 5. Write Commit Messages

Use concise, present-tense messages, e.g., `Add cron persistence hunt for Linux`. Squash WIP commits before opening a PR if needed.

## 6. Open a Pull Request

- Target the `main` branch.
- Fill in the PR template with context, testing evidence, and screenshots (if UI work).
- Link related issues with `Fixes #<issue-number>` so they close automatically on merge.

## 7. Respond to Reviews

- Address reviewer feedback promptly.
- Use GitHub’s “Resolve conversation” once comments are applied.
- If disagreements arise, propose alternatives in the discussion.

## 8. Celebrate & Iterate

Once merged, update any follow-on tasks in the issue tracker and share highlights in Discussions. Repeat with the next idea!

---

### Community Channels

- **Discussions**: questions, ideas, design proposals.
- **Issues**: actionable bugs and feature requests.
- **Security**: report vulnerabilities privately via `SECURITY.md`.

We’re excited to build the hunting platform with you—thanks for contributing!
