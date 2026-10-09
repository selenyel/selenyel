#!/usr/bin/env python3
"""
Custom Contribution Snake Generator for Selen Yel Temellioğlu (stemellioglu.yml)
- Diamond apples for contribution cells (rainbow colored: cyan -> emerald -> gold -> prism magenta)
- Grass cells with blades/spikes for zero-contribution days
- Orange snake with black tiger stripes and dots
- Outputs both light and dark mode SVGs
- Generates glassmorphic profile header banners (header-glass-light.svg & header-glass-dark.svg)
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
            # Take last 371 days (53 weeks * 7 days)
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

    # Final fallback: synthetic realistic grid
    grid = []
    for c in range(COLS):
        week = []
        for r in range(ROWS):
            # cluster contributions on weekdays
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
        # Default scenic loop if no apples
        apples = [(5, 2), (15, 4), (25, 1), (35, 5), (45, 3)]

    # Start snake at (0, 0)
    curr = (0, 0)
    full_path = [(0, 0)]
    unvisited = set(apples)

    while unvisited:
        # Pick closest apple
        nxt = min(unvisited, key=lambda a: abs(a[0] - curr[0]) + abs(a[1] - curr[1]))
        seg = bfs_path(curr, nxt)
        full_path.extend(seg[1:])
        curr = nxt
        unvisited.remove(nxt)

    # Route back to (0, 0) to close loop
    seg = bfs_path(curr, (0, 0))
    full_path.extend(seg[1:])

    # If path is too short, add a loop around grid perimeter
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

    # Find earliest step each apple is visited
    apple_eats = {}
    for step_idx, pt in enumerate(full_path):
        if pt in apples and pt not in apple_eats:
            apple_eats[pt] = step_idx

    return full_path, apple_eats


def build_snake_svg(grid, path, apple_eats, dark_mode=False):
    """Build the animated SVG with custom snake, diamond apples, and glass meadow."""
    num_steps = len(path)
    # Total animation duration: ~25s
    duration_ms = 25000

    # Color tokens
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
        grass_blade_opacity = "0.45"
        text_color = "#334155"
        text_sub = "#94a3b8"

    # Snake segment count: Head (s0) + 4 body segments + tail (s5)
    snake_length = 6

    # Generate CSS keyframes for snake segments
    keyframes_css = []

    for seg_idx in range(snake_length):
        kf_lines = []
        for i in range(num_steps):
            pct = (i / (num_steps - 1)) * 100
            # Follow path with delay for each segment
            path_idx = (i - seg_idx) % num_steps
            pt = path[path_idx]
            x = OFFSET_X + pt[0] * CELL_STEP
            y = OFFSET_Y + pt[1] * CELL_STEP

            # Rotation for head (s0) based on movement direction
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

    # Generate eating animation for each diamond apple
    apple_styles = []
    for pt, eat_step in apple_eats.items():
        c, r = pt
        eat_pct = (eat_step / (num_steps - 1)) * 100
        apple_id = f"apl_{c}_{r}"
        # Apple stays visible, vanishes on snake head arrival, respawns at cycle end
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

    # Assemble SVG content
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_svg_width}" height="{total_svg_height}" viewBox="0 0 {total_svg_width} {total_svg_height}">',
        f'<desc>Stemellioglu Glass Meadow Snake — Selen Yel Temellioğlu</desc>',
        '<defs>',
        # Snake Body Gradients
        '  <linearGradient id="snakeOrange" x1="0%" y1="0%" x2="100%" y2="100%">',
        '    <stop offset="0%" stop-color="#ff7a00"/>',
        '    <stop offset="100%" stop-color="#ff9500"/>',
        '  </linearGradient>',
        '  <linearGradient id="snakeHead" x1="0%" y1="0%" x2="100%" y2="100%">',
        '    <stop offset="0%" stop-color="#ff8c00"/>',
        '    <stop offset="100%" stop-color="#ff5500"/>',
        '  </linearGradient>',
        # Level 1 Cyan Diamond Apple
        '  <g id="diamond-apple-1">',
        '    <path d="M6,2.2 L10.5,5.5 L6,11.5 L1.5,5.5 Z" fill="#0284c7"/>',
        '    <path d="M6,2.2 L10.5,5.5 L6,6.5 L1.5,5.5 Z" fill="#38bdf8"/>',
        '    <path d="M1.5,5.5 L6,6.5 L6,11.5 Z" fill="#0369a1"/>',
        '    <path d="M6,2.2 C6.2,1.2 7,0.7 7.6,0.5" stroke="#78350f" stroke-width="0.8" stroke-linecap="round" fill="none"/>',
        '    <circle cx="8" cy="1" r="0.8" fill="#10b981"/>',
        '  </g>',
        # Level 2 Emerald Diamond Apple
        '  <g id="diamond-apple-2">',
        '    <path d="M6,2.2 L10.5,5.5 L6,11.5 L1.5,5.5 Z" fill="#059669"/>',
        '    <path d="M6,2.2 L10.5,5.5 L6,6.5 L1.5,5.5 Z" fill="#34d399"/>',
        '    <path d="M1.5,5.5 L6,6.5 L6,11.5 Z" fill="#047857"/>',
        '    <path d="M6,2.2 C6.2,1.2 7,0.7 7.6,0.5" stroke="#78350f" stroke-width="0.8" stroke-linecap="round" fill="none"/>',
        '    <circle cx="8" cy="1" r="0.8" fill="#6ee7b7"/>',
        '  </g>',
        # Level 3 Gold Diamond Apple
        '  <g id="diamond-apple-3">',
        '    <path d="M6,2.2 L10.5,5.5 L6,11.5 L1.5,5.5 Z" fill="#d97706"/>',
        '    <path d="M6,2.2 L10.5,5.5 L6,6.5 L1.5,5.5 Z" fill="#fbbf24"/>',
        '    <path d="M1.5,5.5 L6,6.5 L6,11.5 Z" fill="#b45309"/>',
        '    <path d="M6,2.2 C6.2,1.2 7,0.7 7.6,0.5" stroke="#78350f" stroke-width="0.8" stroke-linecap="round" fill="none"/>',
        '    <circle cx="8" cy="1" r="0.8" fill="#10b981"/>',
        '  </g>',
        # Level 4 Prism Magenta Diamond Apple
        '  <g id="diamond-apple-4">',
        '    <path d="M6,2.2 L10.5,5.5 L6,11.5 L1.5,5.5 Z" fill="#9333ea"/>',
        '    <path d="M6,2.2 L10.5,5.5 L6,6.5 L1.5,5.5 Z" fill="#f472b6"/>',
        '    <path d="M1.5,5.5 L6,6.5 L6,11.5 Z" fill="#c026d3"/>',
        '    <path d="M6,2.2 C6.2,1.2 7,0.7 7.6,0.5" stroke="#78350f" stroke-width="0.8" stroke-linecap="round" fill="none"/>',
        '    <circle cx="8" cy="1" r="0.8" fill="#ec4899"/>',
        '  </g>',
        # Grass Meadow Tile with blades/spikes
        f'  <g id="grass-tile">',
        f'    <rect width="{CELL_SIZE}" height="{CELL_SIZE}" rx="3" fill="{grass_tile_fill}" stroke="{grass_tile_stroke}" stroke-width="0.75"/>',
        f'    <path d="M4,10 L5,5 L6,10 M8,10 L8.5,3.5 L9.5,10" stroke="{grass_blade_stroke}" stroke-width="0.85" stroke-linecap="round" stroke-linejoin="round" opacity="{grass_blade_opacity}" fill="none"/>',
        f'  </g>',
        # Snake Head (Orange with Black Tiger Stripes and Eyes & Tongue)
        '  <g id="snake-head-asset">',
        '    <rect width="13" height="13" rx="4" fill="url(#snakeHead)" stroke="#c2410c" stroke-width="0.75"/>',
        '    <!-- Black Tiger Chevron Markings -->',
        '    <path d="M3.5,1.5 L6.5,4.5 L9.5,1.5" stroke="#09090b" stroke-width="1.2" stroke-linecap="round" fill="none"/>',
        '    <path d="M3.5,11.5 L6.5,8.5 L9.5,11.5" stroke="#09090b" stroke-width="1.2" stroke-linecap="round" fill="none"/>',
        '    <!-- Glowing Eyes (Dots) -->',
        '    <circle cx="9.5" cy="4" r="1.8" fill="#ffffff"/>',
        '    <circle cx="10" cy="4" r="1" fill="#09090b"/>',
        '    <circle cx="10.3" cy="3.7" r="0.4" fill="#38bdf8"/>',
        '    <circle cx="9.5" cy="9" r="1.8" fill="#ffffff"/>',
        '    <circle cx="10" cy="9" r="1" fill="#09090b"/>',
        '    <circle cx="10.3" cy="8.7" r="0.4" fill="#38bdf8"/>',
        '    <!-- Flicking Tongue -->',
        '    <path d="M13,6.5 L15,6.5 L16.5,5 M15,6.5 L16.5,8" stroke="#ef4444" stroke-width="0.9" stroke-linecap="round" fill="none"/>',
        '  </g>',
        # Snake Body Segment with Black Tiger Stripes
        '  <g id="snake-body-asset">',
        '    <rect width="12" height="12" rx="3.5" fill="url(#snakeOrange)" stroke="#c2410c" stroke-width="0.75"/>',
        '    <!-- Black Tiger Stripes -->',
        '    <path d="M2.5,2.5 L6,6 L2.5,9.5 M6.5,2.5 L10,6 L6.5,9.5" stroke="#09090b" stroke-width="1.2" stroke-linecap="round" fill="none"/>',
        '  </g>',
        # Snake Tail Segment
        '  <g id="snake-tail-asset">',
        '    <path d="M1,2.5 L11,1 L11,11 L1,9.5 Z" fill="url(#snakeOrange)" stroke="#c2410c" stroke-width="0.75"/>',
        '    <path d="M4,3 L8,3 M4,6 L8,6 M4,9 L8,9" stroke="#09090b" stroke-width="1.1" stroke-linecap="round" fill="none"/>',
        '  </g>',
        '</defs>',
        '<style>',
        '  .bg-box { rx: 12px; }',
        '\n'.join(snake_classes),
        '\n'.join(keyframes_css),
        '\n'.join(apple_styles),
        '</style>',
        # Background card
        f'<rect class="bg-box" width="{total_svg_width}" height="{total_svg_height}" fill="{bg_fill}" stroke="{border_stroke}" stroke-width="1"/>',
    ]

    # Grid: Render grass meadow tiles for all 53 x 7 cells
    for c in range(COLS):
        col_x = OFFSET_X + c * CELL_STEP
        for r in range(ROWS):
            row_y = OFFSET_Y + r * CELL_STEP
            svg_parts.append(f'<use href="#grass-tile" x="{col_x}" y="{row_y}"/>')

    # Grid: Render diamond apples on cells with contributions
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

    # Legend at bottom
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

    # Render Snake Segments (Tail -> Body -> Head) so Head renders on top
    # Tail (s5)
    svg_parts.append(f'<g class="s_5"><use href="#snake-tail-asset"/></g>')
    # Body (s4, s3, s2, s1)
    for seg_idx in range(snake_length - 2, 0, -1):
        svg_parts.append(f'<g class="s_{seg_idx}"><use href="#snake-body-asset"/></g>')
    # Head (s0)
    svg_parts.append(f'<g class="s_0"><use href="#snake-head-asset"/></g>')

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def build_header_svg(username="Selen Yel Temellioğlu", dark_mode=False):
    """Build a signature glassmorphic header card for Selen Yel Temellioğlu."""
    width = 880
    height = 200

    if dark_mode:
        bg_card = "#0B0F19"
        border_grad_stops = """
          <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.6"/>
          <stop offset="50%" stop-color="#818cf8" stop-opacity="0.25"/>
          <stop offset="100%" stop-color="#c084fc" stop-opacity="0.6"/>
        """
        inner_glass_fill = "#111827"
        inner_glass_opacity = "0.75"
        text_title = "#f8fafc"
        text_subtitle = "#94a3b8"
        badge_bg = "#1e293b"
        badge_border = "#334155"
        badge_text = "#38bdf8"
        chip_bg = "#0f172a"
        chip_border = "#1e293b"
        chip_text = "#cbd5e1"
        glow_color_1 = "#0284c7"
        glow_color_2 = "#7c3aed"
    else:
        bg_card = "#f8fafc"
        border_grad_stops = """
          <stop offset="0%" stop-color="#0284c7" stop-opacity="0.5"/>
          <stop offset="50%" stop-color="#6366f1" stop-opacity="0.25"/>
          <stop offset="100%" stop-color="#9333ea" stop-opacity="0.5"/>
        """
        inner_glass_fill = "#ffffff"
        inner_glass_opacity = "0.85"
        text_title = "#0f172a"
        text_subtitle = "#475569"
        badge_bg = "#e0f2fe"
        badge_border = "#bae6fd"
        badge_text = "#0369a1"
        chip_bg = "#f1f5f9"
        chip_border = "#e2e8f0"
        chip_text = "#334155"
        glow_color_1 = "#38bdf8"
        glow_color_2 = "#c084fc"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="headerBorder" x1="0%" y1="0%" x2="100%" y2="100%">
      {border_grad_stops}
    </linearGradient>
    <linearGradient id="titleGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{text_title}"/>
      <stop offset="100%" stop-color="{text_subtitle}"/>
    </linearGradient>
    <filter id="ambientBlur" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="50"/>
    </filter>
  </defs>

  <!-- Canvas Card -->
  <rect width="{width}" height="{height}" rx="18" fill="{bg_card}" stroke="#1e293b" stroke-width="0.5"/>

  <!-- Ambient Glow Orbs -->
  <circle cx="140" cy="40" r="110" fill="{glow_color_1}" opacity="0.12" filter="url(#ambientBlur)"/>
  <circle cx="760" cy="160" r="130" fill="{glow_color_2}" opacity="0.12" filter="url(#ambientBlur)"/>

  <!-- Glass Card Overlay -->
  <rect x="12" y="12" width="{width - 24}" height="{height - 24}" rx="14" fill="{inner_glass_fill}" fill-opacity="{inner_glass_opacity}" stroke="url(#headerBorder)" stroke-width="1"/>

  <!-- Top Discipline Pill Badge -->
  <g transform="translate(42, 34)">
    <rect width="284" height="24" rx="12" fill="{badge_bg}" stroke="{badge_border}" stroke-width="1"/>
    <circle cx="14" cy="12" r="3.5" fill="#10b981"/>
    <text x="26" y="16" fill="{badge_text}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="10.5" font-weight="700" letter-spacing="1">UX ENGINEER • FRONT-END ARCHITECTURE</text>
  </g>

  <!-- Name -->
  <text x="42" y="98" fill="url(#titleGrad)" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="34" font-weight="800" letter-spacing="-0.5">{username}</text>

  <!-- Subtitle -->
  <text x="42" y="126" fill="{text_subtitle}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14" font-weight="500">Bridging Design Token Architecture • Multi-Platform Ergonomics • Scalable UI Systems</text>

  <!-- Tags / Chips along bottom -->
  <g transform="translate(42, 148)">
    <!-- Chip 1 -->
    <rect x="0" y="0" width="138" height="24" rx="6" fill="{chip_bg}" stroke="{chip_border}" stroke-width="1"/>
    <text x="10" y="16" fill="{chip_text}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">Web • iOS • watchOS</text>

    <!-- Chip 2 -->
    <rect x="146" y="0" width="156" height="24" rx="6" fill="{chip_bg}" stroke="{chip_border}" stroke-width="1"/>
    <text x="156" y="16" fill="{chip_text}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">Design Systems (Tokens)</text>

    <!-- Chip 3 -->
    <rect x="310" y="0" width="186" height="24" rx="6" fill="{chip_bg}" stroke="{chip_border}" stroke-width="1"/>
    <text x="320" y="16" fill="{chip_text}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">React • Angular • TypeScript</text>

    <!-- Chip 4 -->
    <rect x="504" y="0" width="144" height="24" rx="6" fill="{chip_bg}" stroke="{chip_border}" stroke-width="1"/>
    <text x="514" y="16" fill="{chip_text}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600">WCAG 2.1 AA Compliant</text>
  </g>
</svg>"""
    return svg


def clean_xml(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def build_timeline_svg(dark_mode=False):
    """Build glassmorphic timeline cards matching the interactive web app design."""
    w, h = 880, 608
    bg = '#0B0F19' if dark_mode else '#f8fafc'
    border = '#1e293b' if dark_mode else '#e2e8f0'
    head_title = '#38bdf8' if dark_mode else '#0284c7'
    head_sub = '#64748b' if dark_mode else '#94a3b8'
    card_bg = '#111827' if dark_mode else '#ffffff'
    card_opacity = '0.75' if dark_mode else '0.95'
    card_border = '#1e293b' if dark_mode else '#e2e8f0'
    text_primary = '#f8fafc' if dark_mode else '#0f172a'
    text_muted = '#94a3b8' if dark_mode else '#475569'

    jobs = [
        ('Sep 2025 – Present', '#38bdf8', 'UI/UX Designer & Front-End Developer', 'OneWell',
         'Design and engineer the unified interface layer of a workforce management and care support platform for Direct Support Professionals',
         'across watchOS, iOS, Android, and Web. Own component systems, WCAG 2.1 AA accessibility, and API contracts under active shift conditions.'),
        ('Nov 2022 – Jul 2025', '#34d399', 'Lead Front-End Developer', 'Ministry of Commerce (ESBIS & Consumer Portal)',
         'Led front-end architecture and implementation for two national government web applications serving millions of citizens.',
         'Governed component lifecycles, rendering performance, state isolation, and responsive UI for regulatory committees nationwide.'),
        ('Jan – Mar 2020', '#fbbf24', 'Front-End Engineering Intern', 'Bisoft',
         'Engineered React dashboards rendering complex multi-dimensional metric datasets, including real-time seismic readings.',
         'Focused on adaptive graphing, proportional data density across screen sizes, and tabular data stability.'),
        ('2017 & 2018', '#c084fc', 'Front-End Engineering Intern', 'LOGO Yazılım',
         'Angular enterprise component design implementation and UI integration across core ERP modules.',
         'Test coverage scripting and automated CI package publication pipelines.'),
        ('Academic Foundations', '#60a5fa', 'B.S. in Computer Engineering • TÜBİTAK Researcher', 'TOBB ETÜ & TÜBİTAK (Prof. Mehmet Akşit)',
         'Collaborated on TÜBİTAK research website (ADMPD). Rigorous training in algorithmic design and distributed systems.',
         'Built foundations for treating user interfaces and design token architecture as mission-critical systems.')
    ]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f'  <rect width="{w}" height="{h}" rx="16" fill="{bg}" stroke="{border}" stroke-width="1"/>',
        f'  <text x="28" y="32" fill="{head_title}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-size="11" font-weight="700" letter-spacing="1.5">CAREER TIMELINE • ENGINEERING &amp; UX JOURNEY</text>',
        f'  <text x="852" y="32" text-anchor="end" fill="{head_sub}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-size="11" font-weight="500">Chronological Archive</text>',
    ]

    y_offset = 48
    card_h = 98
    gap = 12

    for date_str, color, role, company, line1, line2 in jobs:
        parts.append(f'  <g transform="translate(24, {y_offset})">')
        parts.append(f'    <rect width="832" height="{card_h}" rx="12" fill="{card_bg}" fill-opacity="{card_opacity}" stroke="{card_border}" stroke-width="1"/>')
        parts.append(f'    <text x="20" y="24" fill="{color}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-size="11" font-weight="700">{clean_xml(date_str)}</text>')
        parts.append(f'    <text x="20" y="46" fill="{text_primary}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-size="14.5" font-weight="700">{clean_xml(role)}</text>')
        offset_x = 24 + len(role) * 8.2
        parts.append(f'    <text x="{offset_x:.0f}" y="46" fill="{color}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-size="12.5" font-weight="600">• {clean_xml(company)}</text>')
        parts.append(f'    <text x="20" y="68" fill="{text_muted}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-size="11.5" font-weight="400">{clean_xml(line1)}</text>')
        parts.append(f'    <text x="20" y="84" fill="{text_muted}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-size="11.5" font-weight="400">{clean_xml(line2)}</text>')
        parts.append('  </g>')
        y_offset += card_h + gap

    parts.append('</svg>')
    return '\n'.join(parts)


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "dist"
    username = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("GITHUB_ACTOR", "selenyel")

    os.makedirs(out_dir, exist_ok=True)
    print(f"Generating Stemellioglu Snake & Header SVGs for '{username}' -> '{out_dir}'...")

    grid = fetch_contributions(username=username)
    print(f"Fetched {len(grid)} columns of contribution data.")

    path, apple_eats = generate_snake_path(grid)
    print(f"Computed snake path: {len(path)} steps, {len(apple_eats)} diamond apples visited.")

    # 1. Light Mode Snake SVG
    snake_light = build_snake_svg(grid, path, apple_eats, dark_mode=False)
    with open(os.path.join(out_dir, "github-contribution-grid-snake.svg"), "w", encoding="utf-8") as f:
        f.write(snake_light)
    print("✓ Saved github-contribution-grid-snake.svg (light)")

    # 2. Dark Mode Snake SVG
    snake_dark = build_snake_svg(grid, path, apple_eats, dark_mode=True)
    with open(os.path.join(out_dir, "github-contribution-grid-snake-dark.svg"), "w", encoding="utf-8") as f:
        f.write(snake_dark)
    print("✓ Saved github-contribution-grid-snake-dark.svg (dark)")

    # 3. Light Mode Header SVG
    header_light = build_header_svg("Selen Yel Temellioğlu", dark_mode=False)
    with open(os.path.join(out_dir, "header-glass-light.svg"), "w", encoding="utf-8") as f:
        f.write(header_light)
    print("✓ Saved header-glass-light.svg (light)")

    # 4. Dark Mode Header SVG
    header_dark = build_header_svg("Selen Yel Temellioğlu", dark_mode=True)
    with open(os.path.join(out_dir, "header-glass-dark.svg"), "w", encoding="utf-8") as f:
        f.write(header_dark)
    print("✓ Saved header-glass-dark.svg (dark)")

    # 5. Light Mode Career Timeline SVG
    timeline_light = build_timeline_svg(dark_mode=False)
    with open(os.path.join(out_dir, "career-timeline-light.svg"), "w", encoding="utf-8") as f:
        f.write(timeline_light)
    print("✓ Saved career-timeline-light.svg (light)")

    # 6. Dark Mode Career Timeline SVG
    timeline_dark = build_timeline_svg(dark_mode=True)
    with open(os.path.join(out_dir, "career-timeline-dark.svg"), "w", encoding="utf-8") as f:
        f.write(timeline_dark)
    print("✓ Saved career-timeline-dark.svg (dark)")

    # 7. Copy interactive profile HTML for GitHub Pages if exists
    for src in ["interactive_profile.html", os.path.join(os.path.dirname(__file__), "../../interactive_profile.html")]:
        if os.path.exists(src):
            import shutil
            shutil.copy(src, os.path.join(out_dir, "index.html"))
            print("✓ Saved index.html (interactive web profile)")
            break

    print("All SVGs successfully generated!")

if __name__ == "__main__":
    main()