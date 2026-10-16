-- PREPARED ONLY: database execution was declined; not applied or verified on the live database.
-- Private editorial history. Does not expose drafts or revisions to public readers.
create schema if not exists private;
create table if not exists public.cms_event_revisions (
 id bigint generated always as identity primary key,
 city_slug text not null,
 event_id text not null,
 action text not null check (action in ('baseline','INSERT','UPDATE','DELETE')),
 before_row jsonb,
 after_row jsonb,
 actor_id uuid,
 recorded_at timestamptz not null default now()
);
create index if not exists cms_event_revisions_event_idx on public.cms_event_revisions(city_slug,event_id,id desc);
alter table public.cms_event_revisions enable row level security;
revoke all on public.cms_event_revisions from anon;
grant select,insert on public.cms_event_revisions to authenticated;
grant usage,select on sequence public.cms_event_revisions_id_seq to authenticated;
grant select,insert on public.cms_event_revisions to service_role;
grant usage,select on sequence public.cms_event_revisions_id_seq to service_role;
drop policy if exists "editors read revisions" on public.cms_event_revisions;
create policy "editors read revisions" on public.cms_event_revisions for select to authenticated using (public.can_edit_content());
drop policy if exists "trigger records revisions" on public.cms_event_revisions;
create policy "trigger records revisions" on public.cms_event_revisions for insert to authenticated with check (pg_trigger_depth()>0 and public.can_edit_content() and actor_id=auth.uid());
create or replace function private.record_cms_event_revision() returns trigger
language plpgsql security invoker set search_path='' as $$
begin
 if TG_OP='UPDATE' and NEW.payload is not distinct from OLD.payload and NEW.publication_status is not distinct from OLD.publication_status and NEW.status is not distinct from OLD.status then return NEW; end if;
 insert into public.cms_event_revisions(city_slug,event_id,action,before_row,after_row,actor_id)
 values(coalesce(NEW.city_slug,OLD.city_slug),coalesce(NEW.event_id,OLD.event_id),TG_OP,
 case when TG_OP<>'INSERT' then to_jsonb(OLD) end,
 case when TG_OP<>'DELETE' then to_jsonb(NEW) end,auth.uid());
 if TG_OP='DELETE' then return OLD; end if;
 return NEW;
end;$$;
revoke all on function private.record_cms_event_revision() from public,anon,authenticated;
drop trigger if exists cms_event_revision on public.cms_event_records;
create trigger cms_event_revision after insert or update or delete on public.cms_event_records for each row execute function private.record_cms_event_revision();
-- A baseline starts history at deployment; it does not fabricate earlier versions.
insert into public.cms_event_revisions(city_slug,event_id,action,after_row)
select r.city_slug,r.event_id,'baseline',to_jsonb(r) from public.cms_event_records r
where not exists(select 1 from public.cms_event_revisions h where h.city_slug=r.city_slug and h.event_id=r.event_id);
