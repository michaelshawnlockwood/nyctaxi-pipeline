# Lab Context

Central reference file for tracking the state of the lab environment, active issues, priorities, and script inventory.  
Keep this updated at the end of each working session.

---

## 🖥️ Lab State

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
