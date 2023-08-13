create role docs_user;

create database docs;

\connect docs;

-- users
create table users (
    id      serial primary key,
    created timestamptz not null default now(),
    login   text not null check (length(login) between 1 and 12 and login ~* '^\w+$') unique,
    pass    text not null check (length(pass) between 1 and 12 and pass ~* '^\w+$'),
    org     text not null check (length(org) between 1 and 12 and org ~* '^\w+$')
);

create index on users (login);

grant select (id, login, org) on users to docs_user;
grant update (org) on users to docs_user;

alter table users enable row level security;
create policy p1 on users to docs_user using (true) with check (login = current_user);

-- docs
create table docs (
    id      serial primary key,
    created timestamptz not null default now(),
    title   text not null check (length(title) between 1 and 32) unique,
    owner   integer not null references users(id),
    shares  integer[] not null default array[]::integer[]
);

create function set_owner() returns trigger as $set_owner$
begin
    new.owner = (select id from users as u where u.login = current_user);
    return new;
end;
$set_owner$ language plpgsql;

create trigger set_owner before insert on docs
    for each row execute function set_owner();

grant select on docs to docs_user;
grant update (shares) on docs to docs_user;
grant insert (title, shares) on docs to docs_user;
grant usage on docs_id_seq to docs_user;

alter table docs enable row level security;
create policy p1 on docs to docs_user using (
    (select login from users as u where owner = u.id) = current_user
);
create policy p2 on docs to docs_user using (
    (select id from users as u where current_user = u.login) = any(shares)
);
create policy p3 on docs to docs_user using (
    (select org from users as u where current_user = u.login)
    = (select org from users as u where owner = u.id)
);

-- contents
create table contents (
    id      serial primary key,
    created timestamptz not null default now(),
    doc_id  integer not null references docs(id) unique,
    data    text not null check (length(data) between 1 and 4096)
);

create index on contents (doc_id);

grant select on contents to docs_user;
grant update (data) on contents to docs_user;
grant insert (doc_id, data) on contents to docs_user;
grant usage on contents_id_seq to docs_user;

alter table contents enable row level security;
create policy p1 on contents to docs_user using (
    (select login from users as u where (select owner from docs as d where d.id = doc_id) = u.id)
    = current_user
);
create policy p2 on contents to docs_user using (
    (select id from users as u where current_user = u.login)
    in (select unnest(shares) from docs as d where d.id = doc_id)
);
create policy p3 on contents as restrictive to docs_user with check (
    (select id from users as u where current_user = u.login)
    not in (select unnest(shares) from docs as d where d.id = doc_id)
);
