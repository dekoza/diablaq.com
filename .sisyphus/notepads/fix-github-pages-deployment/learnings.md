## Task 2 Learnings: API Switch to Workflow Mode

### GitHub Pages API Behavior
- **HTTP 204 No Content is success**: The PUT endpoint returns 204 with empty body on success. This is NOT an error — it's the expected response.
- **Omitting `source` field is critical**: The request must only include `build_type=workflow`, not a `source` field. Including both can cause validation errors.
- **Silent success requires explicit verification**: Since the PUT returns no JSON body, we must verify the change with a separate GET request to confirm the switch.

### Verified Workflow
1. Switch API call: `gh api -X PUT repos/{owner}/{repo}/pages -F build_type=workflow`
2. Verify with three checks:
   - `build_type` via `.build_type` jq filter
   - Custom domain via `.cname` jq filter
   - HTTPS enforcement via `.https_enforced` jq filter
3. All three checks must pass before proceeding to file cleanup (Task 3)

### Root Cause Verification
- Legacy mode (`build_type: "legacy"`) served raw files from gh-pages root
- Workflow mode (`build_type: "workflow"`) serves only GitHub Actions artifacts
- This switch eliminates the race condition between raw files and built artifacts
