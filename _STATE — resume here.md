# Davis Landworks website — resume here

**Last updated:** 2026-09-14 (Patrick + Claude)

## What this is
Friend-favor one-page site for **Davis Landworks LLC** — Harrison Davis (close friend, former
Navy SEAL, owner of the excavation/site-work company; contact in the vault at
`_Vendors/_contacts_directory.md`). Stump grinding, grading, light excavation, hauling/cleanup,
Virginia Beach / Hampton Roads. Booking-first: the estimate form opens the visitor's Messages
app pre-addressed to Harrison's cell — no backend.

## Status — LIVE 2026-09-14
- **Site is live at https://davislandworksva.com** (HTTPS enforced, cert approved). Also serves
  at www and at `bylerent-bot.github.io/davis-landworks-site/`.
- **DONE:** Migrated off ChatGPT's "Sites" builder into a clean static site here on Desktop
  (`~/Desktop/davis-landworks-site/`), design preserved verbatim, verified desktop + mobile,
  no console errors. Repo: `github.com/bylerent-bot/davis-landworks-site` (main root, GitHub Pages).
- **Domain registered:** davislandworksva.com via **Cloudflare Registrar** in Patrick's account
  (patrick@bylerenterprises.com, acct 40149e...), $10.46/yr, **auto-renew ON**, WHOIS private.
  (davislandworks.com was taken/expired-parked at GoDaddy — not used.)
- **DNS (Cloudflare, all DNS-only/grey cloud):** 4 apex A records → 185.199.108–111.153;
  `www` CNAME → bylerent-bot.github.io. `CNAME` file in the repo = davislandworksva.com.
- The original ChatGPT project (React/vinext/Cloudflare, ~646 MB incl. node_modules) still sits
  in the vault at `_Non-BE/Davis Landworks Website/` — **to be archived/removed** (nested repo +
  node_modules in iCloud). Superseded by this folder.

## Open items / next steps
1. **Email — needs Harrison.** Cloudflare Email Routing is enabled on the domain (MX/DKIM/SPF
   records added). Destination **Davislandworksllc@gmail.com** is added but **Pending** — Cloudflare
   emailed a verification link to that inbox; **Harrison must click it**. Only AFTER that can the
   routing rule **harrison@davislandworksva.com → Davislandworksllc@gmail.com** be created (the rule
   builder only accepts verified destinations). Then Harrison sets Gmail "Send as" to reply as harrison@.
2. **Review claims — VERIFIED 2026-09-14** against Harrison's real Google profile.
   - Real & kept: 5.0 rating, 39 reviews; Jessica quote and Patrick Clark quote (both verbatim
     from real reviews); grading story + service area (from the Aug 9 owner post).
   - ChatGPT had FABRICATED these — now corrected on the site: "18 mention stump grinding" →
     real "11 stump removal"; "11 punctuality" and "5 cleanliness" (no such topics) → real
     "7 fair pricing" + "6 Hampton Roads cities" + "Owner operated"; "quality in 8 reviews" →
     softened to no false count; the "J 1776" quote (wasn't his words) → his real visible words.
   - Real Google review topics for future edits: stump removal 11, fair pricing 7,
     clean up & haul away 2, professional process 2 (+6 more not expandable in limited view).
3. **Harrison hasn't seen the copy.** Confirm he's good with it before sharing the link widely.
4. **Vault cleanup:** archive/remove the old 646 MB ChatGPT project at `_Non-BE/Davis Landworks Website/`.

## Notes
- Google profile linked on the page:
  `https://www.google.com/maps/place/Davis+Landworks+LLC/...11yx7ln9cz`
- Contact wired on the site: cell **251-243-2422**, email **Davislandworksllc@gmail.com**
  (both match the vault contact entry).
