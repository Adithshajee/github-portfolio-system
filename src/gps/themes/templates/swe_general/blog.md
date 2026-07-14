### ✍️ {{ data.title or 'Recent Blog Posts' }}

{% for post in data.posts %}
- **[{{ post.title }}]({{ post.link }})**{% if post.pub_date %} *({{ post.pub_date }})*{% endif %}
{% endfor %}
