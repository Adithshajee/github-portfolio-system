# Deployment Guide

This guide details how to host and deploy the GitHub Portfolio System documentation site via GitHub Pages.

---

## 1. Local Preview

Before deploying, always test the site layout locally:

```bash
# Start local MkDocs dev server
mkdocs serve
```

Once running, navigate to `http://127.0.0.1:8000` in your web browser to check pages, navigation, search capabilities, and CSS styles.

---

## 2. GitHub Pages Deployment

We use a automated GitHub Actions workflow to compile the site and push it to the `gh-pages` branch. 

### Automated Workflow Configuration
The release and deployment action performs the following steps:
1.  Checks out the code.
2.  Sets up Python environment.
3.  Installs dependencies (`mkdocs` and `mkdocs-material`).
4.  Builds the static site using `mkdocs build`.
5.  Deploys the static assets to the `gh-pages` branch.

### Manual Branch Deployment
If you prefer to deploy manually from your terminal, execute:

```bash
mkdocs gh-deploy --clean
```

---

## 3. Configuring Repository Settings

To ensure the site resolves correctly on GitHub:
1.  Go to the repository on GitHub.
2.  Click on **Settings** > **Pages** (in the sidebar).
3.  Set the **Source** to `Deploy from a branch`.
4.  Choose the branch `gh-pages` and folder `/ (root)`.
5.  Save your changes. The site will be available shortly at `https://<your-username>.github.io/github-portfolio-system/`.
