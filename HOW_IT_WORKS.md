# CivicAlert — How It Works
### Smart Civic Issue Reporting & Resolution Management System
**PS 03.1 · Hack & Hook Hackathon**

---

## Table of Contents
1. [Overview](#overview)
2. [User Roles](#user-roles)
3. [Full App Workflow](#full-app-workflow)
4. [Page-by-Page Breakdown](#page-by-page-breakdown)
5. [Priority Ranking System](#priority-ranking-system)
6. [Database Design](#database-design)
7. [Demo Walkthrough](#demo-walkthrough)

---

## Overview

Citizens regularly encounter civic problems — potholes, broken streetlights, garbage overflow, water leaks — but have no simple, trackable way to report them. Authorities receive scattered complaints with no structured priority, leading to the loudest voice (not the most urgent issue) getting attention first.

**CivicAlert solves this by:**
- Giving citizens a fast, structured form to report issues
- Auto-generating a tracking ID so citizens can follow progress
- Auto-ranking every issue using a priority score (no human bias)
- Giving authorities a sorted queue — most urgent issues always on top
- Surfacing recurring problem hotspots through analytics

---

## User Roles

| Role | What They Do |
|------|-------------|
| **Citizen** | Reports a civic issue, receives a tracking ID, checks status later |
| **Authority / Official** | Views the priority-sorted dashboard, assigns officers, updates status, adds resolution notes |

> No login is required for this prototype — designed for fast, friction-free demo.

---

## Full App Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CITIZEN SIDE                                 │
└─────────────────────────────────────────────────────────────────────┘

  Citizen fills /report form
       │
       ├── Name, Phone (optional)
       ├── Category      → e.g. "Road Damage"
       ├── Severity      → High / Medium / Low
       ├── Location      → Street name, landmark, ward
       ├── Description   → What they see, for how long
       └── Photo         → Optional image upload

       │
       ▼
  System AUTO-CALCULATES Priority Score
       │
       ├── Category Weight  (based on public safety impact)
       ├── Severity Weight  (citizen-assessed urgency)
       └── Recurrence Bonus (same issue reported before in same area?)

       │
       ▼
  Issue saved to SQLite DB with unique ID (e.g. CIV3A7F2B1C)

       │
       ▼
  Citizen receives Tracking ID on screen
       │
       └── Citizen visits /track → enters ID
                │
                └── Sees: Status badge, Location, Authority notes,
                          Visual timeline (Submitted → In Progress → Resolved)


┌─────────────────────────────────────────────────────────────────────┐
│                        AUTHORITY SIDE                                │
└─────────────────────────────────────────────────────────────────────┘

  Authority opens /admin dashboard
       │
       ├── Sees STATS BAR:  Total | Pending | In Progress | Resolved
       ├── Can FILTER by:   Status, Category, Priority Level
       └── Issue TABLE sorted by Priority Score (highest = top)

       │
       ▼
  Authority clicks "View" on an issue
       │
       ├── Sees full details: reporter, location, description, photo
       ├── Sees Priority Breakdown (score explained)
       └── UPDATE PANEL:
             ├── Change Status  → Pending / In Progress / Resolved / Closed
             ├── Assign To      → Officer name or department
             └── Add Notes      → Visible to citizen when they track

       │
       ▼
  Citizen tracks issue → sees the update in real-time
```

---

## Page-by-Page Breakdown

### `/` — Home
- Overview of the platform
- Three entry cards: Report Issue, Track Issue, Authority Dashboard
- "How It Works" 4-step guide

---

### `/report` — Report an Issue (Citizen)

**Form Fields:**

| Field | Required | Notes |
|-------|----------|-------|
| Name | ✅ | Reporter identity |
| Phone | ❌ | Optional contact |
| Category | ✅ | Dropdown — 7 categories |
| Severity | ✅ | High / Medium / Low |
| Location | ✅ | Street, landmark, ward — be specific |
| Description | ✅ | Freetext — what, since when, danger? |
| Photo | ❌ | Max 5MB, stored in `static/uploads/` |

On submit:
1. Priority score is calculated automatically
2. Issue is saved to `civic.db`
3. Citizen is redirected to `/track?issue_id=CIVxxxxxxxx`

---

### `/track` — Track Issue Status (Citizen)

Enter the tracking ID (e.g. `CIV0000003`) to see:

- **Status badge** — Pending / In Progress / Resolved / Closed
- **Priority label** — Critical / High / Medium / Low
- **Issue details** — Category, Severity, Location
- **Authority notes** — What action has been taken
- **Assigned officer** — Who is handling it
- **Photo evidence** — Submitted photo (if any)
- **Visual timeline** — 3-step progress indicator

```
[● Submitted] ──────── [● In Progress] ──────── [○ Resolved]
     ✅                       ✅                      ⬜
```

---

### `/admin` — Authority Dashboard

**Stats Bar (live counts):**
```
[ 12 Total ]  [ 7 Pending ]  [ 3 In Progress ]  [ 2 Resolved ]
```

**Filter Controls:**
- By Status: Pending / In Progress / Resolved / Closed
- By Category: Road Damage, Flooding, Power Outage, etc.
- By Priority: Critical / High / Medium / Low

**Issue Table (sorted by Priority Score, highest first):**

| ID | Category | Location | Severity | Priority | Score | Authenticity | Status | Date |
|----|----------|----------|----------|----------|-------|--------------|--------|------|
| CIV0000003 | Flooding / Drain | MG Road | High | 🔴 Critical | 13 | High (Photo) | In Progress | 2026-09-05 |
| CIV0000001 | Road Damage | MG Road | High | 🟠 High | 9 | Low | Pending | 2026-09-05 |
| ...

---

### `/admin/issue/<id>` — Issue Detail (Authority)

Left panel — full issue info:
- Reporter name, phone, category, severity, location
- Full description
- Submitted photo

Right panel — **Update Issue**:
- Change status dropdown
- Assign to (officer/department name)
- Authority notes textarea → submitted notes are immediately visible to citizen

Priority Breakdown box:
```
Category weight    +5
Severity weight    +3
Recurrence bonus   +5
─────────────────────
Total Score        13   → 🔴 Critical
```

---

### `/analytics` — Analytics Dashboard

| Chart | What It Shows |
|-------|--------------|
| Issues by Category | Horizontal bar chart — which category is reported most |
| Resolution Status | Pill breakdown — Pending vs In Progress vs Resolved |
| Priority Distribution | Bar chart — how many Critical / High / Medium / Low |
| Top Hotspot Locations | Top 5 locations by report count — recurring problem areas |
| Daily Trend | Vertical bar chart — reports per day for last 7 days |

---

## Priority Ranking System

> This is the core of CivicAlert — it removes human bias and surfaces the most urgent issues automatically.

### Formula

```
Priority Score = Category Weight + Severity Weight + Recurrence Bonus
```

---

### Step 1 — Category Weight

Each category has a fixed weight based on **public safety impact and infrastructure criticality**:

| Category | Weight | Reason |
|----------|--------|--------|
| Road Damage | **5** | Direct accident risk, high traffic impact |
| Flooding / Drain | **5** | Health hazard, property damage, accident risk |
| Power Outage | **4** | Safety + economic disruption |
| Water Leakage | **4** | Public health + resource waste |
| Garbage Overflow | **3** | Health + sanitation concern |
| Broken Streetlight | **3** | Nighttime safety risk |
| Other | **2** | Unknown severity, handled case-by-case |

---

### Step 2 — Severity Weight

The citizen self-reports severity, which contributes an additive weight:

| Severity | Weight | Citizen Guidance |
|----------|--------|-----------------|
| High | **3** | Immediate danger, completely blocking road/drain |
| Medium | **2** | Worsening condition, partial obstruction |
| Low | **1** | Minor inconvenience, no immediate danger |

---

### Step 3 — Recurrence Bonus

The system checks how many **existing reports** exist for the **same category in the same location area**.

```python
recurrence = COUNT of issues WHERE category = X AND location LIKE '%<area>%'
bonus = min(recurrence, 5)   # capped at +5
```

**Why this matters:**
- A single pothole report = Score 8 → High Priority
- The same pothole reported 5 more times = Score 13 → Critical
- This **automatically detects persistent hotspots** without any admin intervention
- Authorities see recurring problems rise to the top naturally

---

### Step 4 — Priority Label

The final score maps to a label:

| Score | Label | Badge |
|-------|-------|-------|
| ≥ 10 | Critical | 🔴 Red |
| 7 – 9 | High | 🟠 Orange |
| 5 – 6 | Medium | 🟡 Yellow |
| < 5 | Low | 🟢 Green |

---

### Worked Example

> *"Large pothole on MG Road near bus stop" — reported as Road Damage, High severity. MG Road already has 2 prior flooding reports.*

```
Category Weight  (Road Damage)    =  5
Severity Weight  (High)           =  3
Recurrence Bonus (2 prior nearby) =  2
─────────────────────────────────────
Total Score                       = 10  →  🔴 Critical
```

> *"Broken streetlight on Park Street" — Broken Streetlight, Low severity. No prior reports.*

```
Category Weight  (Broken Streetlight) =  3
Severity Weight  (Low)                =  1
Recurrence Bonus (0 prior)            =  0
──────────────────────────────────────────
Total Score                           =  4  →  🟢 Low
```

The pothole (score 10) appears **above** the streetlight (score 4) in the authority dashboard — without anyone manually reordering anything.

---

### Why This Ranking Is Fair

| Problem | How Ranking Solves It |
|---------|----------------------|
| Loud complainers getting priority | Score is objective — severity weight is bounded at 3 |
| Old issues getting ignored | Recurrence bonus keeps increasing as more people report the same area |
| All issues looking the same | Category weight differentiates road damage (safety) from minor issues |
| Manual triage taking time | Dashboard auto-sorts by score — authority just works top-to-bottom |

---

## Authenticity Ranking

To help authorities verify issues faster, the system includes an **Authenticity** metric.
This is currently determined by the presence of photographic evidence:
- **High (Photo Attached)**: The citizen provided visual proof of the issue.
- **Low (No Photo)**: The report is text-only and unverified.

This field is visible on the authority dashboard, issue detail page, and citizen tracking page.

---

## Database Design

Single table `issues` in SQLite (`civic.db`):

```
┌──────────────────┬────────┬────────────────────────────────────────┐
│ Column           │ Type   │ Description                            │
├──────────────────┼────────┼────────────────────────────────────────┤
│ id               │ TEXT   │ Unique ID e.g. CIV3A7F2B1C            │
│ name             │ TEXT   │ Citizen's name                         │
│ phone            │ TEXT   │ Optional contact                       │
│ category         │ TEXT   │ Issue category                         │
│ severity         │ TEXT   │ High / Medium / Low                    │
│ description      │ TEXT   │ Citizen's freetext description         │
│ location         │ TEXT   │ Street, landmark, ward                 │
│ photo            │ TEXT   │ Filename saved in static/uploads/      │
│ status           │ TEXT   │ Pending / In Progress / Resolved       │
│ priority_score   │ INTEGER│ Calculated score (auto)                │
│ priority_label   │ TEXT   │ Critical / High / Medium / Low (auto)  │
│ assigned_to      │ TEXT   │ Officer/department (set by authority)  │
│ admin_notes      │ TEXT   │ Authority update (visible to citizen)  │
│ created_at       │ TEXT   │ Timestamp of report                    │
│ updated_at       │ TEXT   │ Timestamp of last update               │
└──────────────────┴────────┴────────────────────────────────────────┘
```

---

## Demo Walkthrough

**Pre-seeded issues (ready on first run):**

| Tracking ID | Issue | Location | Score | Status |
|-------------|-------|----------|-------|--------|
| `CIV0000001` | Road Damage | MG Road, Ward 5 | 9 | Pending |
| `CIV0000002` | Garbage Overflow | Gandhi Nagar | 6 | Pending |
| `CIV0000003` | Flooding / Drain | MG Road, Ward 5 | 13 | In Progress |
| `CIV0000004` | Broken Streetlight | Park Street | 4 | In Progress |
| `CIV0000005` | Water Leakage | Civil Lines | 8 | Resolved |

**Suggested demo flow:**

1. Open `/admin` → show Critical issue (CIV0000003) at the top — explain why
2. Click **View** → show the priority breakdown panel
3. Update status to "In Progress", add officer name and note
4. Switch to `/track` → enter `CIV0000003` → citizen sees the note live
5. Open `/report` → submit a new Road Damage report on "MG Road" → watch score jump due to recurrence bonus
6. Open `/analytics` → MG Road appears as top hotspot

---

*Built for Hack & Hook · PS 03.1 · CivicAlert — Smart Civic Issue Reporting & Resolution Management System*
