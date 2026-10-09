#!/usr/bin/env python3
"""
Custom Contribution Snake Generator for Selen Yel Temellioğlu (stemellioglu.yml)
- Diamond apples for contribution cells (rainbow colored: cyan -> emerald -> gold -> prism magenta)
- Grass cells with blades/spikes for zero-contribution days
- Orange snake with black tiger stripes and dots
- Outputs both light and dark mode SVGs
"""
import sys
import json
import math
import random
import os
import urllib.request
import ssl
def fetch_contributions(username, token=None):
    """Fetch contribution calendar using GitHub GraphQL API if token provided, or public fallback."""
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
                for w in weeks:
                    week_days = []
                    for d in w["contributionDays"]:
                        cnt = d["contributionCount"]
                        lvl = 0
                        if cnt > 0:
                            if cnt <= 2: lvl = 1
                            elif cnt <= 5: lvl = 2
                            elif cnt <= 9: lvl = 3