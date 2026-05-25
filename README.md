# 0) Bài toán cần giải quyết (Problem Statement)

**Xây dựng một data platform cho Digital Wallet (fintech) đảm bảo:**
1. **Ledger immutability**: giao dịch không update, chỉ append; sửa sai bằng reversal/adjustment.
2. **Balance derivation**: số dư không là “source of truth”; balance phải **tính lại được từ ledger**.
3. **Reconciliation & audit**: bất kỳ ngày nào cũng kiểm tra được:
    - tổng debit/credit hợp lệ
    - snapshot balance khớp ledger
    - truy vết “vì sao số dư thành như vậy”
4. Có **realtime ingestion** để demo + **batch ELT** để build marts và report.

---

# 1) Definition phase: Data semantics trước (không đụng tool)

## 1.1 Chốt scope nghiệp vụ (Deliverable: 1 trang spec)

- [ ]  Chọn loại ví: **single-currency** (VND) để đơn giản
- [ ]  Chọn entities: `customer`, `wallet_account`
- [ ]  Chọn transaction types tối thiểu (5 loại):
    - [ ]  `topup` (credit)
    - [ ]  `purchase` (debit)
    - [ ]  `refund` (credit)
    - [ ]  `transfer` (debit + credit 2 ví)
    - [ ]  `adjustment` (manual)
- [ ]  Quy tắc “không update”: sai thì dùng `reversal_txn_id` hoặc tạo `adjustment`

**Output:** `docs/problem_and_scope.md`

## 1.2 Định nghĩa invariant (Deliverable: checklist rules)

- [ ]  `transaction_id` unique
- [ ]  Amount > 0
- [ ]  Mọi txn phải có `event_time`, `ingest_time`
- [ ]  Transfer tạo **2 entries** (from debit, to credit) và liên kết cùng `transfer_id`
- [ ]  Không được phép “số dư âm” (hoặc cho phép âm? chọn 1 và ghi rõ)

**Output:** `docs/invariants.md`

---

# 2) Data model phase: Ledger-first (cốt lõi fintech)

## 2.1 Thiết kế schema (Deliverable: ERD + DDL draft)

- [ ]  `bronze_wallet_events` (raw)
- [ ]  `silver_wallet_transactions` (cleaned)
- [ ]  `gold_ledger_entries` (double-entry style simplified)
- [ ]  `gold_balance_snapshot_daily`
- [ ]  `gold_reconciliation_results`

**Output:** `docs/data_model.md` (kèm diagram)

## 2.2 Quy tắc tính balance (Deliverable: pseudo-SQL)

- [ ]  Balance tại thời điểm T = SUM(credits) - SUM(debits) đến T
- [ ]  Snapshot daily: end-of-day per account
- [ ]  Late events: chọn rule (theo `event_time` hay `ingest_time`?) và ghi rõ

**Output:** `docs/balance_logic.md`

---

# 3) Platform skeleton: Local-first infra (nhẹ nhưng chuẩn)

## 3.1 Repo + môi trường (Deliverable: chạy được infra)

- [ ]  Setup WSL2 Ubuntu + Docker (WSL backend)
- [ ]  Tạo repo structure: `infra/ generator/ batch/ quality/ docs/`
- [ ]  Tạo `Makefile`: `make up`, `make down`, `make logs`

**Output:** repo chạy được lệnh khởi động

## 3.2 Docker Compose minimal (Deliverable: services up)

- [ ]  Kafka + Kafka UI
- [ ]  MinIO
- [ ]  Postgres
- [ ]  (Tuỳ chọn sau) Airflow

**Output:** `docker compose up` OK

---

# 4) Data generation: tạo dữ liệu đúng semantics

## 4.1 Generator spec (Deliverable: schema JSON)

- [ ]  Define event JSON v1:
    - `event_id`, `event_time`, `ingest_time`
    - `transaction_id`, `account_id`, `customer_id`
    - `txn_type`, `amount`, `direction`
    - `currency`, `status`
    - `ref_txn_id` (cho refund/reversal)
    - `transfer_id` (cho transfer)

**Output:** `docs/event_schema_v1.json`

## 4.2 Implement generator → Kafka (Deliverable: data chạy liên tục)

- [ ]  Python producer bắn events theo tỉ lệ:
    - topup/purchase nhiều, refund ít, adjustment rất ít
- [ ]  Inject lỗi có kiểm soát (để test quality):
    - duplicate transaction_id
    - amount âm
    - missing account_id

**Output:** `generator/` chạy 1 lệnh là bắn data

---

# 5) Streaming ingestion: Kafka → Bronze (realtime demo)

## 5.1 Kafka Connect S3 Sink → MinIO (Deliverable: bronze files)

- [ ]  Cấu hình sink ghi `bronze/wallet_events/event_date=...`
- [ ]  Append-only

**Output:** MinIO có file tăng theo thời gian

## 5.2 Basic observability (Deliverable: demo lag)

- [ ]  Kafka UI kiểm tra throughput / consumer lag

**Output:** screenshot/notes trong `docs/demo.md`

---

# 6) Batch ELT: Bronze → Silver → Gold bằng dbt + DuckDB/Postgres

## 6.1 Silver transformations (Deliverable: bảng sạch)

- [ ]  Parse raw → typed columns
- [ ]  Dedup theo `transaction_id` (hoặc event_id, tuỳ rule)
- [ ]  Normalize sign: credit(+), debit(-)
- [ ]  Validate basic constraints (lọc hoặc gắn cờ invalid)

**Output:** `silver_wallet_transactions`

## 6.2 Gold ledger entries (Deliverable: ledger đúng)

- [ ]  Tạo `gold_ledger_entries`:
    - 1 txn → 1 entry (simplified) hoặc 2 entries (double-entry)
- [ ]  Với transfer: tạo 2 entries debit/credit

**Output:** ledger entries query ra hợp lý

## 6.3 Balance snapshots + reconciliation (Deliverable: đúng “fintech”)

- [ ]  `gold_balance_snapshot_daily`
- [ ]  `gold_reconciliation_results`:
    - check: debit/credit totals
    - check: snapshot = sum(entries)
    - count invalid txns

**Output:** báo cáo reconcile theo ngày

## 6.4 dbt tests + docs (Deliverable: professional)

- [ ]  unique/not null tests
- [ ]  accepted values tests
- [ ]  dbt docs generate

**Output:** `dbt test` pass + docs site

---

# 7) Orchestration: chạy theo lịch (Airflow hoặc cron)

## 7.1 Airflow local (Deliverable: DAG)

- [ ]  DAG chạy `dbt run` → `dbt test`
- [ ]  Lịch mỗi 15 phút/1 giờ

**Output:** Airflow UI có lịch sử run

---

# 8) Serving & Dashboard demo

## 8.1 Publish Gold sang Postgres (Deliverable: BI connect)

- [ ]  Materialize gold tables vào Postgres schema `mart`

## 8.2 Dashboard (Deliverable: demo business + audit)

- [ ]  Realtime-ish: transaction count per minute
- [ ]  Daily balance per account
- [ ]  Reconciliation status (pass/fail)
- [ ]  Top accounts by volume

**Output:** file PBIX hoặc dashboard Metabase

---

# 9) Extension

- [ ]  Exactly-once / idempotency strategy (dedup keys, outbox pattern)
- [ ]  Late-event policy (event_time vs ingest_time) + backfill
- [ ]  Slowly changing customer/account attributes (SCD2)
- [ ]  Lineage/metadata (OpenLineage)
- [ ]  Monitoring (Prometheus/Grafana)
- [ ]  Data privacy masking (PII)

# 10) Rule for commit
    [FEAT] add new feature
    [FIX] fix bug
    [CONFIG] update project configuration
    [DOCS] update documentation
    [TEST] add or update tests
    [REFACTOR] refactor code structure