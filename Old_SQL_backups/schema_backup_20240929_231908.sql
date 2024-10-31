CREATE TABLE policy (
    id integer NOT NULL DEFAULT nextval('policy_id_seq'::regclass),
    created_at timestamp without time zone,
    internal_id uuid NOT NULL DEFAULT gen_random_uuid(),
    club_id integer,
    klubb character varying(100) NOT NULL,
    policy_content text NOT NULL
);

CREATE TABLE schema_migrations (
    executed_at timestamp without time zone NOT NULL DEFAULT now(),
    filename character varying(512) NOT NULL,
    checksum character varying(32) NOT NULL
);

CREATE TABLE signature (
    id integer NOT NULL DEFAULT nextval('signature_id_seq'::regclass),
    datum timestamp without time zone,
    internal_id uuid NOT NULL DEFAULT gen_random_uuid(),
    club_id integer,
    email character varying(100) NOT NULL,
    namn character varying(100) NOT NULL,
    klubb character varying(100) NOT NULL,
    position character varying(100) NOT NULL
);

CREATE TABLE sent_email (
    club_id integer,
    date timestamp without time zone,
    internal_id uuid NOT NULL DEFAULT gen_random_uuid(),
    id integer NOT NULL DEFAULT nextval('sent_email_id_seq'::regclass),
    status character varying(50) NOT NULL,
    klubb character varying(100) NOT NULL,
    name character varying(100) NOT NULL,
    email character varying(100) NOT NULL
);

CREATE TABLE alembic_version (
    version_num character varying(32) NOT NULL
);

CREATE TABLE club (
    id integer NOT NULL DEFAULT nextval('club_id_seq'::regclass),
    name character varying(100) NOT NULL
);

