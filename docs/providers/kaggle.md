# Kaggle Provider

The Kaggle provider integration utilizes the official Kaggle API package to aggregate public competitions, notebooks, and dataset profiles.

## Configuration

Enable it in your `gps.yml` file:

```yaml
providers:
  kaggle:
    enabled: true
    username: "your-kaggle-username"
```

## Secrets

Requires your API Credentials loaded in the environment:

```bash
export KAGGLE_USERNAME="your-kaggle-username"
export KAGGLE_KEY="your-kaggle-api-key"
```
