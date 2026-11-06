---
name: awesome-design-md
description: Library of 84 DESIGN.md files that capture the design systems of well-known brands (Stripe, Linear, Vercel, Apple, Notion, Supabase, Coinbase, Revolut, Spotify...). Use when starting a UI, landing page or dashboard and the user wants a specific visual style ("make it look like Linear/Stripe"), or when a project needs a coherent palette, typography, spacing and component rules instead of generic defaults.
---

# Awesome DESIGN.md

Source: https://github.com/VoltAgent/awesome-design-md (MIT, see LICENSE). Catalogue: https://getdesign.md/

Each folder in `design-md/<brand>/` has a `DESIGN.md` describing colors (hex), typography,
spacing, radii, shadows, components and tone of that brand's design system.

## How to use

1. Pick the brand closest to the style the user wants (`ls design-md/`). For fintech / market
   dashboards good fits are: `stripe`, `coinbase`, `kraken`, `revolut`, `wise`, `mercury`,
   `linear.app`, `vercel`, `supabase`, `posthog`.
2. Copy `design-md/<brand>/DESIGN.md` into the project root as `DESIGN.md`.
3. Read it and follow its tokens and rules for every UI decision. Use it as inspiration for a
   coherent system: do not copy the brand's logo, name or trademarked assets into the product.
4. Combine with `taste-skill` (anti-slop rules), `web-design-guidelines` (audit) and
   `playwright-cli` (check the render in a real browser).
