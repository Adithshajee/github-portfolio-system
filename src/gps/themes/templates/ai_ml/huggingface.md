### 🧠 Hugging Face Hub (AI/ML Models & Spaces)

🤖 **{{ data.total_downloads }}** total model inference downloads · ⚡ **{{ data.total_likes }}** community stars

**Deployed Spaces:**
{% for space in data.spaces %}
- **[{{ space.space_id.split('/')[-1] }}]({{ space.url }})** `{{ space.sdk }}` — ⭐ `{{ space.likes }}`
{% endfor %}

**Inference Models:**
{% for model in data.models %}
- **[{{ model.display_name }}]({{ model.url }})** {% if model.pipeline_tag %}`[{{ model.pipeline_tag }}]`{% endif %} — 🔽 `{{ model.downloads }}` downloads
{% endfor %}
