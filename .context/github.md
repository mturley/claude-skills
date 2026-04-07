# GitHub API - Context for AI Agents

Read this file before interacting with the GitHub API via `gh` CLI.

## WIP PRs

When marking a PR as Work In Progress, use brackets in the title: `[WIP] PR title here`. Do not use `WIP:` prefix.

## Creating Pending PR Reviews with Inline Comments

The REST API (`gh api repos/{owner}/{repo}/pulls/{number}/reviews`) has quirks with inline comments. Use the **GraphQL API** instead for reliable multi-line, line-anchored review comments.

### What doesn't work (REST API)

- `event: "PENDING"` is **not a valid value** for the `event` field on review creation. Omit `event` entirely to create a pending review.
- Comments passed in the `comments` array on the REST create-review endpoint often **silently fail to anchor to lines** — they get created as file-level comments instead.
- The `subject_type`, `start_side`, and `side` fields are **not accepted** in the `comments` array of the create-review endpoint (despite being documented for the individual comment endpoint).
- The `pull_request_review_id` field is **not accepted** on the create-comment endpoint (`POST /pulls/{number}/comments`).

### What works: GraphQL `addPullRequestReview` mutation

Use variables for comment bodies to avoid escaping issues in the query string.

```bash
# 1. Get the PR node ID
PR_NODE_ID=$(gh api repos/{owner}/{repo}/pulls/{number} --jq '.node_id')

# 2. Write the mutation to a file (avoids shell escaping problems)
cat <<'EOF' > /tmp/review_mutation.graphql
mutation($prId: ID!, $body1: String!, $body2: String!) {
  addPullRequestReview(input: {
    pullRequestId: $prId
    threads: [
      {
        path: "src/example/File.tsx"
        body: $body1
        startLine: 10
        line: 20
        side: RIGHT
        startSide: RIGHT
      },
      {
        path: "src/example/OtherFile.ts"
        body: $body2
        line: 5
        side: RIGHT
      }
    ]
  }) {
    pullRequestReview {
      id
      state
    }
  }
}
EOF

# 3. Call with variables for the bodies
gh api graphql \
  -f query="$(cat /tmp/review_mutation.graphql)" \
  -f "prId=$PR_NODE_ID" \
  -f 'body1=First review comment text here.' \
  -f 'body2=Second review comment text here.'
```

### Key details

- **Multi-line comments**: Use both `startLine` and `line`. For single-line, just use `line`.
- **Side**: Use `RIGHT` for comments on the new version of the file (most common). Use `LEFT` for the old version.
- **Pending state**: The review is created in `PENDING` state by default. The author can submit it from the GitHub UI, or you can submit it via a separate `submitPullRequestReview` mutation.
- **Line numbers must be within the diff**: The `line` and `startLine` values must reference lines that appear in the PR diff. Comments on unchanged lines will fail.

## `gh pr checks --json` Fields

The `--json` flag on `gh pr checks` supports a **different set of fields** than you might expect. There is no `conclusion` field — use `state` instead.

**Available fields:** `bucket`, `completedAt`, `description`, `event`, `link`, `name`, `startedAt`, `state`, `workflow`

**`state` values:** `SUCCESS`, `FAILURE`, `PENDING`, `QUEUED`, `IN_PROGRESS`, `SKIPPING`, `STARTUP_FAILURE`, `STALE`, `WAITING`

**Example — get structured check results:**
```bash
gh pr checks 123 --json name,state,link --jq '.[] | select(.state == "FAILURE")'
```

**Without `--json`:** The default tabular output uses columns: `name`, `status` (pass/fail/pending/skipping), `elapsed`, `link`. Parse with `grep` for simple checks.

### Deleting a pending review (if needed)

```bash
# REST API works fine for deletion
gh api repos/{owner}/{repo}/pulls/{number}/reviews/{review_id} --method DELETE
```

### Verifying comments on a pending review

```bash
gh api repos/{owner}/{repo}/pulls/{number}/reviews/{review_id}/comments \
  --jq '[.[] | {path: .path, line: .line, body: .body[:80]}]'
```
