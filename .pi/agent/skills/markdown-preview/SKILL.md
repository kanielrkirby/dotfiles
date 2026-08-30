---
name: markdown-preview
description: Render Markdown as styled HTML and open it in the default browser
---

# Markdown preview

Run `~/dev/lab/markdown-preview/render-markdown.sh INPUT.md [OUTPUT.html]`. The renderer lives in `~/dev/lab/markdown-preview/`. Without output path, HTML goes to `/tmp/markdown-preview/<random>.html`.

It uses Pandoc with GFM, built-in syntax highlighting, local CSS, and browser-side Mermaid. If no output path is supplied, it writes a random HTML file under `/tmp/markdown-preview/` and opens it with `xdg-open`.

Example:

```sh
~/dev/lab/markdown-preview/render-markdown.sh /tmp/hd-1888-pr-body.md
```

Requirements: `pandoc`, `xdg-open`, and browser network access for Mermaid diagrams. Mermaid blocks must use `mermaid` as fence language:

````markdown
```mermaid
graph TD
  A --> B
```
````
