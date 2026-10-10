-- ISNET media catalogue v2: apply manually to the existing Supabase project.
-- No public bucket: images are private until explicitly reviewed and published.
create table if not exists public.isnet_media_assets (
 asset_id text primary key,
 asset_type text not null check(asset_type in ('event_poster','artist','production','venue','subcategory','category')),
 title text not null default '',
 original_url text not null,
 source_url text not null,
 source_id text,
 object_path text unique,
 stored_url text,
 content_sha256 text,
 rights_status text not null default 'unknown' check (rights_status in ('verified','permission_required','unknown','expired')),
 image_credit text,
 licensed_until date,
 width integer check(width>0),
 height integer check(height>0),
 tags text[] not null default '{}',
 subjects text[] not null default '{}',
 related_event_ids text[] not null default '{}',
 reviewer uuid references auth.users(id),
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 constraint verified_assets_require_reviewer check(rights_status <> 'verified' or reviewer is not null)
);
create index if not exists isnet_media_subjects_idx on public.isnet_media_assets using gin(subjects);
create index if not exists isnet_media_event_ids_idx on public.isnet_media_assets using gin(related_event_ids);
alter table public.isnet_media_assets enable row level security;
revoke all on public.isnet_media_assets from anon;
grant select,insert,update on public.isnet_media_assets to authenticated;
drop policy if exists isnet_media_admin_read on public.isnet_media_assets;
create policy isnet_media_admin_read on public.isnet_media_assets for select to authenticated
using (exists(select 1 from public.admin_users a where a.user_id = auth.uid()));
drop policy if exists isnet_media_admin_insert on public.isnet_media_assets;
create policy isnet_media_admin_insert on public.isnet_media_assets for insert to authenticated
with check (exists(select 1 from public.admin_users a where a.user_id = auth.uid()));
drop policy if exists isnet_media_admin_update on public.isnet_media_assets;
create policy isnet_media_admin_update on public.isnet_media_assets for update to authenticated
using (exists(select 1 from public.admin_users a where a.user_id = auth.uid()))
with check (exists(select 1 from public.admin_users a where a.user_id = auth.uid()));
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values('isnet-event-media','isnet-event-media',false,5242880,array['image/jpeg','image/png','image/webp'])
on conflict(id) do nothing;
drop policy if exists isnet_event_media_admin_read on storage.objects;
create policy isnet_event_media_admin_read on storage.objects for select to authenticated
using(bucket_id='isnet-event-media' and exists(select 1 from public.admin_users a where a.user_id=auth.uid()));
drop policy if exists isnet_event_media_admin_insert on storage.objects;
create policy isnet_event_media_admin_insert on storage.objects for insert to authenticated
with check(bucket_id='isnet-event-media' and exists(select 1 from public.admin_users a where a.user_id=auth.uid()));
