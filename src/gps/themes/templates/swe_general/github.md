### 📂 Active Projects & Repositories

{% for repo in data.repos %}
- **[{{ repo.name }}]({{ repo.html_url }})** — *Updated {{ repo.updated_date if repo.updated_date else 'today' }}*
  > {{ repo.display_description or 'No description provided.' }}
  > 🌟 `{{ repo.stargazers_count }}` | 🍴 `{{ repo.forks_count }}`
{% endfor %}
