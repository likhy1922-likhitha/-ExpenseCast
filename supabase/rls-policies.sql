-- ExpenseCast Row-Level Security policies
--
-- Applies to the Supabase Postgres project once backend/alembic migrations
-- (or the equivalent supabase/migrations/*.sql) have created the tables.
-- Assumes each personal table has a `user_id` column equal to
-- auth.uid() (Supabase's built-in current-user function), matching the
-- backend's `User.id` primary key (see backend/app/models/user_models.py).
--
-- Run in the Supabase SQL editor, or via `supabase db push`.

-- Enable RLS on every personal table.
alter table users enable row level security;
alter table user_profiles enable row level security;
alter table accounts enable row level security;
alter table transactions enable row level security;
alter table budgets enable row level security;
alter table savings_goals enable row level security;
alter table goal_contributions enable row level security;
alter table investments enable row level security;
alter table recurring_transactions enable row level security;
alter table category_rules enable row level security;
alter table imported_files enable row level security;
alter table import_batches enable row level security;
alter table import_errors enable row level security;
alter table predictions enable row level security;
alter table notifications enable row level security;
alter table user_settings enable row level security;
alter table audit_logs enable row level security;

-- categories is a special case: rows with user_id IS NULL are global
-- defaults readable by everyone; rows with a user_id are private.
alter table categories enable row level security;

-- --- users ---
create policy "Users can view own row" on users
  for select using (auth.uid() = id);
create policy "Users can update own row" on users
  for update using (auth.uid() = id);
create policy "Users can delete own row" on users
  for delete using (auth.uid() = id);

-- --- user_profiles ---
create policy "Users manage own profile" on user_profiles
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- --- accounts ---
create policy "Users manage own accounts" on accounts
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- --- categories (global defaults + own custom categories) ---
create policy "Anyone can read default categories" on categories
  for select using (user_id is null or auth.uid() = user_id);
create policy "Users manage own custom categories" on categories
  for insert with check (auth.uid() = user_id);
create policy "Users update own custom categories" on categories
  for update using (auth.uid() = user_id);
create policy "Users delete own custom categories" on categories
  for delete using (auth.uid() = user_id);

-- --- transactions ---
create policy "Users manage own transactions" on transactions
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- --- budgets ---
create policy "Users manage own budgets" on budgets
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- --- savings_goals ---
create policy "Users manage own goals" on savings_goals
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- --- goal_contributions ---
create policy "Users manage own goal contributions" on goal_contributions
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- --- investments ---
create policy "Users manage own investments" on investments
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- --- recurring_transactions ---
create policy "Users manage own recurring transactions" on recurring_transactions
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- --- category_rules (global system rules readable by all, user rules private) ---
create policy "Anyone can read system category rules" on category_rules
  for select using (user_id is null or auth.uid() = user_id);
create policy "Users manage own category rules" on category_rules
  for insert with check (auth.uid() = user_id);
create policy "Users update own category rules" on category_rules
  for update using (auth.uid() = user_id);
create policy "Users delete own category rules" on category_rules
  for delete using (auth.uid() = user_id);

-- --- imports ---
create policy "Users manage own imported files" on imported_files
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "Users manage own import batches" on import_batches
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "Users view own import errors" on import_errors
  for select using (
    exists (
      select 1 from import_batches b
      where b.id = import_errors.import_batch_id and b.user_id = auth.uid()
    )
  );

-- --- predictions ---
create policy "Users view own predictions" on predictions
  for select using (auth.uid() = user_id);
create policy "Users insert own predictions" on predictions
  for insert with check (auth.uid() = user_id);

-- --- notifications ---
create policy "Users manage own notifications" on notifications
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- --- user_settings ---
create policy "Users manage own settings" on user_settings
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- --- audit_logs (read-only for the owning user; writes only via backend
--     service-role key, never directly from the client) ---
create policy "Users view own audit logs" on audit_logs
  for select using (auth.uid() = user_id);

-- Note: the FastAPI backend authenticates to Postgres using the Supabase
-- service-role key (bypasses RLS) for the demo-mode seeding job and for
-- any background jobs; all *user-facing* API calls go through the
-- get_current_user() dependency, which additionally filters every query
-- by user_id at the application layer -- so isolation is enforced twice
-- (RLS + application-level filtering) for defense in depth.
