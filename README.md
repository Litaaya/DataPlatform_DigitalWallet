# Digital Wallet Data Platform (Fintech Case Study)

An end-to-end production-grade data platform designed for a single-currency (USD) Digital Wallet. This project focuses on solving core financial data engineering challenges: **Ledger Immutability**, **Deterministic Balance Derivation**, and **Automated Daily Reconciliation**.

---

## Data Architecture (will be drawn completely later)

The platform implements a Medallion Architecture combining real-time streaming ingestion and batch ELT processing:

Raw Events (App) ──> Kafka ──(Kafka Connect S3 Sink)──> MinIO (Bronze / Parquet)
                                                           │
                                                      (dbt + DuckDB)
                                                           │
Postgres (Mart / Serving) <── Gold (Ledger & Recon) <── Silver (Cleaned)
         │
  (Metabase/PowerBI)

## Documentation:
For detailed business requirements, accounting rules, and constraints:
- [Business Problem and Scopes](docs/problem_and_scope.md)
- [Data Invariants and Quality Rules](docs/invariants.md)
- [Data Model: Schema Design](docs/data_model.md)
- [Data Model: Balance Logic](docs/balance_logic.md)

## Tech Stack and Core Concepts:
- Infrastructure: Docker & WSL2 (Ubuntu) for localized environment orchestration.
- Streaming Ingestion: Apache Kafka & Kafka UI for event streaming; Kafka Connect (S3 Sink) for landing raw events.
- Storage / Data Lake: MinIO (S3-compatible object storage) storing append-only historical Parquet files.
- Compute / Transformation: DuckDB for lightning-fast OLAP processing embedded within dbt (Data Build Tool) for modular SQL modeling.
- Serving Layer: PostgreSQL for production data mart rendering.
- Data Quality & Audit: Built-in dbt data tests alongside custom Double-Entry Ledger Reconciliation pipelines.

## Setup (incoming)
- ...

## Roadmap and Progress
- Phase 1: Definition & Data Semantics:
- [x] 1.1 Business Scope: Defined core entities and 5 transaction types. (docs/problem_and_scope.md)
- [x] 1.2 Invariants Checklist: Formulated data integrity rules. (docs/invariants.md)

- Phase 2: Data Model Layer
- [ ] 2.1 Schema Design: Drafted Medallion architecture (Bronze/Silver/Gold). (docs/data_model.md)
- [ ] 2.2 Balance Logic: Designed pseudo-SQL for historical balance derivation. (docs/balance_logic.md)

- Phase 3: Platform Skeleton (Infra)
- [ ] 3.1 Repo Setup: Initialized WSL2, directory structure, and Makefile.
- [ ] 3.2 Docker Compose: Containers for Kafka, MinIO, and Postgres are running.

- Phase 4: Data Generation
- [ ] 4.1 Generator Spec: Event JSON v1 schema defined.
- [ ] 4.2 Python Producer: Capable of streaming valid/invalid transactions into Kafka.

- Phase 5: Streaming Ingestion
- [ ] 5.1 S3 Sink: Kafka Connect successfully streams data into MinIO partition by date.
- [ ] 5.2 Observability: Monitoring consumer lag via Kafka UI.

- Phase 6: Batch ELT (dbt + DuckDB)
- [ ] 6.1 Silver Layer: Deduplication and type casting logic implemented.
- [ ] 6.2 Gold Layer: Double-entry ledger generation setup.
- [ ] 6.3 Reconciliation: Auto daily auditing logic developed.
- [ ] 6.4 Data Quality: Passed all unique, not_null, and accepted_values dbt tests.

- Phase 7 & 8: Orchestration & Dashboard
- [ ] 7.1 DAG Scheduling: Orchestrated pipeline runs via Airflow/Cron.
- [ ] 8.1 Data Mart: Materialized Gold layer into PostgreSQL.
- [ ] 8.2 Analytics: Built financial audit dashboard via Metabase/PowerBI.

- Phase 9: Advanced Extensions
- [ ] Idempotency / Exactly-once strategy.
- [ ] Late-event backfilling policy.

## Convention Commits Rule
- [FEAT] - New features/pipelines.
- [FIX] - Bug fixes.
- [CONFIG] - Infra or project setup updates.
- [DOCS] - Documentation updates.
- [TEST] - Adding/updating quality tests.
- [REFACTOR] - Code restructuring without logic changes.