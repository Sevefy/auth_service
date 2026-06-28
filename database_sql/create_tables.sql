-- public.sessions определение
-- Drop table
-- DROP TABLE public.sessions;

create table public.sessions (
	user_id int4 not null,
	"token" uuid not null,
	id serial4 not null,
	expire_token timestamptz not null,
	constraint sessions_pkey primary key (id)
);
-- public.sessions внешние включи

alter table public.sessions add constraint session_user_id_fkey foreign key (user_id) references public.users(id);


-- public.users определение
-- Drop table
-- DROP TABLE public.users;

create table public.users (
	id int4 default nextval('user_id_seq'::regclass) not null,
	username varchar(50) not null,
	"password" varchar(128) not null,
	created_at timestamp default CURRENT_TIMESTAMP null,
	constraint user_pkey primary key (id),
	constraint user_username_key unique (username)
);

create unique index users_username_idx on
public.users
    using btree (username,
password);
