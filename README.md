# xiaohongshu-cli

小红书 CLI — 通过逆向 API 在终端操作小红书 📕

## 推荐项目

- [bilibili-cli](https://github.com/jackwener/bilibili-cli) — Bilibili CLI
- [twitter-cli](https://github.com/jackwener/twitter-cli) — Twitter/X CLI

## Features

- 🔐 **Auth** — auto-extract browser cookies, status, whoami
- 🔍 **Search** — notes by keyword, user search, topic search
- 📖 **Reading** — note detail, comments, sub-comments, user profiles
- 📰 **Feed** — recommendation feed, hot/trending by category
- 👥 **Social** — follow/unfollow, favorites
- 👍 **Interactions** — like, favorite, comment, reply, delete
- ✍️ **Creator** — post image notes, my-notes list, experimental delete
- 🔔 **Notifications** — unread count, mentions, likes, new followers
- 📊 **Structured output** — commands support `--yaml` and `--json`; non-TTY stdout defaults to YAML
- 📦 **Stable envelope** — see [SCHEMA.md](./SCHEMA.md) for `ok/schema_version/data/error`

## Installation

```bash
# From source
git clone git@github.com:jackwener/xiaohongshu-cli.git
cd xiaohongshu-cli
uv sync

# Or: pip install
pip install -e .
```

## Usage

```bash
# ─── Auth ─────────────────────────────────────────
xhs login                             # Extract cookies from browser
xhs status                            # Check login status
xhs whoami                            # Detailed profile (fans, likes, etc)
xhs whoami --json                     # Structured JSON envelope
xhs logout                            # Clear saved cookies
xhs logout --yaml                     # Structured success envelope

# ─── Search ───────────────────────────────────────
xhs search "美食"                      # Search notes
xhs search "旅行" --sort popular       # Sort: general, popular, latest
xhs search "穿搭" --type video         # Filter: all, video, image
xhs search "AI" --page 2              # Pagination
xhs search-user "用户名"               # Search users
xhs topics "美食"                      # Search hashtags/topics

# ─── Reading ──────────────────────────────────────
xhs read <note_id>                     # Read a note
xhs read https://xiaohongshu.com/...   # Read by URL
xhs comments <note_id>                 # View comments
xhs sub-comments <note_id> <cmt_id>   # View replies to a comment
xhs user <user_id>                     # User profile
xhs user-posts <user_id>              # User's published notes
xhs user-posts <user_id> --cursor X   # Paginate with cursor

# ─── Feed & Discovery ────────────────────────────
xhs feed                              # Recommendation feed
xhs hot                               # Hot notes (default: food)
xhs hot -c fashion                    # Categories: fashion, food, cosmetics,
                                      #   movie, career, love, home, gaming,
                                      #   travel, fitness

# ─── Social ───────────────────────────────────────
xhs favorites <user_id>                # User's bookmarked notes
xhs follow <user_id>                  # Follow a user
xhs unfollow <user_id>                # Unfollow a user

# ─── Interactions ─────────────────────────────────
xhs like <note_id>                     # Like a note
xhs like <note_id> --undo             # Unlike
xhs favorite <note_id>                 # Favorite (bookmark)
xhs unfavorite <note_id>               # Unfavorite
xhs comment <note_id> -c "好赞！"     # Post comment
xhs reply <note_id> --comment-id X -c "回复"  # Reply to comment
xhs delete-comment <note_id> <cmt_id> # Delete own comment

# ─── Creator ─────────────────────────────────────
xhs my-notes                           # List own notes (v2 creator endpoint)
xhs my-notes --page 1                 # Next page
xhs post --title "标题" --body "正文" --images img.jpg  # Post note
xhs delete <note_id>                   # Experimental: delete note
xhs delete <note_id> -y               # Skip confirmation

# ─── Notifications ────────────────────────────────
xhs unread                             # Unread counts (likes, mentions, follows)
xhs notifications                      # 评论和@ notifications
xhs notifications --type likes        # 赞和收藏 notifications
xhs notifications --type connections   # 新增关注 notifications
```

## Authentication

xiaohongshu-cli uses a 2-tier authentication strategy:

1. **Saved cookies** — loads from `~/.xiaohongshu-cli/cookies.json`
2. **Browser cookies** — auto-extracts from Chrome, Firefox, Safari, Edge, Brave

`xhs login` always refreshes cookies from the selected browser and overwrites the local cache.
Other authenticated commands automatically retry once with fresh browser cookies when the saved session has expired.

Most commands require authentication. Use `--cookie-source` to specify browser (default: chrome; also supports firefox, edge, safari, brave).

### Cookie TTL

Saved cookies are valid for **7 days** by default. After that, the client automatically attempts to refresh from the browser. If browser extraction fails, the existing cookies are used with a warning.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OUTPUT` | `auto` | Output format: `json`, `yaml`, `rich`, or `auto` (→ YAML when non-TTY) |
| `XHS_COOKIE_SOURCE` | `chrome` | Default browser for cookie extraction |

## Rate Limiting & Anti-Detection

xiaohongshu-cli includes built-in rate-limit protection and anti-detection:

- **Request delay**: 1 second minimum between consecutive API calls (with random jitter)
- **Auto-retry**: Automatically retries on HTTP 429/5xx and network errors (up to 3 times, exponential backoff)
- **Browser fingerprint**: Sends `sec-ch-ua`, `sec-fetch-*`, and `accept-language` headers matching Edge 142
- **Signed requests**: All API calls use `x-s` / `x-t` signatures (reverse-engineered from web client)

## AI Agent Integration

All commands support `--json` and `--yaml` flags for structured output. When `stdout` is not a TTY (e.g., piped to another program or invoked by an AI agent), output defaults to YAML.

Output follows a stable envelope schema ([SCHEMA.md](./SCHEMA.md)):
```yaml
ok: true
schema_version: "1"
data: { ... }
```

See `.agent/skills/SKILL.md` for AI agent usage instructions.

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest tests/ -v

# Unit tests only (no network)
uv run pytest tests/ -v --ignore=tests/test_integration.py -m "not smoke"

# Smoke tests (need cookies)
uv run pytest tests/ -v -m smoke

# Integration tests (need cookies)
uv run pytest tests/test_integration.py -v

# Lint
uv run ruff check .
```

## Troubleshooting

**Q: `NoCookieError: No 'a1' cookie found`**

1. Open Chrome/Edge and visit https://www.xiaohongshu.com/
2. Log in with your account
3. Run `xhs login --cookie-source chrome`

**Q: `NeedVerifyError: Captcha required`**

XHS has triggered a captcha check. Open https://www.xiaohongshu.com/ in your browser, complete the captcha, then retry.

**Q: `IpBlockedError: IP blocked by XHS`**

Try a different network (e.g., mobile hotspot or VPN). XHS blocks IPs that make too many requests.

**Q: `SessionExpiredError: Session expired`**

Your cookies have expired. Run `xhs login` to refresh.

**Q: Requests are slow**

The built-in rate-limit delay (1s between requests) is intentional to avoid triggering XHS's anti-scraping. You can reduce it at your own risk by passing a shorter timeout in code, but this may lead to IP blocks.

## License

Apache-2.0
