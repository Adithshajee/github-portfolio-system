### 🤗 Hugging Face Portfolio

📊 **{{ data.total_downloads }}** total downloads · ❤️ **{{ data.total_likes }}** total likes

**Models:**
{% for model in data.models %}
- **[{{ model.display_name }}]({{ model.url }})** — 🔽 `{{ model.downloads }}` | ❤️ `{{ model.likes }}`
{% endfor %}

**Spaces:**
{% for space in data.spaces %}
- **[{{ space.space_id.split('/')[-1] }}]({{ space.url }})** — ❤️ `{{ space.likes }}`
{% endfor %}
