---
name: plugin-maker
description: Scaffold a new Miri web plugin under plugins/<id>/ — manifest.json, static assets, nav item, and the 3 path pitfalls that bite every first-time plugin author.
triggers: [plugin, new plugin, web plugin, scaffold plugin, plugins/, manifest.json]
---

# Plugin Maker — build a Miri web plugin in one pass

Miri auto-discovers any folder under `plugins/` that contains a
`manifest.json`. The loader is `agent_miri/web_plugin_registry.py`
(`WebPluginRegistry.from_workspace(cwd)`); routes are added to the HTTP
router in `agent_miri/miri_web.py`, and nav items are returned by
`/api/plugins/nav` (rendered by the chat UI).

## 1. Directory layout

```
plugins/
  <plugin-id>/
    manifest.json              ← required; lowercase, kebab-case id
    static/
      index.html               ← whatever your plugin serves
      index.js
      index.css                (optional)
```

Nothing outside `plugins/<plugin-id>/` is part of the plugin.
Asset filenames are yours to pick — just keep them inside `static/`.

## 2. manifest.json — minimal working example

```json
{
  "id": "hello-world",
  "name": "Hello World",
  "version": "1.0",
  "description": "Demonstrates the smallest possible Miri web plugin.",
  "nav_items": [
    {
      "label": "Hello",
      "route": "/hello",
      "icon": "\ud83d\udc4b",
      "title": "Open the Hello World panel"
    }
  ],
  "routes": {
    "/hello":      "static/index.html",
    "/hello.html": "static/index.html"
  }
}
```

Field rules:
- `id`, `name` — required. Any dict missing either is silently dropped.
- `routes` values are **relative to the plugin folder**, not to cwd.
  The loader resolves them with `(plugin_dir / static_rel).resolve()`
  and stores the **absolute** path in the route table.
- `nav_items[*]` must have both `label` and `route`; others are skipped.
- Only routes whose target file exists at load time are registered.
  A typo in the path silently drops the route — no warning at startup.

## 3. Three path pitfalls that bite every first-time plugin author

These are the real failure modes observed in this repo. Check them before
declaring the plugin "done":

### 3a. `<script src>` pointing at a non-plugin URL

`_serve_static()` in `miri_web.py` serves from **workspace root**
(`cwd / rel_path`). The plugin route table only resolves the exact
routes listed in `manifest.json`. So a tag like:

```html
<!-- WRONG: server looks under <cwd>/static/foo/bar.js, which does not exist -->
<script src="/static/foo/bar.js"></script>
```

…falls through to `_serve_static("static/foo/bar.js")` and 404s.
The fix is to use a workspace-rooted path that points at the real
location, or to declare a route for it in the manifest.

```html
<!-- RIGHT: matches the file on disk -->
<script src="/plugins/hello-world/static/index.js"></script>
```

Either approach works (static fall-through serves any file under cwd,
plugin routes resolve declared paths first).

### 3b. Relative fetches that assume a different base URL

Client JS that does `fetch('data/foo.json')` resolves relative to
the **current page URL**, which is your plugin route (e.g. `/hello`),
not to the plugin folder. Prefer absolute paths:

```js
// Absolute — always hits the workspace root, predictable
const resp = await fetch('/plugins/hello-world/static/data/foo.json');
```

### 3c. Forgetting to cache-bust during iteration

`_serve_static()` caches file contents in-memory on first read. If you
edit `index.js` and the browser still sees the old file, hit the
`/api/reload` endpoint (POST) or the "Reload UI" button if your
plugin exposes one — that clears `server._static_cache`.

## 4. Security model — what you inherit for free

- Directory traversal is blocked: `_serve_file()` refuses any resolved
  path that does not start with `cwd`. `..` in a URL can't escape the
  workspace.
- MIME types are auto-detected by extension (html/css/js/json/md/png/
  jpg/gif/svg/webp). Anything else is sent as
  `application/octet-stream`.
- CORS is permissive (`Access-Control-Allow-Origin: *`). The server is
  meant to be localhost-only; do not expose it to the network without
  tightening this.

## 5. Step-by-step when the user asks for a new plugin

1. Pick a kebab-case `id` (e.g. `quick-notes`). Confirm with the user.
2. `mkdir -p plugins/<id>/static`
3. Write `plugins/<id>/manifest.json` using the template above,
   substituting `id`, `name`, `description`, one `nav_items` entry,
   and at least the primary route (`/<id>`).
4. Write `plugins/<id>/static/index.html`. Every `<script>` and
   `<link>` tag must use an **absolute** `/plugins/<id>/static/...`
   URL. Re-read section 3a if tempted to write `/static/...`.
5. Write `plugins/<id>/static/index.js`. All `fetch(...)` calls use
   absolute paths (section 3b).
6. Verify: restart Miri (or refresh and POST `/api/reload`), GET
   `/api/plugins/nav` — the new item must appear. Click it; the page
   loads; open devtools Network tab and confirm no 404s on the
   static assets.
7. If anything 404s, `grep -n 'src=\\|href=\\|fetch(' plugins/<id>/static/*`
   and fix absolute paths.

## 6. When NOT to use a web plugin

Web plugins only expose **UI**. They cannot add LLM tool-calls, alter
the system prompt, or run Python on the server. For those, use:

- **Agent-side plugin** (`.miri-plugin/plugin.json`) — adds tool
  aliases, virtual tools, hooks, and prompt injection. See
  `agent_miri/plugin_runtime.py`.
- **User tool** (`miri_profile/tools/<name>.json`) — declarative
  shell-command tool, gated by `--allow-shell`.
- **User skill** (`miri_profile/skills/<name>/SKILL.md`) — loaded on
  demand via the built-in `use_skill` tool.

A web plugin is the right choice when the user wants a **page in the
browser** (dashboard, reader, form) backed by existing HTTP endpoints.

# RULES
1. Plugin `id` must be lowercase kebab-case.
2. All `<script src>` and `<link href>` tags MUST use absolute paths starting with `/plugins/<id>/static/`.
3. All `fetch()` calls in JS MUST use absolute paths — never relative URLs.
4. `manifest.json` must contain both `id` and `name` fields — omission silently drops the plugin.
5. Only declare routes whose target files actually exist on disk.

# REQUIRED TOOLS
- write_file (for creating manifest.json, index.html, index.js, index.css)
- bash (for mkdir and verification)

# VALIDATION
Before completing this work, you MUST verify:
- `manifest.json` is valid JSON with `id` and `name` fields
- All routes in `manifest.json` point to files that exist on disk
- All `<script src>` and `<link href>` use absolute `/plugins/<id>/static/...` paths
- No relative `fetch()` calls exist in the JS files
- GET `/api/plugins/nav` returns the new nav item after reload
