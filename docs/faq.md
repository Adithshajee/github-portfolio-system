# Frequently Asked Questions (FAQ)

### Q: Why is my profile README not updating?
- Ensure the start/end markers `<!-- REPOS_START -->` and `<!-- REPOS_END -->` exist in your README.
- Check that the `readme_path` in `gps.yml` matches your file location.
- Verify `GH_PAT` token is loaded in the terminal or action environment.

### Q: How can I change the number of repositories listed?
Modify `providers.github.repo_count` inside `gps.yml`:

```yaml
providers:
  github:
    enabled: true
    repo_count: 10
```
