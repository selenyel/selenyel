#!/usr/bin/env python3
"""
Custom Contribution Snake & Glassmorphism Asset Generator for Selen Yel Temellioğlu
- Clean floating glassmorphic cards (NO awkward background plates/containers)
- Diamond apples for contribution cells (rainbow colored: cyan -> emerald -> gold -> prism magenta)
- Grass cells with blades/spikes for zero-contribution days
- Orange snake with black tiger stripes and dots
- Floating Droplet Career Timeline SVGs with transparent canvas
- Adaptive Droplet Pill Button SVGs without underline artifacts
- Deploys full interactive web profile (index.html) to GitHub Pages
"""
import sys
import json
import os
import urllib.request
import ssl
import collections

COLS = 53
ROWS = 7
CELL_SIZE = 12
CELL_GAP = 4
CELL_STEP = CELL_SIZE + CELL_GAP  # 16px
OFFSET_X = 16
OFFSET_Y = 20

def clean_xml(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def fetch_contributions(username="selenyel", token=None):
    """Fetch contribution calendar using GitHub GraphQL API if token provided, or public fallback."""
    if not token:
        token = os.environ.get("GITHUB_TOKEN")

    if token:
        query = """
        query($login: String!) {
          user(login: $login) {
            contributionsCollection {
              contributionCalendar {
                totalContributions
                weeks {
                  contributionDays {
                    contributionCount
                    contributionLevel
                    date
                    weekday
                  }
                }
              }
            }
          }
        }
        """
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=json.dumps({"query": query, "variables": {"login": username}}).encode("utf-8"),
            headers={"Authorization": f"Bearer {token}", "User-Agent": "stemellioglu-snake"}
        )
        try:
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(req, context=ctx, timeout=15) as res:
                data = json.loads(res.read().decode())
                weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
                grid = []
                for w in weeks[-COLS:]:
                    week_days = []
                    for d in w["contributionDays"]:
                        cnt = d["contributionCount"]
                        lvl = 0
                        if cnt > 0:
                            if cnt <= 2: lvl = 1
                            elif cnt <= 5: lvl = 2
                            elif cnt <= 9: lvl = 3
                            else: lvl = 4
                        week_days.append({
                            "count": cnt,
                            "level": lvl,
                            "date": d.get("date", ""),
                            "weekday": d.get("weekday", 0)
                        })
                    grid.append(week_days)
                if len(grid) == COLS:
                    return grid
        except Exception as e:
            print(f"GraphQL fetch failed ({e}), trying public fallback...")

    # Fallback to public contributions API
    try:
        url = f"https://github-contributions-api.jogruber.de/v4/{username}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode())
            contributions = data.get("contributions", [])
            recent = contributions[- (COLS * ROWS):]
            grid = []
            for col_i in range(COLS):
                week_days = []
                for row_i in range(ROWS):
                    idx = col_i * ROWS + row_i
                    if idx < len(recent):
                        d = recent[idx]
                        cnt = d.get("count", 0)
                        lvl = d.get("level", 0)
                        week_days.append({
                            "count": cnt,
                            "level": lvl,
                            "date": d.get("date", ""),
                            "weekday": row_i
                        })
                    else:
                        week_days.append({"count": 0, "level": 0, "date": "", "weekday": row_i})
                grid.append(week_days)
            return grid
    except Exception as e:
        print(f"Public API fetch failed ({e}), generating placeholder grid...")

    grid = []
    for c in range(COLS):
        week = []
        for r in range(ROWS):
            lvl = 0
            if (c + r * 7) % 11 == 0: lvl = 1
            elif (c + r * 7) % 17 == 0: lvl = 2
            elif (c + r * 7) % 29 == 0: lvl = 3
            elif (c + r * 7) % 43 == 0: lvl = 4
            week.append({"count": lvl * 2, "level": lvl, "date": "", "weekday": r})
        grid.append(week)
    return grid


def bfs_path(start, goal):
    """Find shortest grid path from start to goal within bounds [0..COLS-1, 0..ROWS-1]."""
    if start == goal:
        return [start]
    queue = collections.deque([[start]])
    visited = {start}
    while queue:
        curr_path = queue.popleft()
        curr = curr_path[-1]
        if curr == goal:
            return curr_path
        neighbors = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = curr[0] + dx, curr[1] + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS and (nx, ny) not in visited:
                visited.add((nx, ny))
                neighbors.append((nx, ny))
        neighbors.sort(key=lambda n: abs(n[0] - goal[0]) + abs(n[1] - goal[1]))
        for n in neighbors:
            queue.append(curr_path + [n])
    return [start, goal]


def generate_snake_path(grid):
    """Generate a smooth cyclic path visiting all diamond apples."""
    apples = []
    for c_idx, col in enumerate(grid):
        for r_idx, day in enumerate(col):
            if day.get("level", 0) > 0:
                apples.append((c_idx, r_idx))

    if not apples:
        apples = [(5, 2), (15, 4), (25, 1), (35, 5), (45, 3)]

    curr = (0, 0)
    full_path = [(0, 0)]
    unvisited = set(apples)

    while unvisited:
        nxt = min(unvisited, key=lambda a: abs(a[0] - curr[0]) + abs(a[1] - curr[1]))
        seg = bfs_path(curr, nxt)
        full_path.extend(seg[1:])
        curr = nxt
        unvisited.remove(nxt)

    seg = bfs_path(curr, (0, 0))
    full_path.extend(seg[1:])

    if len(full_path) < 140:
        perimeter = []
        for x in range(0, COLS): perimeter.append((x, 0))
        for y in range(1, ROWS): perimeter.append((COLS - 1, y))
        for x in range(COLS - 2, -1, -1): perimeter.append((x, ROWS - 1))
        for y in range(ROWS - 2, 0, -1): perimeter.append((0, y))
        seg_p = bfs_path(full_path[-1], perimeter[0])
        full_path.extend(seg_p[1:])
        full_path.extend(perimeter[1:])
        seg_close = bfs_path(full_path[-1], (0, 0))
        full_path.extend(seg_close[1:])

    apple_eats = {}
    for step_idx, pt in enumerate(full_path):
        if pt in apples and pt not in apple_eats:
            apple_eats[pt] = step_idx

    return full_path, apple_eats


def build_snake_svg(grid, path, apple_eats, dark_mode=False):
    """Build the animated SVG with custom snake, diamond apples, and clean floating card."""
    num_steps = len(path)
    duration_ms = 25000

    if dark_mode:
        bg_fill = "#0B0F19"
        border_stroke = "#1e293b"
        grass_tile_fill = "#111827"
        grass_tile_stroke = "#1f2937"
        grass_blade_stroke = "#059669"
        grass_blade_opacity = "0.55"
        text_color = "#94a3b8"
        text_sub = "#64748b"
    else:
        bg_fill = "#ffffff"
        border_stroke = "#e2e8f0"
        grass_tile_fill = "#f8fafc"
        grass_tile_stroke = "#e2e8f0"
        grass_blade_stroke = "#10b981"
        grass_blade_opacity = "0.5"
        text_color = "#334155"
        text_sub = "#64748b"

    snake_length = 6
    keyframes_css = []

    for seg_idx in range(snake_length):
        kf_lines = []
        for i in range(num_steps):
            pct = (i / (num_steps - 1)) * 100
            path_idx = (i - seg_idx) % num_steps
            pt = path[path_idx]
            x = OFFSET_X + pt[0] * CELL_STEP
            y = OFFSET_Y + pt[1] * CELL_STEP

            if seg_idx == 0:
                nxt_idx = (i + 1) % num_steps
                nxt_pt = path[nxt_idx]
                dx = nxt_pt[0] - pt[0]
                dy = nxt_pt[1] - pt[1]
                rot = 0
                if dx > 0: rot = 0
                elif dx < 0: rot = 180
                elif dy > 0: rot = 90
                elif dy < 0: rot = 270
                kf_lines.append(f"{pct:.2f}%{{transform:translate({x}px,{y}px) rotate({rot}deg);}}")
            else:
                kf_lines.append(f"{pct:.2f}%{{transform:translate({x}px,{y}px);}}")

        keyframes_css.append(f"@keyframes snake_seg_{seg_idx} {{\n" + "\n".join(kf_lines) + "\n}")

    apple_styles = []
    for pt, eat_step in apple_eats.items():
        c, r = pt
        eat_pct = (eat_step / (num_steps - 1)) * 100
        apple_id = f"apl_{c}_{r}"
        kf_apple = f"""@keyframes kf_{apple_id} {{
            0%, {max(0.0, eat_pct - 0.2):.2f}% {{ opacity: 1; transform: scale(1); }}
            {eat_pct:.2f}%, 99.4% {{ opacity: 0; transform: scale(0); }}
            100% {{ opacity: 1; transform: scale(1); }}
        }}
        .{apple_id} {{
            animation: kf_{apple_id} {duration_ms}ms linear infinite;
            transform-origin: {OFFSET_X + c * CELL_STEP + 6}px {OFFSET_Y + r * CELL_STEP + 6}px;
        }}"""
        apple_styles.append(kf_apple)

    snake_classes = []
    for seg_idx in range(snake_length):
        origin = "transform-origin: 6px 6px;" if seg_idx == 0 else ""
        snake_classes.append(f".s_{seg_idx} {{ animation: snake_seg_{seg_idx} {duration_ms}ms linear infinite; {origin} }}")

    total_svg_width = OFFSET_X * 2 + COLS * CELL_STEP
    total_svg_height = OFFSET_Y * 2 + ROWS * CELL_STEP + 26

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_svg_width}" height="{total_svg_height}" viewBox="0 0 {total_svg_width} {total_svg_height}">',
        f'<desc>Stemellioglu Glass Meadow Snake — Selen Yel Temellioğlu</desc>',
        '<defs>',
        '  <filter id="snakeCardShadow" x="-2%" y="-5%" width="104%" height="115%">',
        '    <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="' + ('0.3' if dark_mode else '0.05') + '"/>',
        '  </filter>',
        '  <linearGradient id="snakeOrange" x1="0%" y1="0%" x2="100%" y2="100%">',
        '    <stop offset="0%" stop-color="#ff7a00"/>',
        '    <stop offset="100%" stop-color="#ff9500"/>',
        '  </linearGradient>',
        '  <linearGradient id="snakeHead" x1="0%" y1="0%" x2="100%" y2="100%">',
        '    <stop offset="0%" stop-color="#ff8c00"/>',
        '    <stop offset="100%" stop-color="#ff5500"/>',
        '  </linearGradient>',
        '  <g id="diamond-apple-1">',
        '    <path d="M6,2.2 L10.5,5.5 L6,11.5 L1.5,5.5 Z" fill="#0284c7"/>',
        '    <path d="M6,2.2 L10.5,5.5 L6,6.5 L1.5,5.5 Z" fill="#38bdf8"/>',
        '    <path d="M1.5,5.5 L6,6.5 L6,11.5 Z" fill="#0369a1"/>',
        '    <path d="M6,2.2 C6.2,1.2 7,0.7 7.6,0.5" stroke="#78350f" stroke-width="0.8" stroke-linecap="round" fill="none"/>',
        '    <circle cx="8" cy="1" r="0.8" fill="#10b981"/>',
        '  </g>',
        '  <g id="diamond-apple-2">',
        '    <path d="M6,2.2 L10.5,5.5 L6,11.5 L1.5,5.5 Z" fill="#059669"/>',
        '    <path d="M6,2.2 L10.5,5.5 L6,6.5 L1.5,5.5 Z" fill="#34d399"/>',
        '    <path d="M1.5,5.5 L6,6.5 L6,11.5 Z" fill="#047857"/>',
        '    <path d="M6,2.2 C6.2,1.2 7,0.7 7.6,0.5" stroke="#78350f" stroke-width="0.8" stroke-linecap="round" fill="none"/>',
        '    <circle cx="8" cy="1" r="0.8" fill="#6ee7b7"/>',
        '  </g>',
        '  <g id="diamond-apple-3">',
        '    <path d="M6,2.2 L10.5,5.5 L6,11.5 L1.5,5.5 Z" fill="#d97706"/>',
        '    <path d="M6,2.2 L10.5,5.5 L6,6.5 L1.5,5.5 Z" fill="#fbbf24"/>',
        '    <path d="M1.5,5.5 L6,6.5 L6,11.5 Z" fill="#b45309"/>',
        '    <path d="M6,2.2 C6.2,1.2 7,0.7 7.6,0.5" stroke="#78350f" stroke-width="0.8" stroke-linecap="round" fill="none"/>',
        '    <circle cx="8" cy="1" r="0.8" fill="#10b981"/>',
        '  </g>',
        '  <g id="diamond-apple-4">',
        '    <path d="M6,2.2 L10.5,5.5 L6,11.5 L1.5,5.5 Z" fill="#9333ea"/>',
        '    <path d="M6,2.2 L10.5,5.5 L6,6.5 L1.5,5.5 Z" fill="#f472b6"/>',
        '    <path d="M1.5,5.5 L6,6.5 L6,11.5 Z" fill="#c026d3"/>',
        '    <path d="M6,2.2 C6.2,1.2 7,0.7 7.6,0.5" stroke="#78350f" stroke-width="0.8" stroke-linecap="round" fill="none"/>',
        '    <circle cx="8" cy="1" r="0.8" fill="#ec4899"/>',
        '  </g>',
        f'  <g id="grass-tile">',
        f'    <rect width="{CELL_SIZE}" height="{CELL_SIZE}" rx="3" fill="{grass_tile_fill}" stroke="{grass_tile_stroke}" stroke-width="0.75"/>',
        f'    <path d="M4,10 L5,5 L6,10 M8,10 L8.5,3.5 L9.5,10" stroke="{grass_blade_stroke}" stroke-width="0.85" stroke-linecap="round" stroke-linejoin="round" opacity="{grass_blade_opacity}" fill="none"/>',
        f'  </g>',
        '  <g id="snake-head-asset">',
        '    <rect width="13" height="13" rx="4" fill="url(#snakeHead)" stroke="#c2410c" stroke-width="0.75"/>',
        '    <path d="M3.5,1.5 L6.5,4.5 L9.5,1.5" stroke="#09090b" stroke-width="1.2" stroke-linecap="round" fill="none"/>',
        '    <path d="M3.5,11.5 L6.5,8.5 L9.5,11.5" stroke="#09090b" stroke-width="1.2" stroke-linecap="round" fill="none"/>',
        '    <circle cx="9.5" cy="4" r="1.8" fill="#ffffff"/>',
        '    <circle cx="10" cy="4" r="1" fill="#09090b"/>',
        '    <circle cx="10.3" cy="3.7" r="0.4" fill="#38bdf8"/>',
        '    <circle cx="9.5" cy="9" r="1.8" fill="#ffffff"/>',
        '    <circle cx="10" cy="9" r="1" fill="#09090b"/>',
        '    <circle cx="10.3" cy="8.7" r="0.4" fill="#38bdf8"/>',
        '    <path d="M13,6.5 L15,6.5 L16.5,5 M15,6.5 L16.5,8" stroke="#ef4444" stroke-width="0.9" stroke-linecap="round" fill="none"/>',
        '  </g>',
        '  <g id="snake-body-asset">',
        '    <rect width="12" height="12" rx="3.5" fill="url(#snakeOrange)" stroke="#c2410c" stroke-width="0.75"/>',
        '    <path d="M2.5,2.5 L6,6 L2.5,9.5 M6.5,2.5 L10,6 L6.5,9.5" stroke="#09090b" stroke-width="1.2" stroke-linecap="round" fill="none"/>',
        '  </g>',
        '  <g id="snake-tail-asset">',
        '    <path d="M1,2.5 L11,1 L11,11 L1,9.5 Z" fill="url(#snakeOrange)" stroke="#c2410c" stroke-width="0.75"/>',
        '    <path d="M4,3 L8,3 M4,6 L8,6 M4,9 L8,9" stroke="#09090b" stroke-width="1.1" stroke-linecap="round" fill="none"/>',
        '  </g>',
        '</defs>',
        '<style>',
        '  .bg-box { rx: 16px; }',
        '\n'.join(snake_classes),
        '\n'.join(keyframes_css),
        '\n'.join(apple_styles),
        '</style>',
        f'<rect class="bg-box" x="2" y="2" width="{total_svg_width - 4}" height="{total_svg_height - 4}" fill="{bg_fill}" stroke="{border_stroke}" stroke-width="1" filter="url(#snakeCardShadow)"/>',
    ]

    for c in range(COLS):
        col_x = OFFSET_X + c * CELL_STEP
        for r in range(ROWS):
            row_y = OFFSET_Y + r * CELL_STEP
            svg_parts.append(f'<use href="#grass-tile" x="{col_x}" y="{row_y}"/>')

    for c in range(COLS):
        col_x = OFFSET_X + c * CELL_STEP
        col_data = grid[c] if c < len(grid) else []
        for r in range(ROWS):
            row_y = OFFSET_Y + r * CELL_STEP
            day = col_data[r] if r < len(col_data) else {"level": 0}
            lvl = day.get("level", 0)
            if lvl > 0:
                apple_id = f"apl_{c}_{r}"
                svg_parts.append(f'<use class="{apple_id}" href="#diamond-apple-{lvl}" x="{col_x}" y="{row_y}"/>')

    legend_y = OFFSET_Y + ROWS * CELL_STEP + 10
    svg_parts.append(f'<g transform="translate({OFFSET_X}, {legend_y})">')
    svg_parts.append(f'  <text x="0" y="9" fill="{text_sub}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-size="10" font-weight="500">Less</text>')
    svg_parts.append(f'  <use href="#grass-tile" x="32" y="0"/>')
    svg_parts.append(f'  <use href="#diamond-apple-1" x="52" y="0"/>')
    svg_parts.append(f'  <use href="#diamond-apple-2" x="72" y="0"/>')
    svg_parts.append(f'  <use href="#diamond-apple-3" x="92" y="0"/>')
    svg_parts.append(f'  <use href="#diamond-apple-4" x="112" y="0"/>')
    svg_parts.append(f'  <text x="132" y="9" fill="{text_sub}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-size="10" font-weight="500">More</text>')
    svg_parts.append(f'  <text x="{total_svg_width - OFFSET_X * 2}" y="9" text-anchor="end" fill="{text_color}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-size="10" font-weight="600">Stemellioglu Glass Meadow Snake</text>')
    svg_parts.append('</g>')

    svg_parts.append(f'<g class="s_5"><use href="#snake-tail-asset"/></g>')
    for seg_idx in range(snake_length - 2, 0, -1):
        svg_parts.append(f'<g class="s_{seg_idx}"><use href="#snake-body-asset"/></g>')
    svg_parts.append(f'<g class="s_0"><use href="#snake-head-asset"/></g>')

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def build_header_svg(username="Selen Yel Temellioğlu", dark_mode=False):
    """Build a single clean floating glassmorphic header card with NO outer plate."""
    width = 880
    height = 185

    if dark_mode:
        card_fill = "#0B0F19"
        border_grad_stops = """
          <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.6"/>
          <stop offset="50%" stop-color="#818cf8" stop-opacity="0.25"/>
          <stop offset="100%" stop-color="#c084fc" stop-opacity="0.6"/>
        """
        text_title = "#f8fafc"
        text_subtitle = "#94a3b8"
        badge_bg = "#1e293b"
        badge_border = "#334155"
        badge_text = "#38bdf8"
        chip_bg = "#111827"
        chip_border = "#1e293b"
        chip_text = "#cbd5e1"
        shadow_opacity = "0.35"
    else:
        card_fill = "#ffffff"
        border_grad_stops = """
          <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.5"/>
          <stop offset="50%" stop-color="#6366f1" stop-opacity="0.2"/>
          <stop offset="100%" stop-color="#9333ea" stop-opacity="0.5"/>
        """
        text_title = "#0f172a"
        text_subtitle = "#475569"
        badge_bg = "#e0f2fe"
        badge_border = "#bae6fd"
        badge_text = "#0369a1"
        chip_bg = "#f8fafc"
        chip_border = "#e2e8f0"
        chip_text = "#334155"
        shadow_opacity = "0.06"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="headerBorder" x1="0%" y1="0%" x2="100%" y2="100%">
      {border_grad_stops}
    </linearGradient>
    <linearGradient id="titleGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{text_title}"/>
      <stop offset="100%" stop-color="{text_subtitle}"/>
    </linearGradient>
    <filter id="headerShadow" x="-5%" y="-5%" width="110%" height="125%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="{shadow_opacity}"/>
    </filter>
  </defs>

  <!-- Clean Floating Card (NO outer backdrop plate) -->
  <rect x="2" y="2" width="{width - 4}" height="{height - 4}" rx="18" fill="{card_fill}" stroke="url(#headerBorder)" stroke-width="1.2" filter="url(#headerShadow)"/>

  <!-- Top Discipline Pill Badge -->
  <g transform="translate(32, 26)">
    <rect width="284" height="24" rx="12" fill="{badge_bg}" stroke="{badge_border}" stroke-width="1"/>
    <circle cx="14" cy="12" r="3.5" fill="#10b981"/>
    <text x="26" y="16" fill="{badge_text}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="10.5" font-weight="700" letter-spacing="1">UX ENGINEER • FRONT-END ARCHITECTURE</text>
  </g>

  <!-- Name & UXE Badge -->
  <g transform="translate(32, 86)">
    <text x="0" y="0" fill="url(#titleGrad)" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="32" font-weight="800" letter-spacing="-0.5">{username}</text>
    <rect x="390" y="-20" width="46" height="22" rx="11" fill="#38bdf8" fill-opacity="0.12" stroke="#38bdf8" stroke-width="1"/>
    <text x="413" y="-5" text-anchor="middle" fill="#0284c7" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="10.5" font-weight="700">UXE</text>
  </g>

  <!-- Subtitle -->
  <text x="32" y="114" fill="{text_subtitle}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14" font-weight="500">UX Engineer • Front-End Architecture • OneWell</text>

  <!-- Tags / Chips along bottom -->
  <g transform="translate(32, 136)">
    <rect x="0" y="0" width="138" height="24" rx="6" fill="{chip_bg}" stroke="{chip_border}" stroke-width="1"/>
    <text x="10" y="16" fill="{chip_text}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">Web • iOS • watchOS</text>

    <rect x="146" y="0" width="156" height="24" rx="6" fill="{chip_bg}" stroke="{chip_border}" stroke-width="1"/>
    <text x="156" y="16" fill="{chip_text}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">Design Systems (Tokens)</text>

    <rect x="310" y="0" width="186" height="24" rx="6" fill="{chip_bg}" stroke="{chip_border}" stroke-width="1"/>
    <text x="320" y="16" fill="{chip_text}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">React • Angular • TypeScript</text>

    <rect x="504" y="0" width="144" height="24" rx="6" fill="{chip_bg}" stroke="{chip_border}" stroke-width="1"/>
    <text x="514" y="16" fill="{chip_text}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">WCAG 2.1 AA Compliant</text>
  </g>
</svg>"""
    return svg


def build_timeline_svg(dark_mode=False):
    """Build floating glassmorphic droplet timeline cards with transparent canvas (NO background plate)."""
    w, h = 880, 770
    card_bg = '#111827' if dark_mode else '#ffffff'
    card_stroke = '#1e293b' if dark_mode else '#e2e8f0'
    text_primary = '#f8fafc' if dark_mode else '#0f172a'
    text_muted = '#94a3b8' if dark_mode else '#64748b'
    section_title = '#38bdf8' if dark_mode else '#0284c7'
    archive_text = '#64748b' if dark_mode else '#94a3b8'
    shadow_opacity = '0.35' if dark_mode else '0.06'

    jobs = [
        ('Sep 2025 – Present', '#38bdf8' if dark_mode else '#0284c7', 'UI/UX Designer & Front-End Developer', 'OneWell',
         ['Design and engineer the unified interface layer of a workforce management and care support',
          'platform for Direct Support Professionals across watchOS, iOS, Android, and Web. Own the',
          'component system, accessibility (WCAG AA), and API contracts under active shift conditions.']),

        ('Nov 2022 – Jul 2025', '#34d399' if dark_mode else '#059669', 'Lead Front-End Developer', 'Ministry of Commerce • ESBIS & Consumer Portal',
         ['Led front-end architecture and implementation for two national government web applications.',
          'Governed component lifecycles, rendering performance, state isolation, and responsive UI',
          'serving millions of citizens and regulatory committees nationwide.']),

        ('Jan – Mar 2020', '#fbbf24' if dark_mode else '#d97706', 'Front-End Engineering Intern', 'Bisoft',
         ['Engineered React dashboards rendering complex multi-dimensional metric datasets, including',
          'real-time seismic readings. Focused on adaptive graphs, proportional data density across',
          'screen sizes, and tabular data stability.']),

        ('2017 & 2018', '#c084fc' if dark_mode else '#7c3aed', 'Front-End Engineering Intern', 'LOGO Yazılım',
         ['Angular enterprise component design implementation, test coverage scripting, and',
          'automated CI package publication pipelines. Built accessible enterprise UI patterns.']),

        ('Academic Foundations', '#60a5fa' if dark_mode else '#2563eb', 'B.S. in Computer Engineering • TÜBİTAK Researcher', 'TOBB University of Economics & Technology',
         ['Collaborated with Prof. Mehmet Akşit on TÜBİTAK research website (ADMPD). Rigorous',
          'training in algorithmic design and distributed systems that laid the foundation for treating',
          'user interfaces as mission-critical systems.'])
    ]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        '  <defs>',
        '    <filter id="cardShadow" x="-5%" y="-5%" width="110%" height="125%">',
        f'      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="{shadow_opacity}"/>',
        '    </filter>',
        '  </defs>',
        f'  <text x="8" y="24" fill="{section_title}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-size="11.5" font-weight="700" letter-spacing="1.5">CAREER TIMELINE • ENGINEERING &amp; UX JOURNEY</text>',
        f'  <text x="872" y="24" text-anchor="end" fill="{archive_text}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-size="11.5" font-weight="500">Chronological Archive</text>',
    ]

    y_offset = 38
    card_h = 132
    gap = 14

    for date_str, color, role, company, desc_lines in jobs:
        parts.append(f'  <g transform="translate(4, {y_offset})">')
        parts.append(f'    <rect width="872" height="{card_h}" rx="16" fill="{card_bg}" stroke="{card_stroke}" stroke-width="1" filter="url(#cardShadow)"/>')
        parts.append(f'    <text x="24" y="28" fill="{color}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-size="12" font-weight="700">{clean_xml(date_str)}</text>')
        parts.append(f'    <text x="24" y="54" fill="{text_primary}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-size="16" font-weight="700">{clean_xml(role)}</text>')
        parts.append(f'    <text x="24" y="75" fill="{color}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-size="13" font-weight="600">{clean_xml(company)}</text>')
        line_y = 96
        for line in desc_lines:
            parts.append(f'    <text x="24" y="{line_y}" fill="{text_muted}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-size="12" font-weight="400">{clean_xml(line)}</text>')
            line_y += 17
        parts.append('  </g>')
        y_offset += card_h + gap

    parts.append('</svg>')
    return '\n'.join(parts)


def build_button_svg(text, width=150):
    """Build an adaptive droplet pill button SVG matching the web app design."""
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="38" viewBox="0 0 {width} 38">
  <defs>
    <filter id="btnShadow" x="-10%" y="-20%" width="120%" height="150%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000000" flood-opacity="0.06"/>
    </filter>
  </defs>
  <style>
    .btn-bg {{ fill: #ffffff; stroke: #e2e8f0; }}
    .btn-txt {{ fill: #1e293b; }}
    @media (prefers-color-scheme: dark) {{
      .btn-bg {{ fill: #1e293b; stroke: #334155; }}
      .btn-txt {{ fill: #f8fafc; }}
    }}
  </style>
  <rect class="btn-bg" x="2" y="2" width="{width - 4}" height="34" rx="17" stroke-width="1.2" filter="url(#btnShadow)"/>
  <text class="btn-txt" x="{width / 2:.1f}" y="22" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="12.5" font-weight="600">{text}</text>
</svg>"""
    return svg


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "dist"
    username = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("GITHUB_ACTOR", "selenyel")

    os.makedirs(out_dir, exist_ok=True)
    print(f"Generating Clean Plateless SVGs for '{username}' -> '{out_dir}'...")

    grid = fetch_contributions(username=username)
    print(f"Fetched {len(grid)} columns of contribution data.")

    path, apple_eats = generate_snake_path(grid)
    print(f"Computed snake path: {len(path)} steps, {len(apple_eats)} diamond apples visited.")

    # 1. Snake SVGs
    snake_light = build_snake_svg(grid, path, apple_eats, dark_mode=False)
    with open(os.path.join(out_dir, "github-contribution-grid-snake.svg"), "w", encoding="utf-8") as f:
        f.write(snake_light)
    print("✓ Saved github-contribution-grid-snake.svg (light)")

    snake_dark = build_snake_svg(grid, path, apple_eats, dark_mode=True)
    with open(os.path.join(out_dir, "github-contribution-grid-snake-dark.svg"), "w", encoding="utf-8") as f:
        f.write(snake_dark)
    print("✓ Saved github-contribution-grid-snake-dark.svg (dark)")

    # 2. Header SVGs (Single clean floating card)
    header_light = build_header_svg("Selen Yel Temellioğlu", dark_mode=False)
    with open(os.path.join(out_dir, "header-glass-light.svg"), "w", encoding="utf-8") as f:
        f.write(header_light)
    print("✓ Saved header-glass-light.svg (light)")

    header_dark = build_header_svg("Selen Yel Temellioğlu", dark_mode=True)
    with open(os.path.join(out_dir, "header-glass-dark.svg"), "w", encoding="utf-8") as f:
        f.write(header_dark)
    print("✓ Saved header-glass-dark.svg (dark)")

    # 3. Career Timeline SVGs (Plateless floating cards)
    timeline_light = build_timeline_svg(dark_mode=False)
    with open(os.path.join(out_dir, "career-timeline-light.svg"), "w", encoding="utf-8") as f:
        f.write(timeline_light)
    print("✓ Saved career-timeline-light.svg (light)")

    timeline_dark = build_timeline_svg(dark_mode=True)
    with open(os.path.join(out_dir, "career-timeline-dark.svg"), "w", encoding="utf-8") as f:
        f.write(timeline_dark)
    print("✓ Saved career-timeline-dark.svg (dark)")

    # 4. Adaptive Pill Button SVGs
    buttons = [
        ("btn-interactive-cv.svg", "Interactive CV", 145),
        ("btn-linkedin.svg", "LinkedIn Profile", 150),
        ("btn-credly.svg", "Credly Badges", 140),
        ("btn-google.svg", "Google Developers", 160),
    ]
    for b_file, b_text, b_w in buttons:
        b_svg = build_button_svg(b_text, b_w)
        with open(os.path.join(out_dir, b_file), "w", encoding="utf-8") as f:
            f.write(b_svg)
        print(f"✓ Saved {b_file}")

    # 5. Copy interactive profile HTML for GitHub Pages (live interactive site)
    for src in ["interactive_profile.html", os.path.join(os.path.dirname(__file__), "../../interactive_profile.html")]:
        if os.path.exists(src):
            import shutil
            shutil.copy(src, os.path.join(out_dir, "index.html"))
            print("✓ Saved index.html (interactive web profile)")
            break

    print("All SVGs successfully generated!")

if __name__ == "__main__":
    main()