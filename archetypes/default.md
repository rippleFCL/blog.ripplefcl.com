---
date: '{{ .Date }}'
draft: False
title: '{{ replace .File.ContentBaseName "-" " " | title }}'
params:
    image: header.png
    tags:
        - replace_tag
---
