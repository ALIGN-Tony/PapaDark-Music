# Software Requirements Specification (SRS)

## Account Trading Safety & Education App (working title: "TradeSafe")

| | |
|---|---|
| **Document version** | 0.1 (Draft for review) |
| **Date** | 2026-08-29 |
| **Author** | PapaDark (engineering) |
| **Product owner / domain expert** | ZAYTSEV |
| **Status** | Awaiting ZAYTSEV review — blanks marked with 🔶 |

---

**How to read this document (ZAYTSEV):** everything marked like this —

> 🔶 **ZAYTSEV — FILL IN:** *question for you*

— is a blank only you can fill. Answer inline, in Discord, or however is easiest. Everything else is my best understanding of what you described; correct anything I got wrong. Nothing here is final until you sign off.

---

## 1. Introduction

### 1.1 Purpose

This document specifies the requirements for a cross-platform mobile application (Android and iOS) that **educates players about buying and selling game accounts safely**. It is the agreed "guardrails and directions" for development: what the app must do, what is in the first release (MVP), and what is deliberately out of scope.

### 1.2 Problem statement

Account trading between players is common but risky. Many players — including experienced account owners — do not know:

- how account ownership and linked credentials actually work,
- what a scammer's playbook looks like,
- which precautions to take before, during, and after a transaction.

The product owner has completed **75+ account sales** for one specific game, has personally encountered essentially every failure mode (scams, recovery hijacks, payment disputes, mislinked credentials), and knows the working countermeasures. That knowledge currently lives in one person's head and in scattered trading-group chats. This app packages it into a searchable, structured, always-available guide.

### 1.3 Product vision

A player opens the app, types a question the way they would into a search engine ("how do I unlink an email before selling?", "buyer wants to pay with PayPal friends & family — is that safe?"), and immediately gets a clear, trustworthy answer — text plus, where it helps, a short demonstration video (e.g., how to delete account links). A dedicated **Precautions** section walks them through a transaction step by step.

**This is an educational app.** It does not host listings, broker deals, hold funds, or connect buyers with sellers. (See §1.5.)

### 1.4 Intended audience for this document

- PapaDark — implementation
- ZAYTSEV — content, domain review, product decisions

### 1.5 Scope

**In scope (product):**

- Searchable knowledge base of Q&A-style articles about account trading safety
- Curated topic/category browsing
- Embedded example/demonstration videos
- A structured "Transaction Precautions" section (checklists for buyers and sellers)
- A scam-pattern encyclopedia ("know the playbook")

**Explicitly out of scope (all releases unless re-decided):**

- Marketplace or listing functionality of any kind
- Escrow, payments, or money handling
- Chat or user-to-user messaging
- Anything that automates or facilitates the trade itself

Keeping the app strictly educational keeps us clear of payment regulation, fraud liability, and most app-store policy risk.

> 🔶 **ZAYTSEV — FILL IN (important, affects everything):** Which game is this for? Is the app **branded around that one game** or written generically with game-specific examples? Note that selling accounts violates most games' Terms of Service — the app *teaching safety* is defensible ("harm reduction / anti-scam education"), but naming the game changes our app-store review risk and possibly wording throughout. What's your call?

> 🔶 **ZAYTSEV — FILL IN:** App name. "TradeSafe" is a placeholder — do you have a name in mind?

> 🔶 **ZAYTSEV — FILL IN:** Languages. English only for MVP, or do your trading groups operate in another language (e.g., Russian) that should come first or ship alongside?

### 1.6 Definitions and abbreviations

| Term | Meaning |
|---|---|
| **Account trading** | Buying/selling of game accounts between players |
| **Linked credential** | Email, phone number, platform link (Google/Apple/Facebook/etc.) attached to a game account |
| **Recovery hijack** | Seller (or original owner) reclaiming a sold account via account-recovery flows |
| **KB** | Knowledge base — the app's article content |
| **MVP** | Minimum Viable Product — the first shippable release (§7) |
| **CMS** | Content management system — where articles/videos are authored |

---

## 2. Overall description

### 2.1 Product perspective

A standalone mobile app built with **Flutter/Dart**, one codebase for Android and iOS. Content (articles, categories, videos metadata) is served from a lightweight backend/CMS so ZAYTSEV can update content **without an app-store release**. Content is cached on-device so previously loaded material works offline.

### 2.2 User classes

| User class | Description | Priority |
|---|---|---|
| **Seller** | Player preparing to sell an account; needs to know how to prepare the account, vet buyers, and transact safely | High |
| **Buyer** | Player buying an account; needs to know how to verify what they're buying and avoid recovery hijacks | High |
| **Curious player** | Not currently trading; wants to understand risks | Medium |
| **Content admin (ZAYTSEV)** | Authors and updates articles, checklists, and videos via the CMS | High (but not via the mobile app) |

No user accounts/login are required to use the app (see NFR-6).

### 2.3 Operating environment

- **Platforms:** Android 8.0+ (API 26+), iOS 14+ *(proposed floor — covers >95% of devices while keeping Flutter tooling simple)*
- **Framework:** Flutter (stable channel), Dart
- **Distribution:** Google Play Store, Apple App Store
- **Backend:** Small content API + CMS (proposed: Firebase [Firestore + Storage + Remote Config] or a headless CMS like Strapi — decision in §8)

### 2.4 Design and implementation constraints

- Single codebase (Flutter) for both platforms — no platform-specific rewrites.
- Content must be editable by a non-developer (ZAYTSEV) without code changes or store releases.
- Videos must not bloat the app binary — streamed/downloaded on demand, never bundled.
- Must comply with Google Play and Apple App Store content policies (educational framing matters here — see §1.5 scope note).

### 2.5 Assumptions and dependencies

- ZAYTSEV supplies the domain content (article drafts, checklist items, scam patterns, video footage or scripts). PapaDark can edit/structure but cannot invent the domain knowledge.
- Videos will be recorded as screen captures of the relevant flows (e.g., unlinking accounts).

> 🔶 **ZAYTSEV — FILL IN:** Video hosting. Options: (a) unlisted YouTube embeds — free, easy, but shows YouTube chrome and requires their app/player; (b) files in Firebase Storage / a CDN played natively in-app — cleaner UX, small hosting cost. Preference?

> 🔶 **ZAYTSEV — FILL IN:** Who records the videos? Do you already have footage from your 75+ sales days, or are we producing these from scratch?

---

## 3. Functional requirements

Requirements are numbered **FR-x.y** and tagged **[MVP]** or **[Later]**. The MVP set is summarized in §7.

### 3.1 Search ("ask a question") — the core interaction

- **FR-1.1 [MVP]** The home screen SHALL present a prominent search field inviting the user to type a question in natural language (search-engine style).
- **FR-1.2 [MVP]** Search SHALL match against article titles, body text, and admin-defined keywords/synonyms (e.g., "unlink", "remove email", "delete account links" all hit the same article).
- **FR-1.3 [MVP]** Results SHALL show title + one-line summary, ranked by relevance, and open the full article on tap.
- **FR-1.4 [MVP]** An empty-result search SHALL show suggested popular topics and a "suggest a question" action (FR-6.1).
- **FR-1.5 [Later]** Search-as-you-type suggestions.
- **FR-1.6 [Later]** Optional AI-assisted answers synthesized from KB articles (answers must cite the underlying articles; never answer from outside the KB). *Deliberately post-MVP: cost, moderation, and hallucination risk.*

### 3.2 Knowledge base (articles & categories)

- **FR-2.1 [MVP]** Content SHALL be organized into admin-defined categories. Proposed initial set (ZAYTSEV to confirm/edit):
  1. Before you sell — preparing an account
  2. Before you buy — verifying an account
  3. Payment methods — safe vs. dangerous
  4. During the deal — step-by-step process
  5. After the deal — securing/handing over
  6. Scam patterns — know the playbook
  7. Glossary / basics
- **FR-2.2 [MVP]** Articles SHALL support rich text (headings, lists, bold, images) and embedded video blocks.
- **FR-2.3 [MVP]** Each article SHALL display a "last updated" date.
- **FR-2.4 [MVP]** Articles SHALL be updatable server-side with changes appearing in the app without a store release.
- **FR-2.5 [MVP]** Previously viewed content SHALL be readable offline (cached); the app SHALL clearly indicate when showing cached content and cannot reach the server.
- **FR-2.6 [Later]** Bookmarks/favorites.
- **FR-2.7 [Later]** "Related articles" links at the end of each article.

### 3.3 Precautions section (dedicated, first-class)

This is the section ZAYTSEV explicitly called out: key precautions to take during transactions.

- **FR-3.1 [MVP]** A dedicated **Precautions** tab SHALL present two guided tracks: **"I'm selling"** and **"I'm buying."**
- **FR-3.2 [MVP]** Each track SHALL be an ordered, step-by-step checklist (before / during / after the transaction) with a short explanation per step and links into relevant KB articles/videos.
- **FR-3.3 [MVP]** Users SHALL be able to check items off; state persists locally on the device (no account needed).
- **FR-3.4 [MVP]** Steps that protect against a specific scam SHALL name it and link to the scam-pattern entry ("this step prevents: recovery hijack").
- **FR-3.5 [Later]** Printable/shareable summary of the checklist.

> 🔶 **ZAYTSEV — FILL IN (the heart of the app):** Draft the two checklists. Bullet points are fine — I'll structure them. For each: what do you do **before**, **during**, and **after** a sale, and same for a purchase? From your 75+ sales, what are the steps people always skip and regret?

### 3.4 Scam-pattern encyclopedia

- **FR-4.1 [MVP]** A browsable list of known scam patterns. Each entry: name, how it works, warning signs, how to protect yourself, (optional) real anonymized example.
- **FR-4.2 [MVP]** Scam entries SHALL be cross-linked from search results and precaution steps.
- **FR-4.3 [Later]** "Red flag quick-check": user answers a few questions about their current deal and the app flags matching scam patterns.

> 🔶 **ZAYTSEV — FILL IN:** List every scam type you've seen or heard of in the trading groups (name + one-paragraph description each). Examples I'd guess from context: fake payment screenshots, chargeback-after-delivery, recovery hijack by seller, impersonating a middleman, "pay outside the agreed method" switch. What am I missing? Which are the top 5 by frequency?

### 3.5 Video library

- **FR-5.1 [MVP]** Videos SHALL be embedded inside relevant articles/steps (e.g., "how to delete account links" demo).
- **FR-5.2 [MVP]** A simple **Videos** screen SHALL list all videos with title and duration.
- **FR-5.3 [MVP]** Videos stream on demand; nothing video is bundled in the app binary.
- **FR-5.4 [Later]** Offline download of individual videos.

> 🔶 **ZAYTSEV — FILL IN:** First list of videos to produce. You mentioned "how to delete account links" — what are the next 5–10 most valuable demos?

### 3.6 Feedback

- **FR-6.1 [MVP]** Users SHALL be able to submit a question the KB didn't answer (simple text form → lands with the admin). This doubles as our content roadmap.
- **FR-6.2 [Later]** Per-article "Was this helpful? 👍/👎".

### 3.7 Content administration (not in the mobile app)

- **FR-7.1 [MVP]** Admin (ZAYTSEV) SHALL be able to create/edit/publish/unpublish categories, articles, checklist steps, scam entries, and video metadata through a web CMS with login.
- **FR-7.2 [MVP]** Draft vs. published states; only published content appears in the app.
- **FR-7.3 [Later]** Multiple admin roles.

### 3.8 Notifications

- **FR-8.1 [Later]** Push notification when significant new content is published (opt-in). *Post-MVP: not needed to validate the product.*

---

## 4. Non-functional requirements

- **NFR-1 Performance:** Cold start ≤ 3 s on a mid-range device; search results ≤ 1 s on cached index.
- **NFR-2 Offline:** Core reading experience works offline for cached content (see FR-2.5). First run requires connectivity.
- **NFR-3 Usability:** A first-time user reaches an answer to a typed question in ≤ 3 taps from app open. Reading experience supports system light/dark mode.
- **NFR-4 Accessibility:** Respect OS font scaling; meet WCAG AA contrast; all videos get captions or an equivalent text write-up (many users will be in public/no-audio contexts — and it helps non-native speakers).
- **NFR-5 Reliability:** App must never hard-crash on network loss; all network operations have timeouts and user-visible retry.
- **NFR-6 Privacy:** No user accounts, no collection of personal data in MVP. Feedback submissions are anonymous unless the user volunteers contact info. This keeps our store privacy declarations trivial ("data not collected") and builds trust with a scam-wary audience.
- **NFR-7 Security:** CMS admin access behind authentication; content API is read-only to the public; feedback endpoint rate-limited.
- **NFR-8 Maintainability:** All user-facing strings in localization files from day one (cheap now, expensive to retrofit — see the language blank in §1.5).
- **NFR-9 Store compliance:** App copy avoids facilitating-a-marketplace framing; description emphasizes education and scam prevention.

---

## 5. External interface requirements

### 5.1 User interface (screens, MVP)

1. **Home / Ask** — search field, popular questions, category shortcuts
2. **Search results**
3. **Article view** — rich text + embedded video
4. **Categories / browse**
5. **Precautions** — seller track & buyer track checklists
6. **Scam patterns** — list + detail
7. **Videos** — list
8. **About / disclaimer** — who's behind this, educational-purpose disclaimer
9. **Suggest a question** — feedback form

*(No design mockups yet — ZAYTSEV said no specific design idea in mind. PapaDark will propose wireframes after this SRS is agreed; visual style TBD then.)*

### 5.2 Software interfaces

- Content API (read-only JSON) — backend choice in §8
- Video streaming source (per the §2.5 hosting decision)
- Feedback submission endpoint

### 5.3 Hardware interfaces

None beyond a standard phone. No camera/location/contacts permissions. Internet permission only.

---

## 6. Legal & policy considerations (read me, ZAYTSEV)

1. **Game ToS:** Account selling violates most games' Terms of Service. The app must be framed (and genuinely function) as **safety education**, not trade facilitation — this is why §1.5's out-of-scope list is strict.
2. **Disclaimer screen (MVP):** The app SHALL include a disclaimer that it provides educational information only, is not affiliated with the game publisher, and does not encourage ToS violations.
3. **Trademark:** If we name the game or use its imagery, we risk trademark complaints and store takedowns. Safer: generic branding + "for players of [genre] games" framing, or explicit nominative use with no logos/art. Tied to the §1.5 game-branding blank.
4. **No legal advice:** Payment-dispute content should say "how this typically works," not "legal advice."

---

## 7. MVP definition

**Goal of the MVP:** a player can open the app, search a question, read a clear answer (with video where relevant), and follow a buyer/seller precautions checklist. ZAYTSEV can update all content from a web CMS without app releases.

### 7.1 MVP feature list

| # | Feature | Requirements |
|---|---|---|
| 1 | Natural-language search over the KB | FR-1.1–1.4 |
| 2 | Categorized knowledge base, rich text + video embeds, server-updatable, offline cache | FR-2.1–2.5 |
| 3 | Precautions tab: buyer & seller step-by-step checklists with local check-off | FR-3.1–3.4 |
| 4 | Scam-pattern encyclopedia | FR-4.1–4.2 |
| 5 | Video library (streamed, embedded + list screen) | FR-5.1–5.3 |
| 6 | "Suggest a question" feedback form | FR-6.1 |
| 7 | Web CMS for ZAYTSEV (draft/publish) | FR-7.1–7.2 |
| 8 | About + disclaimer screen | §6.2 |
| 9 | Light/dark mode, offline resilience, no-login privacy posture | NFR-2, 3, 5, 6 |

### 7.2 MVP content list (the real critical path)

The app is only as good as its content. Minimum content to launch:

- [ ] 15–25 KB articles covering the most-asked questions — 🔶 **ZAYTSEV: list your top questions from trading groups; the ones you answer over and over**
- [ ] Seller precautions checklist (complete) — 🔶 **ZAYTSEV (§3.3 blank)**
- [ ] Buyer precautions checklist (complete) — 🔶 **ZAYTSEV (§3.3 blank)**
- [ ] 8–12 scam-pattern entries — 🔶 **ZAYTSEV (§3.4 blank)**
- [ ] 3–5 demo videos (incl. "how to delete account links") — 🔶 **ZAYTSEV (§3.5 blank)**
- [ ] Disclaimer text — PapaDark drafts, ZAYTSEV reviews

### 7.3 Explicitly NOT in MVP

AI answers, push notifications, bookmarks, video downloads, user accounts, ratings, red-flag quick-check, multiple languages (unless §1.5 language answer changes this), anything marketplace-shaped (never).

### 7.4 Acceptance criteria (MVP done when…)

1. Fresh install on a real Android device and a real iPhone; user types "how do I remove my email from the account" and reaches the right article in ≤ 3 taps.
2. ZAYTSEV edits an article in the CMS; change appears in the app without an update.
3. Airplane mode: previously read articles and checklist state still work; app degrades gracefully, no crashes.
4. Both checklists can be worked through end-to-end, and checked state survives app restart.
5. All §7.2 content is published.

---

## 8. Open technical decisions (PapaDark to propose, ZAYTSEV to okay)

| # | Decision | Options | Leaning |
|---|---|---|---|
| 1 | Backend/CMS | Firebase (Firestore + Storage + a simple admin panel) vs. headless CMS (Strapi/Directus) vs. static JSON + GitHub | Firebase — least ops burden, free tier fits an educational app, and gives us feedback storage + remote config in one place |
| 2 | Search implementation | On-device index over synced content vs. server-side search | On-device — instant, works offline, KB is small (dozens–hundreds of articles) |
| 3 | Video hosting | Awaiting §2.5 blank | — |
| 4 | State management (Flutter) | Riverpod vs. Bloc | Riverpod — lighter for an app this size |
| 5 | Analytics | None vs. privacy-light aggregate (screen views, search terms with no user IDs) | 🔶 **ZAYTSEV — FILL IN:** search terms with zero results are *gold* for knowing what content to write next, but "no tracking at all" is also a legitimate stance for this audience. Preference? |

---

## 9. Roadmap after MVP (draft)

1. **v1.1** — bookmarks, related articles, 👍/👎 on articles, more videos
2. **v1.2** — red-flag quick-check (FR-4.3), push notifications for new content
3. **v2.0** — AI-assisted answers grounded in the KB (FR-1.6), second language if demanded

---

## 10. Summary of all blanks for ZAYTSEV

Quick checklist of every 🔶 in this document:

1. **§1.5** Which game; branded to it or generic? *(blocks naming, store strategy, legal framing)*
2. **§1.5** App name?
3. **§1.5** Language(s) for launch?
4. **§2.5** Video hosting: YouTube embeds vs. native hosted files?
5. **§2.5** Who records the videos / existing footage?
6. **§3.3** Seller & buyer precaution checklists (before/during/after) — **the core content**
7. **§3.4** Full scam-pattern list + top 5 by frequency
8. **§3.5** First 5–10 videos to produce
9. **§7.2** Top 15–25 questions you get asked in trading groups
10. **§8.5** Analytics: zero-result search-term logging, or no analytics at all?

Items **1, 6, 7, and 9** are the ones that block the most work — everything else can be decided while coding is underway.
