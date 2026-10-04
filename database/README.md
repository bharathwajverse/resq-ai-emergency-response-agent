# ResQ-AI Database Setup

1. Install PostgreSQL.
2. Create a database `resq_ai`.
3. Run `psql -d resq_ai -f schema.sql` to create tables and schema.
4. Run `psql -d resq_ai -f seed.sql` to insert seed data.
