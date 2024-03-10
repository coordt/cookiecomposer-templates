---
title: {{ cookiecutter.project_name }}
summary: {{ cookiecutter.project_short_description }}
date: {% now 'local', '%Y-%m-%d' %}
comments: true
---

# {{ cookiecutter.friendly_name }}

{%raw%}{% 
    include-markdown 
    "../README.md" 
    start="<!--start-->" 
    end="<!--end-->"
    rewrite-relative-urls=false
%}{%endraw%}
