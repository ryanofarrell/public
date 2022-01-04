---
permalink: /mindmap/
title: Mind Map
collection: mindmap
entries_layout: grid
layout: search

---

# test

{% for concept in site.mindmap %}
  {% include mindmap-link url=concept.url text=concept.title %}

  {{ concept.url }}


{% endfor %}

{% for concept in site.data.mindmap %}
  {{ concept.title }}
{% endfor %}