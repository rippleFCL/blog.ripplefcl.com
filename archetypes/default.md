---
date: '{{ .Date }}'
draft: False
title: '{{ replace .File.ContentBaseName "-" " " | title }}'
Description: 'set description'
params:
    image: 'header.png'
    tags:
        - 'replace_tag'
---
