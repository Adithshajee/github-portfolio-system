# Hugging Face Provider

The Hugging Face provider fetches model cards, spaces, and datasets owned by the configured user.

## Configuration

Enable it in your `gps.yml` file:

```yaml
providers:
  huggingface:
    enabled: true
    username: "your-hf-username"
    model_count: 5
    space_count: 3
```

## Secrets

Provide `HF_TOKEN` environment variable for authenticated access or to view private models:

```bash
export HF_TOKEN=hf_your_token_value
```
