# Assets Guide

This guide details instructions for creating, configuring, and updating visual assets for your GitHub Profile and repository pages.

---

## 1. Profile Banners

Your main profile banner should span across the top of your GitHub Profile README.

*   **Optimal Aspect Ratio**: `3:1`
*   **Optimal Resolution**: `1200 x 400` pixels.
*   **Design Rule**: Keep the left portion clean or low contrast to prevent overlap with the round avatar on mobile screens.

---

## 2. Light / Dark Mode SVG Theme Compatibility

GitHub allows rendering different SVGs depending on whether the user is viewing the page in light or dark mode. Use the HTML `<picture>` tag:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/profile-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/profile-light.svg">
  <img alt="Personal Banner" src="assets/profile-light.svg">
</picture>
```

---

## 3. Banner Structure

A cohesive layout for a portfolio header:
- **Title**: Adith Shajee
- **Subtitle**: AI & Computer Vision Engineering
- **Accent Elements**: Subtle node/network graphs, code metrics, or low-opacity grid lines.
