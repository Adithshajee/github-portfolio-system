# GitHub Provider

The GitHub provider is active by default. It parses user profile data using GitHub REST v3 API and pinned repositories using GitHub GraphQL v4 API.

## Configuration

Enable or tune options in your `gps.yml` file:

```yaml
providers:
  github:
    enabled: true
    repo_count: 5
    include_pinned: true
    exclude_forks: true
    exclude_archived: true
```

## Secrets

To fetch pinned repositories via GraphQL or prevent API rate limits, set the `GH_PAT` environment variable with a Personal Access Token:

```bash
export GH_PAT=ghp_your_token_value
```
