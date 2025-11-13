# Instruction 0. — Mandatory Rule: Before proceeding, read and apply all numbered instructions in this file, in full, in the order listed.
# instructions:
1. Restamp and reconstruct the SANE section verbatim located at the bottom of the prior chat using Markdown following these conventions: ✅ for milestones, [x]/[ ] for checklists, Script References if applicable. Do not summarize or generalize — bring forward the exact SANE section from the prior chat.  
2. Do not rewrite any of this file's content in the current chat unless explicitly asked to do so.
3. "Stop", "Wait", and "Do nothing" all mean the same thing: stop, wait and do nothing until I, Michael, reengage.
4. When in a project, do not blast code blocks. We take 1 step at a time, not 2 or more. One!  We step 1 process, 1 T-SQL batch, and only 1 step at a time.
5. Do not write interim SANE block inside of a chat session; only at the beginning and the end when instructed to do so.
6. Read this entire file and limit the scope of the current chat session to the **project we are currently working on**.
7. Read this section, MinIO HTTPS Success Checkpoint (Confirmed), for rootCA.pem location.
8. Preserve formatting (✅ milestones, [x]/[ ] checklists, etc.) exactly as defined in Context.md (this file); at the bottom of this document is a template.  
9. Top-level headings (i.e. # WSFC Lab Context) mark the start of project sections, which end with a different project's top-level heading.
10. Ignore sections from other projects unless explicitly told to reference them.  
11. Always apply the **ChatGPT Rules, Authoring & Output Discipline** section located at the bottom of this document and any project-specific instructions when generating responses.
12. Before producing any code blocks, we must first agree upon the pseudocode that explains what we are intending to achieve or problem we are solving.
13. Stop and ask for clarification if there is any ambiguity about which project is active and what step we are focused on.
14. When analyzing, editing or writing T-SQL, review the ***T-SQL Formatting and Coding Rules*** below.
15. When writing code, T-SQL in particular, see the T-SQL Structure and Formatting rules.
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

---

### ✅ MinIO HTTPS Success Checkpoint (Confirmed)

**Date:** 2025-10-19  
**Host:** MSL-Laptop  
**Environment:** Local Windows / mkcert-signed TLS

**Status:** ✅ Verified working over HTTPS via s3fs + Delta-RS

| Component | Value |
|------------|-------|
| **Endpoint** | `https://127.0.0.1:9010` |
| **Console (UI)** | `https://127.0.0.1:9011` |
| **CA Root Path** | `C:\Users\micha\AppData\Local\mkcert\rootCA.pem` |
| **Certificate Pair in Use** | `C:\Users\micha\.minio\certs\127.0.0.1+1.pem` / `127.0.0.1+1-key.pem` |
| **Environment Variables** | <br>`AWS_ENDPOINT_URL=https://127.0.0.1:9010`<br>`AWS_CA_BUNDLE=C:\Users\micha\AppData\Local\mkcert\rootCA.pem`<br>`AWS_S3_FORCE_PATH_STYLE=1`<

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

## Milestone – 2025-09-22: Firewall & Connectivity

### Achievements
- Confirmed dynamic SQL port assignment (`51433`) via registry and netstat.
- Created inbound firewall rules on SQLNODE2 and SQLNODE3 for TCP 51433.
- Applied **Script ID: 20250922163500** to expand firewall scope to `Profile=Any`, ensuring host (10.10.20.1) connectivity.
- Applied the same script on the host laptop for outbound allowance.
- Verified connectivity with `Test-NetConnection 10.10.20.25 -Port 51433`.
- Successful first SSMS connection from host to SQL FCI using `10.10.20.25,51433`.

### Script References
- **20250922160000** – `add-sql-firewall-rule.ps1`
- **20250922163500** – `set-sql-firewall-profile-any.ps1`

### Next Steps
1. Document this milestone in lab journal and confirm entries are indexed in Context.md.
2. Perform a controlled failover to SQLNODE3; retest host connection to validate cross-node consistency.
3. Prepare data ingestion into SQL FCI for workload and failover validation.

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

# Word-clouds of Sorts

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
  - Apply only the **Word-clouds of Sorts** section; ignore unrelated project notes.
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

# T-SQL Formatting & Coding Rules
- Scope: Applies to all T-SQL in this project (views, inline TVFs, stored procedures, ad-hoc scripts).
- Naming & Identifiers
- Parameters: camelCase (e.g., @quadrant, @top, @tolerance).
- Tables & Columns: PascalCase (e.g., [dbo].[TaxiZones].[LocationID]).
- Schema Qualification & Brackets: Always schema-qualify and always bracket identifiers:
[schema].[Object], [schema].[Object].[Column].
- Object prefixes: pr_ for stored procedures, fn_ for functions (TVFs/UDFs).
## Structure & Order
- CTEs: Define in dependency order (e.g., base → geoms → rings → pts).
- Do not reference a CTE/alias before it is defined.
_ Explicit columns: Avoid SELECT *; list columns explicitly.
- Deterministic output: The outermost query that feeds files/visuals must include a final ORDER BY.
## Parameters & Sampling
- @top as percent: @top is a percentage (0–100). If @top is NULL or <= 0, treat as 100 (full set). Use parentheses and PERCENT:
```sql
SELECT TOP (@top) PERCENT ...
```
## Procedure/Function Hygiene
- SET NOCOUNT ON: Include in stored procedures.
- Parameter normalization: Trim/normalize text params early (e.g., UPPER(LTRIM(RTRIM(@quadrant)))).
- TVFs: Inline TVFs return data only; logging/side effects belong in stored procedures.
## Formatting
- Indentation: Use 2 spaces—be consistent within a file.
- CTE readability: One CTE per block; put AS ( ... ) on its own lines.
- Header comments: Each object starts with a brief header stating Purpose, Inputs, Outputs, and key Assumptions.NW: cx < centerX AND cy >= centerY

## Keyword Tabs
We use a set of standardized keywords as visual "sticky tabs" to flag important content within project notes, documentation, and blog drafts. These help us quickly scan, summarize, and extract highlights for future posts or technical write-ups.
- **Nuance** — Subtle details, edge cases, or conditions that may be overlooked but are important for correct understanding or execution.  
- **Note** — General reminders or clarifications that add context but are not critical instructions.  
- **Important** — High-priority warnings, required steps, or essential knowledge that must not be skipped.  
- **Boxit** — Code that has been tested and is ready to be saved for repeat use. Items to visually box or set apart in a future blog or doc layout (e.g., code caveats, tips, or special callouts). This includes scripts that are ready to be ID'd, saved and documented.  
- **Sticky** *(future use)* — Any other marker we define going forward; can be added here with a clear definition.
- **Guideline**: When writing notes, use these keywords consistently as the first bold word of a sentence or paragraph (e.g., `**Nuance**: A paused node is still a cluster member ...`). This makes it easier to parse later for documentation.

## Script Header Template
```powershell
# Script ID: YYYYMMDDHHMMSS
# Name: <descriptive-file-name>.ps1
# Description: <what the script does>
# Author: Michael S. Lockwood + ChatGPT
# Created: YYYY-MM-DD
# Notes: <execution notes>
```

# Status & Milestone Notation

- Use the **green box with white checkmark** emoji for accomplishments: `✅`.
- Use **GitHub-style checklists** for task status:
  - Completed items: `- [x] <task>`
  - Next steps / not done: `- [ ] <task>`
- Do **not** mix emojis inside checkboxes—use `✅` only for milestones, and `[x]/[ ]` only for task lists.
- Order of sections in updates:
  1) **Achievements & Milestones ✅** — concise, outcome-focused bullets.
  2) **Status Checklist** — split into **Completed** and **Next steps**.
- Style rules:
  - Start bullets with strong verbs (“Moved,” “Installed,” “Validated,” “Snapshotted”).
  - Name nodes/resources explicitly (e.g., **SQLNODE2**, **SQLNODE3**, **SQL FCI – Default**, **Cluster Disk 1**).
  - Include evidence when helpful (Script ID, screenshot ref, or build number).
  - Keep each section tight: **5–10 bullets max**.

# SANE Sections
Definition:
SANE = Summary of Achievements, Next steps, and Evaluation

Every chat should conclude with a SANE section. This ensures project progress is captured, validated, and ready to carry forward. A SANE combines milestones achieved, items completed, pending next steps, and any evaluation/notes for context.

Purpose:
- Maintain consistent project state across chats.
- Provide clear traceability for actions, validations, and checkpoints.
- Reduce redundancy by carrying forward only the SANE from the prior chat.

**Example Structure:**

## SANE Template
### SANE — [Topic/Phase]
### Achievements & Milestones ✅
- ✅ <milestone 1>
- ✅ <milestone 2>

#### 📝 Status Checklist
**Completed**
- [x] <completed task 1>
- [x] <completed task 2>

**Script References by ID**
- [#] <Script ID 987654321>
- [#] <Script ID 987654322>

### Next steps**
- [ ] <next step 1>
- [ ] <next step 2>

### Find the Backlog Worksheet and keep it current, maintaining all items, complete and incomplete.

### 📖 Evaluation
- Observations, issues encountered, or lessons learned.  
- Example: “CU installation was smooth; however, SQLNODE2 required a manual reboot to complete patching.”  

## T-SQL Structure and Formatting  
- Use PascalCase for table and column names.  
- Use camelCase for schema names, which are always one word anyway.  
- Use camelCase for parameters, both input and output.  
- Enclose schema, table and column names in square brackets (i.e. [schema].[table].[column).  
- Please the first column on the same line as the "SELECT" in SELECT statements (i.e. SELECT [ColumnName]),  
  a single space between [ColumnName] and the comma that follows (i.e. [ColumnName] ,),  
  use tabs or spacing equivalent to 4 spaces for subsequent columns, not for joins - see example.  
  Example:
  ```sql
  DECLARE @param varchar(40)  
  SELECT [Column1] ,  
      [Column2] ,  
      [Column3]  
  FROM [schema].[TableOne] AS t1  
      JOING [schema].[TableTwo] AS t2  
          ON t1.[ColumnK] = t2.[ColumnK]
  ```  
  WHERE t2.[ColumnL] = @param  
  - Note that this will be expanded if code blocks begin to drift in terms of formatting.
  - End of Section  




















