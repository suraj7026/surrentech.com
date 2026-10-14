# Surren Technologies — Landing Page (mock v1)

Single self-contained landing page: `index.html` + small local assets.
No build step, no frameworks — open via any static server:

```bash
cd landing
python3 -m http.server 8080
# → http://localhost:8080
```

## What's inside
- `index.html` — the whole page (inline CSS + ~4 KB vanilla JS)
- `assets/logo.png` — full logo (from `Z_SurrenTechFiles/Logo/Full_Logo/…`, resized to 720w)
- `assets/icon.png` — monogram (256px) used in the board header + footer
- `assets/favicon.png` — 64px favicon
- `assets/og-cover.png` — 1200×630 social share card

## Page flow (conversion architecture)
1. **Hero** — value prop ≤8 words, single high-contrast CTA ("Book a free consult"), annotated live product preview (Accuity practice board, pure CSS/SVG — zero image payload)
2. **Social proof strip** — client wordmark marquee (Rohde & Schwarz, Capgemini, Envestnet…)
3. **01 What we do** — 4 outcome-driven pillars with CSS micro-visuals
4. **02 How we work** — dark interactive stepper (autoplay, click/arrow-key)
5. **03 Product subscriptions** — scroll-snap rail (Accuity, Beekart, Hotel Booking, Cleanroom CRM, AI Plug-in)
6. **04 Engagements** — subscription / custom build (highlighted) / managed IT
7. **05 Testimonials** — placeholder quotes → **replace with real client quotes + permissions before go-live**
8. **06 FAQ** — 6 conversion objections, accordion
9. **Footer CTA** — one work-email field + contact details, motto, saranagati line

## Before production
- [ ] Replace placeholder testimonials (marked in HTML comment) with real ones
- [ ] Wire `#consultForm` to CRM/inbox (currently a mock success state)
- [ ] Point `og:image` + canonical at the real domain once deployed
- [ ] Consider pre-generating `.webp` if any photos get added later

Performance notes: explicit `width/height` on every image (no CLS), one `<h1>`,
strict h2/h3 hierarchy, fonts swapped/preconnected, below-fold sections use
`content-visibility`, payload ≈ 210 KB total (~30 KB gzipped over the wire),
`prefers-reduced-motion` respected throughout.