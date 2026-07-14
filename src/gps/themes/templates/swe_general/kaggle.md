### 🏆 Kaggle Portfolio

{% if data.tier %}
**Tier:** {{ data.tier }}
{% endif %}

**Notebooks:**
{% for nb in data.notebooks[:5] %}
- **[{{ nb.title }}]({{ nb.notebook_url }})** — 🗳️ `{{ nb.votes }}` votes
{% endfor %}

**Competitions:**
{% for comp in data.competitions[:5] %}
- **[{{ comp.title }}]({{ comp.competition_url }})**
{% endfor %}
