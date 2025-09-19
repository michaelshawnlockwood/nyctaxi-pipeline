# Instructions for Use

This `Context.md` file applies only to the **current active project**.  
When starting a new chat, ChatGPT must:

1. Upon reading this file, do not rewrite any of its content in the current chat unless the content or content structure is being discussed.
2. You may reiterate ***Current State*** and ***Next Steps*** of the **project we are currently working on**.
3. Read this file and limit its scope to the **project we are currently working on**.
4. Top-level headings (i.e. # WSFC Lab Context) mark the start of project sections, which end with a different project's top-level heading.
5. Ignore sections from other projects unless explicitly told to reference them.  
6. Always apply the **ChatGPT Rules, Authoring & Output Discipline** section located at the bottom and any project-specific instructions before generating responses.  
7. Stop and ask for clarification if there is any ambiguity about which project is active.

---

# WSFC Lab Context

Central reference file for tracking the state of the lab environment, active issues, priorities, and script inventory.  
Keep this updated at the end of each working session.

---

## 🖥️ WSFC Lab State

- **SQLNODE1**  
  - Role: Domain Controller / DNS only  
  - Status: Domain healthy, DNS zone `lab.local` confirmed  
  - Shares: Host shares reconnected via persistent drive mappings  
  - Last snapshot: `LastKnownGoodConfig-share-attached`

- **SQLNODE2**  
  - Role: Domain-joined member server, clean pre-SQL  
  - Status: Static IP configured, joined to `lab.local`  
  - Last snapshot: Pending `Baseline-preSQL`

- **SQLNODE3**  
  - Role: Fresh clone from SQLNODE2 (export → import w/ new ID)  
  - Status: Not yet joined to domain, needs IP and DNS verified  
  - Last snapshot: Pending `Baseline-preSQL`

---

## 🎯 Next Priorities

1. Verify **SQLNODE3** static IP, gateway, DNS → `SQLNODE1`.  
2. Test connectivity with `ping`, `nslookup`, `nltest`.  
3. Join SQLNODE3 to `lab.local` domain.  
4. Snapshot both **SQLNODE2** and **SQLNODE3** as `Baseline-preSQL` once domain joined.  
5. Prepare for SQL Server installation on SQLNODE2 and SQLNODE3.  

---

## ⚠️ Open Issues

- **Retry-on-bad-password mapping script**: misaligned with pseudocode. Shares working now, revisit if reusability matters.  
- **PS7 vs PS5 execution**: One script crash traced to running in PS7 on a VM. Need to standardize which runtime is expected.  
- **File shares visibility**: SQLNODE1 temporarily lost access until remapped. Working now but fragile if host IP/hostname shifts.  

---

## 📸 Snapshots

- **SQLNODE1**  
  - `LastKnownGoodConfig-share-attached`  

- **SQLNODE2**  
  - [pending] `Baseline-preSQL`  

- **SQLNODE3**  
  - [pending] `Baseline-preSQL`  

---

## 📜 Scripts Inventory

**Admin / VM Management**

- `disable-auto-checkpoints.ps1` – Disable automatic checkpoints for a VM.  
- `set-processor-count.ps1` – Adjust vCPU count for a VM.  
- `create-checkpoint.ps1` – Replace/create a named VM checkpoint.  
- `revert-checkpoint.ps1` – Roll back a VM to a specific checkpoint.  

**Networking / System**

- `set-name-n-ip.ps1` – Configure static IP and computer name.  
- `network-status.ps1` – Check IPs, routes, adapters.  
- `system-status.ps1` – Check computer name, domain/workgroup, OS build.  

**Shares / Mapping**

- `ensure-share-winvm.ps1` – Ensures host exposes a share and reports UNC path.  
- `map-share-retry.ps1` – Map SMB shares with retry/timeout logic (needs refinement).  

**Misc**

- `netstat-linux.ps1` – Linux netstat check (early draft, pending robustness).  

---

## 🗂️ Notes on Context Gathering

- End-of-chat handoff blocks (✅ Summary / 📌 Context) → paste here.  
- Backfill from prior chats as needed.  
- This file = single source of truth across sessions.  

2025-09-16 — WSFC Disk Correlation
Script: 20250916194500 correlate-cluster-disks.ps1 (requires Windows PowerShell 5.x)
Verified: Cluster Disk 1→E: SQLData, Disk 2→F: SQLLog, Disk 3→G: SQLBackup (NTFS, 64KB)
Note: PS7 may not expose DiskIdGuid; use PS5.x for this script.


## WSFC Lab Context Central reference file for tracking the state of the lab environment, active issues, priorities, and script inventory. Keep this updated at the end of each working session.
--- ## ️ Lab State - **SQLNODE1** - Role: Domain Controller / DNS only - Status: Domain healthy, DNS zone `lab.local` confirmed - Shares: Host shares reconnected via persistent drive mappings - Last snapshot: `LastKnownGoodConfig-share-attached` - **SQLNODE2** - Role: Domain-joined member server, clean pre-SQL - Status: Static IP configured, joined to `lab.local` - Last snapshot: Pending `Baseline-preSQL` - **SQLNODE3** - Role: Fresh clone from SQLNODE2 (export → import w/ new ID) - Status: Not yet joined to domain, needs IP and DNS verified - Last snapshot: Pending `Baseline-preSQL` --- ## Next Priorities 1.
Verify **SQLNODE3** static IP, gateway, DNS → `SQLNODE1`. 2. Test connectivity with `ping`, `nslookup`, `nltest`. 3. Join SQLNODE3 to `lab.local` domain. 4. Snapshot both **SQLNODE2** and **SQLNODE3** as `Baseline-preSQL` once domain joined. 5. Prepare for SQL Server installation on SQLNODE2 and SQLNODE3. --- ## ⚠️ Open Issues - **Retry-on-bad-password mapping script**: misaligned with pseudocode. Shares working now, revisit if reusability matters.
- **PS7 vs PS5 execution**: One script crash traced to running in PS7 on a VM. Need to standardize which runtime is expected. - **File shares visibility**: SQLNODE1 temporarily lost access until remapped. Working now but fragile if host IP/hostname shifts.
--- ## Snapshots - **SQLNODE1** - `LastKnownGoodConfig-share-attached` - **SQLNODE2** - [pending] `Baseline-preSQL` - **SQLNODE3** - [pending] `Baseline-preSQL` --- ## Scripts Inventory **Admin / VM Management** - `disable-auto-checkpoints.ps1` – Disable automatic checkpoints for a VM. - `set-processor-count.ps1` – Adjust vCPU count for a VM. - `create-checkpoint.ps1` – Replace/create a named VM checkpoint. - `revert-checkpoint.ps1` – Roll back a VM to a specific checkpoint.
**Networking / System** - `set-name-n-ip.ps1` – Configure static IP and computer name. - `network-status.ps1` – Check IPs, routes, adapters. - `system-status.ps1` – Check computer name, domain/workgroup, OS build. **Shares / Mapping** - `ensure-share-winvm.ps1` – Ensures host exposes a share and reports UNC path. - `map-share-retry.ps1` – Map SMB shares with retry/timeout logic (needs refinement). **Misc** - `netstat-linux.ps1` – Linux netstat check (early draft, pending robustness).
--- ## ️ Notes on Context Gathering - End-of-chat handoff blocks (✅ Summary / Context) → paste here. - Backfill from prior chats as needed. - This file = single source of truth across sessions. 2025-09-16 — WSFC Disk Correlation Script: 20250916194500 correlate-cluster-disks.ps1 (requires Windows PowerShell 5.x) Verified: Cluster Disk 1→E: SQLData, Disk 2→F: SQLLog, Disk 3→G: SQLBackup (NTFS, 64KB) Note: PS7 may not expose DiskIdGuid; use PS5.x for this script.

# Runbook Checkpoint

## Script ID: 20250917001000
## Step: TempDB Local Path Warning
**Description:** During SQL Server FCI setup, selecting a local path for TempDB (`C:\SQLTEMPDB`) generates a warning.  
- This is **expected**.  
- Requirement: Ensure the same path exists with correct ACLs (`lab.local\svc-sql` granted Modify) on **all cluster nodes**.  
- Action: Click **Yes** to proceed.  

![TempDB Warning](ac4ced6e-a20d-4ef9-a3c1-bdc34b1a3631.png)

---

## Step: Install Complete
**Description:** SQL Server 2022 Failover Cluster Instance installation succeeded on SQLNODE3.  
- Resource group created: `SQL FCI - Default`  
- Disks E:, F:, G: now owned by the SQL FCI role  
- Services (SQL Engine, Agent, Browser) installed under domain accounts  
- Instance is ready for **post-install verification**  

![Install Complete](1a4f8e6e-3b04-4126-ab63-c35d9107d91e.png)

✅ **Checkpoint reached.** Safe to snapshot VM or mark LKGC (Last Known Good Config).

---

# Wordclouds of Sorts

## Achievements
- Using PowerShell to write geoJSON file directly from SQL Server. 
- Confirmed that the **GeoJSON structure** must be a FeatureCollection with Polygon or MultiPolygon geometries, not Point geometries.

## Current Challenges

- **Validation of exported GeoJSON**: Ensuring the PowerShell-exported file is structurally correct (FeatureCollection, geometry types, properties present, coordinate order).
- **File naming discipline**: Avoiding filename thrash and enforcing the canonical file path in all references.
- **Map rendering baseline**: Achieving a first working D3 map render (zones visible, no tooltips/legends yet).
- **Output discipline**: Preventing cluttered chats by enforcing single-block or text-only outputs per the rules.
- **Context carryover**: Building the habit that ChatGPT reads `Context.md` at the start of every chat and applies only the active project section.

## Next Steps

- **Validate GeoJSON Export**
  - Confirm exported file is a valid FeatureCollection.
  - Check geometry types (Polygon or MultiPolygon) and coordinate order ([longitude, latitude]).
  - Ensure required properties (`LocationID`, `zone`, `borough`) exist and `LocationID` values are unique.

- **Establish a Baseline Map Render**
  - Load the canonical `taxi_zones_4326.geojson` file.
  - Verify that all zones display (even those with metric = 0).
  - Do not add tooltips, legends, or styles until the base render is confirmed working.

- **Context Discipline**
  - Apply only the **Wordclouds of Sorts** section; ignore unrelated project notes.
  - Re-read `Context.md` at the start of every new chat.
  - Follow the Rules section strictly (single multi-page code block, no clutter, HARD STOP compliance).

- **Documentation Hygiene**
  - Keep file path, naming, and join key (`LocationID`) consistent across all notes and outputs.
  - Update `Context.md` immediately when rules, file locations, or scope change.

- **Future Enhancements (after baseline render)**
  - Introduce tooltips with zone/borough/metric values.
  - Add color scales for choropleth representation.
  - Explore externalizing JS and styles only after baseline reliability is achieved.

---

# ChatGPT Rules, Authoring & Output Discipline

## 1) Code-Block Policy
- A **single code block that spans multiple pages is allowed**.  
- **Multiple code blocks that, in total, span more than one page are not allowed.**  
- **Rationale:** Long chats get cluttered and more than 80% of ChatGPT's output ends up ignored. This must be avoided.

## 2) Phase & Scope
- Work only on the current **phase** (e.g., “Validation only”, “Pseudocode only”, “Render baseline only”).  
- Do **not** add extras (tooltips, legends, styling) until the **base map renders** correctly.

## 3) Output Mode & Length
- The request will declare an **OUTPUT MODE**: {Summary, Checklist, Pseudocode, Single Code Block}.  
- Respect the declared **MAX LENGTH**. If unclear, keep it terse.

## 4) File & Data Canon
- Canonical zones file path: `assets/data/taxi_zones_4326.geojson` (WGS84 / EPSG:4326).  
- Required per-feature properties: `LocationID` (int), `zone` (string), `borough` (string).  
- Join key: `LocationID` only. Missing metrics render as **0**; zones must still draw.

## 5) Validation Gate (must pass before any D3 work)
- Top level is `FeatureCollection` with `features[]`.  
- Geometry types are `Polygon` or `MultiPolygon`.  
- Coordinates are `[longitude, latitude]` (WGS84).  
- `LocationID` is unique across all features; coverage aligns with TLC zones.

## 6) Change Management
- No renames of files/keys without updating `Context.md` first.  
- Document each change with: **what changed, why, and its impact**.

## 7) Ambiguity & Stop Word
- If something is ambiguous, return **one clarifying question and stop**.  
- If the user types **HARD STOP**, immediately stop output.












