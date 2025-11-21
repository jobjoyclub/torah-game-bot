--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (415ebe8)
-- Dumped by pg_dump version 17.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: _system; Type: SCHEMA; Schema: -; Owner: neondb_owner
--

CREATE SCHEMA _system;


ALTER SCHEMA _system OWNER TO neondb_owner;

--
-- Name: update_broadcast_stats(); Type: FUNCTION; Schema: public; Owner: neondb_owner
--

CREATE FUNCTION public.update_broadcast_stats() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.status = 'sent' AND OLD.status != 'sent' THEN
        UPDATE newsletter_broadcasts 
        SET successful_deliveries = successful_deliveries + 1
        WHERE id = NEW.broadcast_id;
    ELSIF NEW.status = 'failed' AND OLD.status != 'failed' THEN
        UPDATE newsletter_broadcasts 
        SET failed_deliveries = failed_deliveries + 1
        WHERE id = NEW.broadcast_id;
    END IF;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_broadcast_stats() OWNER TO neondb_owner;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: neondb_owner
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO neondb_owner;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: replit_database_migrations_v1; Type: TABLE; Schema: _system; Owner: neondb_owner
--

CREATE TABLE _system.replit_database_migrations_v1 (
    id bigint NOT NULL,
    build_id text NOT NULL,
    deployment_id text NOT NULL,
    statement_count bigint NOT NULL,
    applied_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE _system.replit_database_migrations_v1 OWNER TO neondb_owner;

--
-- Name: replit_database_migrations_v1_id_seq; Type: SEQUENCE; Schema: _system; Owner: neondb_owner
--

CREATE SEQUENCE _system.replit_database_migrations_v1_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE _system.replit_database_migrations_v1_id_seq OWNER TO neondb_owner;

--
-- Name: replit_database_migrations_v1_id_seq; Type: SEQUENCE OWNED BY; Schema: _system; Owner: neondb_owner
--

ALTER SEQUENCE _system.replit_database_migrations_v1_id_seq OWNED BY _system.replit_database_migrations_v1.id;


--
-- Name: newsletter_subscriptions; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.newsletter_subscriptions (
    id bigint NOT NULL,
    user_id bigint,
    is_active boolean DEFAULT true,
    language character varying(10) DEFAULT 'English'::character varying,
    timezone character varying(50) DEFAULT 'UTC'::character varying,
    delivery_time time without time zone DEFAULT '09:00:00'::time without time zone,
    daily_wisdom boolean DEFAULT true,
    special_events boolean DEFAULT true,
    subscribed_at timestamp with time zone DEFAULT now(),
    unsubscribed_at timestamp with time zone,
    last_delivery timestamp with time zone,
    total_deliveries integer DEFAULT 0,
    total_opens integer DEFAULT 0,
    last_open timestamp with time zone
);


ALTER TABLE public.newsletter_subscriptions OWNER TO neondb_owner;

--
-- Name: users; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.users (
    id bigint NOT NULL,
    telegram_user_id bigint NOT NULL,
    username character varying(100),
    first_name character varying(100),
    last_name character varying(100),
    language_code character varying(10),
    created_at timestamp with time zone DEFAULT now(),
    last_interaction timestamp with time zone DEFAULT now(),
    is_bot boolean DEFAULT false,
    is_premium boolean DEFAULT false,
    is_blocked boolean DEFAULT false,
    total_wisdom_requests integer DEFAULT 0,
    total_quiz_attempts integer DEFAULT 0,
    last_wisdom_topic character varying(200),
    user_data jsonb,
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.users OWNER TO neondb_owner;

--
-- Name: active_subscribers_by_language; Type: VIEW; Schema: public; Owner: neondb_owner
--

CREATE VIEW public.active_subscribers_by_language AS
 SELECT ns.language,
    count(*) AS subscriber_count,
    count(*) FILTER (WHERE (u.last_interaction > (now() - '30 days'::interval))) AS active_users_30d,
    count(*) FILTER (WHERE (u.last_interaction > (now() - '7 days'::interval))) AS active_users_7d
   FROM (public.newsletter_subscriptions ns
     JOIN public.users u ON ((u.telegram_user_id = ns.user_id)))
  WHERE (ns.is_active = true)
  GROUP BY ns.language
  ORDER BY (count(*)) DESC;


ALTER VIEW public.active_subscribers_by_language OWNER TO neondb_owner;

--
-- Name: admin_users; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.admin_users (
    id integer NOT NULL,
    telegram_user_id bigint NOT NULL,
    username character varying(100) NOT NULL,
    role character varying(50) DEFAULT 'admin'::character varying,
    permissions jsonb,
    created_at timestamp with time zone DEFAULT now(),
    last_login timestamp with time zone,
    is_active boolean DEFAULT true
);


ALTER TABLE public.admin_users OWNER TO neondb_owner;

--
-- Name: admin_users_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.admin_users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.admin_users_id_seq OWNER TO neondb_owner;

--
-- Name: admin_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.admin_users_id_seq OWNED BY public.admin_users.id;


--
-- Name: audit_log; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.audit_log (
    id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    event_type character varying(50) NOT NULL,
    user_identifier character varying(255) NOT NULL,
    action character varying(255) NOT NULL,
    resource character varying(255) NOT NULL,
    details jsonb,
    ip_address inet,
    user_agent text,
    success boolean DEFAULT true NOT NULL,
    error_message text,
    session_id character varying(255),
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.audit_log OWNER TO neondb_owner;

--
-- Name: audit_log_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.audit_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.audit_log_id_seq OWNER TO neondb_owner;

--
-- Name: audit_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.audit_log_id_seq OWNED BY public.audit_log.id;


--
-- Name: delivery_log; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.delivery_log (
    id bigint NOT NULL,
    broadcast_id bigint,
    user_id bigint,
    status character varying(20) NOT NULL,
    attempt_count integer DEFAULT 0,
    scheduled_at timestamp with time zone DEFAULT now(),
    delivered_at timestamp with time zone,
    opened_at timestamp with time zone,
    error_message text,
    telegram_message_id integer,
    delivery_metadata jsonb
);


ALTER TABLE public.delivery_log OWNER TO neondb_owner;

--
-- Name: newsletter_broadcasts; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.newsletter_broadcasts (
    id bigint NOT NULL,
    broadcast_date date NOT NULL,
    wisdom_content jsonb,
    image_url text,
    status character varying(20) DEFAULT 'draft'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    scheduled_at timestamp with time zone,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    total_recipients integer DEFAULT 0,
    successful_deliveries integer DEFAULT 0,
    failed_deliveries integer DEFAULT 0,
    created_by character varying(100),
    notes text,
    quiz_topic character varying(255),
    broadcast_type character varying(50) DEFAULT 'wisdom'::character varying,
    wisdom_topic character varying(200)
);


ALTER TABLE public.newsletter_broadcasts OWNER TO neondb_owner;

--
-- Name: broadcast_statistics; Type: VIEW; Schema: public; Owner: neondb_owner
--

CREATE VIEW public.broadcast_statistics AS
 SELECT nb.id,
    nb.broadcast_date,
    nb.status,
    nb.total_recipients,
    nb.successful_deliveries,
    nb.failed_deliveries,
        CASE
            WHEN (nb.total_recipients > 0) THEN round((((nb.successful_deliveries)::numeric / (nb.total_recipients)::numeric) * (100)::numeric), 2)
            ELSE (0)::numeric
        END AS delivery_rate_percent,
    count(dl.opened_at) AS total_opens,
        CASE
            WHEN (nb.successful_deliveries > 0) THEN round((((count(dl.opened_at))::numeric / (nb.successful_deliveries)::numeric) * (100)::numeric), 2)
            ELSE (0)::numeric
        END AS open_rate_percent
   FROM (public.newsletter_broadcasts nb
     LEFT JOIN public.delivery_log dl ON ((nb.id = dl.broadcast_id)))
  GROUP BY nb.id, nb.broadcast_date, nb.status, nb.total_recipients, nb.successful_deliveries, nb.failed_deliveries
  ORDER BY nb.broadcast_date DESC;


ALTER VIEW public.broadcast_statistics OWNER TO neondb_owner;

--
-- Name: delivery_log_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.delivery_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.delivery_log_id_seq OWNER TO neondb_owner;

--
-- Name: delivery_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.delivery_log_id_seq OWNED BY public.delivery_log.id;


--
-- Name: newsletter_broadcasts_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.newsletter_broadcasts_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.newsletter_broadcasts_id_seq OWNER TO neondb_owner;

--
-- Name: newsletter_broadcasts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.newsletter_broadcasts_id_seq OWNED BY public.newsletter_broadcasts.id;


--
-- Name: newsletter_subscriptions_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.newsletter_subscriptions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.newsletter_subscriptions_id_seq OWNER TO neondb_owner;

--
-- Name: newsletter_subscriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.newsletter_subscriptions_id_seq OWNED BY public.newsletter_subscriptions.id;


--
-- Name: test_broadcasts; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.test_broadcasts (
    id bigint NOT NULL,
    admin_id bigint,
    test_content jsonb NOT NULL,
    test_image_url text,
    target_languages text[],
    created_at timestamp with time zone DEFAULT now(),
    sent_at timestamp with time zone,
    status character varying(20) DEFAULT 'draft'::character varying,
    notes text
);


ALTER TABLE public.test_broadcasts OWNER TO neondb_owner;

--
-- Name: test_broadcasts_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.test_broadcasts_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.test_broadcasts_id_seq OWNER TO neondb_owner;

--
-- Name: test_broadcasts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.test_broadcasts_id_seq OWNED BY public.test_broadcasts.id;


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO neondb_owner;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: replit_database_migrations_v1 id; Type: DEFAULT; Schema: _system; Owner: neondb_owner
--

ALTER TABLE ONLY _system.replit_database_migrations_v1 ALTER COLUMN id SET DEFAULT nextval('_system.replit_database_migrations_v1_id_seq'::regclass);


--
-- Name: admin_users id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.admin_users ALTER COLUMN id SET DEFAULT nextval('public.admin_users_id_seq'::regclass);


--
-- Name: audit_log id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.audit_log ALTER COLUMN id SET DEFAULT nextval('public.audit_log_id_seq'::regclass);


--
-- Name: delivery_log id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.delivery_log ALTER COLUMN id SET DEFAULT nextval('public.delivery_log_id_seq'::regclass);


--
-- Name: newsletter_broadcasts id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.newsletter_broadcasts ALTER COLUMN id SET DEFAULT nextval('public.newsletter_broadcasts_id_seq'::regclass);


--
-- Name: newsletter_subscriptions id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.newsletter_subscriptions ALTER COLUMN id SET DEFAULT nextval('public.newsletter_subscriptions_id_seq'::regclass);


--
-- Name: test_broadcasts id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.test_broadcasts ALTER COLUMN id SET DEFAULT nextval('public.test_broadcasts_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: replit_database_migrations_v1; Type: TABLE DATA; Schema: _system; Owner: neondb_owner
--

COPY _system.replit_database_migrations_v1 (id, build_id, deployment_id, statement_count, applied_at) FROM stdin;
1	6f8561fe-61ab-486e-a0e7-67278fd60507	9bf4161d-b7ee-4723-bfdc-624a92cb6794	4	2025-09-11 20:48:06.406968+00
2	0e99f10e-46f5-4546-9f5d-db96aef2567b	9bf4161d-b7ee-4723-bfdc-624a92cb6794	1	2025-09-12 08:40:28.052363+00
3	11a71ef9-2848-4255-9c8b-82b863638a06	9bf4161d-b7ee-4723-bfdc-624a92cb6794	2	2025-09-16 20:12:40.929079+00
4	a9c93a66-93a2-414a-98c6-668b53e07865	9bf4161d-b7ee-4723-bfdc-624a92cb6794	1	2025-09-26 07:31:59.232327+00
5	c9561806-7f21-4138-9ed0-3877710a98b1	9bf4161d-b7ee-4723-bfdc-624a92cb6794	1	2025-09-28 18:29:17.462537+00
6	ab19b4de-7e78-4989-8f0e-9a572cc6f2ec	9bf4161d-b7ee-4723-bfdc-624a92cb6794	2	2025-09-28 21:12:30.847629+00
7	4ea704a0-ff51-496c-aac1-3ddbeccd9ffa	9bf4161d-b7ee-4723-bfdc-624a92cb6794	1	2025-09-29 08:41:04.930021+00
8	4ab5e946-062c-4e4c-92fa-88a9d6f0f8ee	9bf4161d-b7ee-4723-bfdc-624a92cb6794	1	2025-09-29 08:50:34.789866+00
9	036489da-256a-46b9-96b0-ba6c96cdc7cb	9bf4161d-b7ee-4723-bfdc-624a92cb6794	1	2025-09-29 09:03:02.051418+00
10	d94eea9a-daf8-4317-ad46-741365a281f8	9bf4161d-b7ee-4723-bfdc-624a92cb6794	1	2025-10-05 09:42:32.356221+00
11	0d4ab197-3a2b-4b20-90e2-d5a02c731d96	9bf4161d-b7ee-4723-bfdc-624a92cb6794	1	2025-10-05 09:56:07.760716+00
12	16ce3826-06f4-47a8-ac79-c420de9e023c	9bf4161d-b7ee-4723-bfdc-624a92cb6794	1	2025-10-05 10:18:26.065227+00
13	f44f7076-244b-47fe-82b7-b381d2782fa2	9bf4161d-b7ee-4723-bfdc-624a92cb6794	1	2025-10-05 10:30:33.451661+00
14	58092609-d1ee-4593-9d2e-7d011ae50cdd	9bf4161d-b7ee-4723-bfdc-624a92cb6794	1	2025-10-10 13:47:27.175853+00
15	abf3f896-cf86-4fd4-9f4e-7bab5d2b06d2	9bf4161d-b7ee-4723-bfdc-624a92cb6794	1	2025-10-12 07:17:00.134753+00
16	0975003b-8791-4142-a3ce-84a9760514df	9bf4161d-b7ee-4723-bfdc-624a92cb6794	1	2025-10-13 08:01:30.285738+00
17	2aa8f0ac-535d-4491-84b7-dbf81fe6482f	9bf4161d-b7ee-4723-bfdc-624a92cb6794	1	2025-10-16 09:00:09.468723+00
18	56d9d765-2a66-40d6-a793-ed6e8d49aa0b	9bf4161d-b7ee-4723-bfdc-624a92cb6794	1	2025-10-16 09:19:56.970419+00
\.


--
-- Data for Name: admin_users; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.admin_users (id, telegram_user_id, username, role, permissions, created_at, last_login, is_active) FROM stdin;
\.


--
-- Data for Name: audit_log; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.audit_log (id, "timestamp", event_type, user_identifier, action, resource, details, ip_address, user_agent, success, error_message, session_id, created_at) FROM stdin;
\.


--
-- Data for Name: delivery_log; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.delivery_log (id, broadcast_id, user_id, status, attempt_count, scheduled_at, delivered_at, opened_at, error_message, telegram_message_id, delivery_metadata) FROM stdin;
\.


--
-- Data for Name: newsletter_broadcasts; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.newsletter_broadcasts (id, broadcast_date, wisdom_content, image_url, status, created_at, scheduled_at, started_at, completed_at, total_recipients, successful_deliveries, failed_deliveries, created_by, notes, quiz_topic, broadcast_type, wisdom_topic) FROM stdin;
1	2025-09-17	\N	\N	reserved	2025-09-17 03:00:48.545989+00	\N	\N	\N	0	0	0	auto_scheduler	\N	\N	wisdom	\N
140	2025-10-14	\N	\N	sent	2025-10-14 06:00:39.233761+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	стабильность и постоянство в служении
212	2025-11-01	\N	\N	sent	2025-11-01 06:00:22.598396+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	духовное возвышение через покой
144	2025-10-15	\N	\N	sent	2025-10-15 06:00:49.479517+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	роль молитвы в духовном развитии
148	2025-10-16	\N	\N	sent	2025-10-16 06:00:58.756829+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	сила воли и самодисциплина
216	2025-11-02	\N	\N	sent	2025-11-02 06:00:41.476762+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	благословения на простые радости
152	2025-10-17	\N	\N	sent	2025-10-17 06:01:08.640393+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	нахождение Бога в природе
220	2025-11-03	\N	\N	sent	2025-11-03 06:00:46.394921+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	смирение и духовная скромность
156	2025-10-18	\N	\N	sent	2025-10-18 06:01:11.650059+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	борьба с ленью и прокрастинацией
41	2025-09-18	\N	\N	sent	2025-09-18 06:01:00.749262+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	честность и праведность в поступках
224	2025-11-04	\N	\N	sent	2025-11-04 06:00:39.774968+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	преодоление гордыни и высокомерия
44	2025-09-19	\N	\N	sent	2025-09-19 06:01:02.174381+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	семейные ценности и любовь
228	2025-11-05	\N	\N	generating	2025-11-05 06:00:46.719124+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	святость в обыденных делах
160	2025-10-19	\N	\N	sent	2025-10-19 06:00:53.979088+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	дружба и верность в отношениях
47	2025-09-20	\N	\N	sent	2025-09-20 06:00:59.508804+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	радость в служении и изучении Торы
231	2025-11-06	\N	\N	generating	2025-11-06 06:00:46.327177+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	восстановление после неудач
50	2025-09-21	\N	\N	sent	2025-09-21 06:00:08.503227+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	надежда и вера в трудные времена
164	2025-10-20	\N	\N	sent	2025-10-20 06:00:54.381031+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	энергия нового дня и духовные возможности
234	2025-11-07	\N	\N	generating	2025-11-07 06:00:33.122146+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	постоянство в духовном росте
237	2025-11-08	\N	\N	generating	2025-11-08 06:00:32.786881+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	применение учения в повседневной жизни
168	2025-10-21	\N	\N	sent	2025-10-21 06:01:03.616148+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	поддержка товарищей в радости и печали
240	2025-11-09	\N	\N	generating	2025-11-09 06:00:59.760487+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	ежедневная мудрость и духовное наставление
172	2025-10-22	\N	\N	sent	2025-10-22 06:00:49.090995+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	внутренний мир и гармония души
243	2025-11-10	\N	\N	generating	2025-11-10 06:00:38.040498+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	забота о здоровье тела и души
246	2025-11-11	\N	\N	generating	2025-11-11 06:00:33.291129+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	превращение препятствий в возможности
176	2025-10-23	\N	\N	sent	2025-10-23 06:00:51.604539+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	умение слушать и понимать других
124	2025-10-10	\N	\N	sent	2025-10-10 06:00:37.408835+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	благотворительность и забота о других
249	2025-11-12	\N	\N	generating	2025-11-12 06:00:49.430685+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	осознанность в каждом действии дня
180	2025-10-24	\N	\N	sent	2025-10-24 06:00:43.285181+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	нахождение смысла в страданиях
128	2025-10-11	\N	\N	sent	2025-10-11 06:00:52.913335+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	прощение и очищение души
252	2025-11-13	\N	\N	generating	2025-11-13 06:00:47.596867+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	подготовка к завершению недели и духовные размышления
184	2025-10-25	\N	\N	sent	2025-10-25 06:00:54.956761+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	простота и чистота намерений
132	2025-10-12	\N	\N	sent	2025-10-12 06:00:38.833262+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	мудрость старцев и жизненный опыт
188	2025-10-26	\N	\N	sent	2025-10-26 06:00:52.271437+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	терпение в ожидании благословений
192	2025-10-27	\N	\N	sent	2025-10-27 06:00:52.569511+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	забота о вдовах, сиротах и нуждающихся
136	2025-10-13	\N	\N	sent	2025-10-13 06:00:42.230416+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	понимание Божественного Провидения
196	2025-10-28	\N	\N	sent	2025-10-28 06:01:12.655001+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	мудрость Пиркей Авот в жизни
200	2025-10-29	\N	\N	sent	2025-10-29 06:00:50.019434+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	радость от самосовершенствования
204	2025-10-30	\N	\N	sent	2025-10-30 06:00:43.839303+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	сила надежды в темные времена
208	2025-10-31	\N	\N	sent	2025-10-31 06:00:34.774663+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	самопознание и понимание своего пути
255	2025-11-14	\N	\N	generating	2025-11-14 06:01:07.512907+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	учение и передача знаний
258	2025-11-15	\N	\N	generating	2025-11-15 06:01:04.404213+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	нахождение Бога в природе
261	2025-11-16	\N	\N	generating	2025-11-16 06:00:54.523044+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	мудрость праведников и духовный рост
264	2025-11-17	\N	\N	generating	2025-11-17 06:00:49.232973+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	мир в доме и семейное благополучие
267	2025-11-18	\N	\N	generating	2025-11-18 06:01:00.15469+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	доброта и помощь ближним
270	2025-11-19	\N	\N	generating	2025-11-19 06:00:43.671943+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	радость от самосовершенствования
273	2025-11-20	\N	\N	generating	2025-11-20 06:00:38.643715+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	благодарность и благословения в жизни
276	2025-11-21	\N	\N	generating	2025-11-21 06:00:51.51748+00	\N	\N	\N	0	0	0	\N	\N	\N	wisdom	благословения на простые радости
\.


--
-- Data for Name: newsletter_subscriptions; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.newsletter_subscriptions (id, user_id, is_active, language, timezone, delivery_time, daily_wisdom, special_events, subscribed_at, unsubscribed_at, last_delivery, total_deliveries, total_opens, last_open) FROM stdin;
183	6652298761	t	English	UTC	09:00:00	t	t	2025-09-19 07:27:56.273019+00	\N	\N	0	0	\N
6	123	t	English	UTC	09:00:00	t	t	2025-09-01 17:25:43.981577+00	\N	\N	0	0	\N
69	456	t	English	UTC	09:00:00	t	t	2025-09-03 12:04:10.03396+00	\N	\N	0	0	\N
70	31126146	t	English	UTC	09:00:00	t	t	2025-09-03 13:38:43.38814+00	\N	\N	0	0	\N
184	588617031	t	Russian	UTC	09:00:00	t	t	2025-09-19 08:05:33.073447+00	\N	\N	0	0	\N
72	67518954	t	Russian	UTC	09:00:00	t	t	2025-09-03 20:04:59.691412+00	\N	\N	0	0	\N
11	12345	t	English	UTC	09:00:00	t	t	2025-09-01 20:41:15.827747+00	\N	\N	0	0	\N
73	6952108531	t	English	UTC	09:00:00	t	t	2025-09-03 20:18:44.98376+00	\N	\N	0	0	\N
74	5287789980	t	English	UTC	09:00:00	t	t	2025-09-03 21:31:41.147551+00	\N	\N	0	0	\N
14	822722753	t	Russian	UTC	09:00:00	t	t	2025-09-02 06:41:56.051246+00	\N	\N	0	0	\N
75	6363994226	t	English	UTC	09:00:00	t	t	2025-09-03 23:43:06.606239+00	\N	\N	0	0	\N
76	8148436015	t	English	UTC	09:00:00	t	t	2025-09-04 00:27:55.062062+00	\N	\N	0	0	\N
77	427948100	t	Russian	UTC	09:00:00	t	t	2025-09-04 06:14:16.195255+00	\N	\N	0	0	\N
78	6534457085	t	Arabic	UTC	09:00:00	t	t	2025-09-04 17:43:49.375798+00	\N	\N	0	0	\N
185	207866676	t	Russian	UTC	09:00:00	t	t	2025-09-19 08:22:54.745739+00	\N	\N	0	0	\N
186	109048024	t	Russian	UTC	09:00:00	t	t	2025-09-19 15:01:27.54921+00	\N	\N	0	0	\N
187	327241593	t	Russian	UTC	09:00:00	t	t	2025-09-19 15:17:52.705537+00	\N	\N	0	0	\N
188	160723514	t	Russian	UTC	09:00:00	t	t	2025-09-19 15:37:20.698608+00	\N	\N	0	0	\N
142	982704568	t	English	UTC	09:00:00	t	t	2025-09-05 17:43:56.417809+00	\N	\N	0	0	\N
144	6587666086	t	Russian	UTC	09:00:00	t	t	2025-09-05 21:23:39.436928+00	\N	\N	0	0	\N
146	7064637241	t	English	UTC	09:00:00	t	t	2025-09-06 09:18:35.63489+00	\N	\N	0	0	\N
147	1555718844	t	Spanish	UTC	09:00:00	t	t	2025-09-06 20:33:20.346689+00	\N	\N	0	0	\N
148	7105471939	t	English	UTC	09:00:00	t	t	2025-09-06 22:51:29.964029+00	\N	\N	0	0	\N
149	5114151095	t	English	UTC	09:00:00	t	t	2025-09-07 13:30:06.25304+00	\N	\N	0	0	\N
150	7560435904	t	English	UTC	09:00:00	t	t	2025-09-08 02:53:07.067435+00	\N	\N	0	0	\N
37	354007772	t	Russian	UTC	09:00:00	t	t	2025-09-02 16:15:14.720908+00	\N	\N	0	0	\N
151	177509235	t	Russian	UTC	09:00:00	t	t	2025-09-08 06:31:55.654921+00	\N	\N	0	0	\N
152	5118483797	t	English	UTC	09:00:00	t	t	2025-09-08 09:24:51.252333+00	\N	\N	0	0	\N
153	6269732115	t	Russian	UTC	09:00:00	t	t	2025-09-08 11:26:34.216931+00	\N	\N	0	0	\N
190	6328396822	t	English	UTC	09:00:00	t	t	2025-09-20 18:53:24.925984+00	\N	\N	0	0	\N
191	6445848544	t	French	UTC	09:00:00	t	t	2025-09-20 20:19:24.644219+00	\N	\N	0	0	\N
156	6029332831	t	English	UTC	09:00:00	t	t	2025-09-09 13:01:03.161371+00	\N	\N	0	0	\N
192	7921564756	t	English	UTC	09:00:00	t	t	2025-09-20 20:20:27.688696+00	\N	\N	0	0	\N
193	7107917224	t	German	UTC	09:00:00	t	t	2025-09-20 21:14:28.353242+00	\N	\N	0	0	\N
159	371684516	t	Russian	UTC	09:00:00	t	t	2025-09-09 21:18:59.671416+00	\N	\N	0	0	\N
161	171878750	t	Russian	UTC	09:00:00	t	t	2025-09-10 05:34:19.700108+00	\N	\N	0	0	\N
210	741786918	t	Russian	UTC	09:00:00	t	t	2025-09-30 14:07:50.127881+00	\N	\N	0	0	\N
203	1782586181	t	English	UTC	09:00:00	t	t	2025-09-28 09:35:05.978886+00	\N	\N	0	0	\N
52	5030166891	t	English	UTC	09:00:00	t	t	2025-09-03 05:46:39.642768+00	\N	\N	0	0	\N
164	1856803179	t	English	UTC	09:00:00	t	t	2025-09-11 10:09:59.863893+00	\N	\N	0	0	\N
111	1826148571	t	English	UTC	09:00:00	t	t	2025-09-05 07:48:35.937982+00	\N	\N	0	0	\N
165	822889431	t	English	UTC	09:00:00	t	t	2025-09-11 12:51:28.347232+00	\N	\N	0	0	\N
166	5330685646	t	English	UTC	09:00:00	t	t	2025-09-11 13:37:21.629908+00	\N	\N	0	0	\N
54	123456	t	English	UTC	09:00:00	t	t	2025-09-03 09:30:30.057608+00	\N	\N	0	0	\N
59	454009966	t	English	UTC	09:00:00	t	t	2025-09-03 09:32:19.357932+00	\N	\N	0	0	\N
5	7057240608	t	Russian	UTC	09:00:00	t	t	2025-09-01 17:25:38.722859+00	\N	\N	0	0	\N
167	6411996480	t	French	UTC	09:00:00	t	t	2025-09-11 20:26:00.102434+00	\N	\N	0	0	\N
194	47284045	t	Russian	UTC	09:00:00	t	t	2025-09-22 16:59:59.210757+00	\N	\N	0	0	\N
168	984329227	t	English	UTC	09:00:00	t	t	2025-09-14 11:20:53.419296+00	\N	\N	0	0	\N
169	6309222119	t	English	UTC	09:00:00	t	t	2025-09-14 20:27:25.645172+00	\N	\N	0	0	\N
170	943605976	t	English	UTC	09:00:00	t	t	2025-09-14 22:24:16.316741+00	\N	\N	0	0	\N
171	1170190175	t	English	UTC	09:00:00	t	t	2025-09-15 10:25:57.057344+00	\N	\N	0	0	\N
172	8364612041	t	English	UTC	09:00:00	t	t	2025-09-15 11:00:53.38743+00	\N	\N	0	0	\N
173	7094910035	t	English	UTC	09:00:00	t	t	2025-09-15 16:38:24.950454+00	\N	\N	0	0	\N
174	6044608391	t	English	UTC	09:00:00	t	t	2025-09-15 20:59:25.253509+00	\N	\N	0	0	\N
175	2125464300	t	English	UTC	09:00:00	t	t	2025-09-15 21:40:16.529078+00	\N	\N	0	0	\N
176	1953435121	t	English	UTC	09:00:00	t	t	2025-09-16 08:40:37.0515+00	\N	\N	0	0	\N
177	1564068820	t	English	UTC	09:00:00	t	t	2025-09-17 12:08:05.051997+00	\N	\N	0	0	\N
178	7660474342	t	Russian	UTC	09:00:00	t	t	2025-09-17 16:38:30.324587+00	\N	\N	0	0	\N
179	1552107375	t	English	UTC	09:00:00	t	t	2025-09-18 23:10:35.365237+00	\N	\N	0	0	\N
180	7930538909	t	English	UTC	09:00:00	t	t	2025-09-19 01:35:33.146343+00	\N	\N	0	0	\N
127	111111111	t	English	UTC	09:00:00	t	t	2025-09-05 11:53:51.487008+00	\N	\N	0	0	\N
181	422150282	t	French	UTC	09:00:00	t	t	2025-09-19 02:53:04.411626+00	\N	\N	0	0	\N
182	840665822	t	English	UTC	09:00:00	t	t	2025-09-19 04:56:36.474915+00	\N	\N	0	0	\N
195	8414586612	t	English	UTC	09:00:00	t	t	2025-09-22 19:35:36.649438+00	\N	\N	0	0	\N
196	528842488	t	English	UTC	09:00:00	t	t	2025-09-23 00:23:47.983+00	\N	\N	0	0	\N
197	7662402291	t	English	UTC	09:00:00	t	t	2025-09-23 04:24:28.971906+00	\N	\N	0	0	\N
198	7578030596	t	English	UTC	09:00:00	t	t	2025-09-24 08:57:14.553838+00	\N	\N	0	0	\N
199	5464572799	t	English	UTC	09:00:00	t	t	2025-09-25 11:43:08.052358+00	\N	\N	0	0	\N
200	1005837694	t	Russian	UTC	09:00:00	t	t	2025-09-27 06:24:17.593912+00	\N	\N	0	0	\N
201	7539436948	t	English	UTC	09:00:00	t	t	2025-09-27 22:17:02.144237+00	\N	\N	0	0	\N
202	6368188743	t	Russian	UTC	09:00:00	t	t	2025-09-28 08:31:25.873349+00	\N	\N	0	0	\N
208	6650435700	t	English	UTC	09:00:00	t	t	2025-09-29 05:09:47.4996+00	\N	\N	0	0	\N
7	6630727156	t	Russian	UTC	09:00:00	t	t	2025-09-01 17:29:48.347442+00	\N	\N	0	0	\N
211	1297394659	t	English	UTC	09:00:00	t	t	2025-09-30 19:04:59.67228+00	\N	\N	0	0	\N
212	8405872912	t	English	UTC	09:00:00	t	t	2025-10-02 13:45:09.773034+00	\N	\N	0	0	\N
213	261113926	t	English	UTC	09:00:00	t	t	2025-10-02 19:01:48.745641+00	\N	\N	0	0	\N
214	126595368	t	English	UTC	09:00:00	t	t	2025-10-03 15:06:25.296554+00	\N	\N	0	0	\N
216	6888754964	t	German	UTC	09:00:00	t	t	2025-10-03 17:02:02.49292+00	\N	\N	0	0	\N
1	215335	t	Russian	UTC	09:00:00	t	t	2025-09-01 17:25:35.696591+00	\N	\N	0	0	\N
217	5681426744	t	English	UTC	09:00:00	t	t	2025-10-03 17:10:03.937328+00	\N	\N	0	0	\N
218	129542059	t	English	UTC	09:00:00	t	t	2025-10-03 17:34:31.997661+00	\N	\N	0	0	\N
219	5747645852	t	Spanish	UTC	09:00:00	t	t	2025-10-03 20:09:15.016061+00	\N	\N	0	0	\N
220	6978463557	t	Russian	UTC	09:00:00	t	t	2025-10-03 20:30:19.10126+00	\N	\N	0	0	\N
221	946710923	t	Spanish	UTC	09:00:00	t	t	2025-10-03 20:32:22.308936+00	\N	\N	0	0	\N
222	5249566335	t	Russian	UTC	09:00:00	t	t	2025-10-03 20:52:43.614046+00	\N	\N	0	0	\N
223	6831339695	t	English	UTC	09:00:00	t	t	2025-10-03 20:59:57.816483+00	\N	\N	0	0	\N
224	5554678952	t	English	UTC	09:00:00	t	t	2025-10-03 21:03:39.418369+00	\N	\N	0	0	\N
225	5615101684	t	Russian	UTC	09:00:00	t	t	2025-10-03 21:14:17.911593+00	\N	\N	0	0	\N
226	7144105860	t	English	UTC	09:00:00	t	t	2025-10-03 21:24:03.785478+00	\N	\N	0	0	\N
227	250152350	t	Russian	UTC	09:00:00	t	t	2025-10-03 21:45:29.855146+00	\N	\N	0	0	\N
228	745427964	t	Russian	UTC	09:00:00	t	t	2025-10-03 23:27:19.764829+00	\N	\N	0	0	\N
229	543447442	t	English	UTC	09:00:00	t	t	2025-10-04 07:41:10.088784+00	\N	\N	0	0	\N
230	5249381610	t	English	UTC	09:00:00	t	t	2025-10-04 08:08:25.279811+00	\N	\N	0	0	\N
231	5284659496	t	Russian	UTC	09:00:00	t	t	2025-10-04 08:42:30.580487+00	\N	\N	0	0	\N
232	7775146035	t	English	UTC	09:00:00	t	t	2025-10-04 09:13:29.682081+00	\N	\N	0	0	\N
233	62036930	t	Russian	UTC	09:00:00	t	t	2025-10-04 10:06:55.678524+00	\N	\N	0	0	\N
234	1667124224	t	English	UTC	09:00:00	t	t	2025-10-04 12:39:03.352806+00	\N	\N	0	0	\N
235	287079394	t	English	UTC	09:00:00	t	t	2025-10-04 15:09:12.48698+00	\N	\N	0	0	\N
236	1546881779	t	English	UTC	09:00:00	t	t	2025-10-04 15:47:55.886065+00	\N	\N	0	0	\N
238	165852222	t	Russian	UTC	09:00:00	t	t	2025-10-04 16:47:13.193131+00	\N	\N	0	0	\N
239	1958518123	t	German	UTC	09:00:00	t	t	2025-10-04 16:48:39.870008+00	\N	\N	0	0	\N
240	1309402200	t	German	UTC	09:00:00	t	t	2025-10-04 17:11:13.586192+00	\N	\N	0	0	\N
241	1597736081	t	Russian	UTC	09:00:00	t	t	2025-10-04 17:12:21.217446+00	\N	\N	0	0	\N
242	7390994963	t	Russian	UTC	09:00:00	t	t	2025-10-04 17:42:43.987726+00	\N	\N	0	0	\N
243	5193896065	t	English	UTC	09:00:00	t	t	2025-10-04 20:30:30.871143+00	\N	\N	0	0	\N
244	6892428416	t	Russian	UTC	09:00:00	t	t	2025-10-04 22:35:11.442269+00	\N	\N	0	0	\N
245	1659448634	t	Spanish	UTC	09:00:00	t	t	2025-10-04 22:38:43.875132+00	\N	\N	0	0	\N
246	1378251732	t	English	UTC	09:00:00	t	t	2025-10-04 23:11:41.587618+00	\N	\N	0	0	\N
247	5990098796	t	English	UTC	09:00:00	t	t	2025-10-04 23:44:29.469645+00	\N	\N	0	0	\N
248	7544606394	t	English	UTC	09:00:00	t	t	2025-10-05 00:50:45.804342+00	\N	\N	0	0	\N
249	1708316144	t	English	UTC	09:00:00	t	t	2025-10-05 01:17:46.790964+00	\N	\N	0	0	\N
250	7645010451	t	English	UTC	09:00:00	t	t	2025-10-05 01:30:20.1163+00	\N	\N	0	0	\N
251	6369643886	t	English	UTC	09:00:00	t	t	2025-10-05 01:43:00.267786+00	\N	\N	0	0	\N
252	965200380	t	German	UTC	09:00:00	t	t	2025-10-05 01:49:31.68983+00	\N	\N	0	0	\N
253	6471286973	t	Spanish	UTC	09:00:00	t	t	2025-10-05 01:54:18.026189+00	\N	\N	0	0	\N
254	6808247296	t	English	UTC	09:00:00	t	t	2025-10-05 01:57:28.396766+00	\N	\N	0	0	\N
255	8019989846	t	Hebrew	UTC	09:00:00	t	t	2025-10-05 02:05:59.874336+00	\N	\N	0	0	\N
256	1541512996	t	English	UTC	09:00:00	t	t	2025-10-05 02:14:35.391474+00	\N	\N	0	0	\N
257	6220451088	t	English	UTC	09:00:00	t	t	2025-10-05 02:30:47.773604+00	\N	\N	0	0	\N
258	1229686563	t	English	UTC	09:00:00	t	t	2025-10-05 02:44:05.290908+00	\N	\N	0	0	\N
259	8370380793	t	English	UTC	09:00:00	t	t	2025-10-05 02:45:00.675507+00	\N	\N	0	0	\N
260	5322833967	t	English	UTC	09:00:00	t	t	2025-10-05 03:06:30.690932+00	\N	\N	0	0	\N
262	6204287807	t	English	UTC	09:00:00	t	t	2025-10-05 03:10:52.71752+00	\N	\N	0	0	\N
263	691739278	t	English	UTC	09:00:00	t	t	2025-10-05 03:27:21.471797+00	\N	\N	0	0	\N
264	6101379779	t	English	UTC	09:00:00	t	t	2025-10-05 04:03:00.10891+00	\N	\N	0	0	\N
265	1560020634	t	English	UTC	09:00:00	t	t	2025-10-05 04:05:05.208534+00	\N	\N	0	0	\N
266	7183012526	t	English	UTC	09:00:00	t	t	2025-10-05 04:56:36.706714+00	\N	\N	0	0	\N
267	535705843	t	English	UTC	09:00:00	t	t	2025-10-05 05:01:23.107212+00	\N	\N	0	0	\N
268	1593123837	t	English	UTC	09:00:00	t	t	2025-10-05 05:02:15.240227+00	\N	\N	0	0	\N
269	6350653649	t	English	UTC	09:00:00	t	t	2025-10-05 05:06:30.920831+00	\N	\N	0	0	\N
270	346704101	t	English	UTC	09:00:00	t	t	2025-10-05 06:10:44.595012+00	\N	\N	0	0	\N
271	704610936	t	Russian	UTC	09:00:00	t	t	2025-10-05 11:13:09.717789+00	\N	\N	0	0	\N
272	6177341806	t	Russian	UTC	09:00:00	t	t	2025-10-05 11:14:42.518343+00	\N	\N	0	0	\N
273	382947638	t	Russian	UTC	09:00:00	t	t	2025-10-05 11:14:56.19731+00	\N	\N	0	0	\N
274	434450668	t	Russian	UTC	09:00:00	t	t	2025-10-05 11:16:54.418372+00	\N	\N	0	0	\N
275	690147786	t	English	UTC	09:00:00	t	t	2025-10-05 11:17:22.496997+00	\N	\N	0	0	\N
276	369477807	t	Russian	UTC	09:00:00	t	t	2025-10-05 11:19:44.134895+00	\N	\N	0	0	\N
277	1207798300	t	Russian	UTC	09:00:00	t	t	2025-10-05 11:20:23.217606+00	\N	\N	0	0	\N
278	250329368	t	Russian	UTC	09:00:00	t	t	2025-10-05 11:30:57.17425+00	\N	\N	0	0	\N
279	6352288632	t	English	UTC	09:00:00	t	t	2025-10-05 11:31:52.668451+00	\N	\N	0	0	\N
280	1013230906	t	German	UTC	09:00:00	t	t	2025-10-05 11:41:35.319851+00	\N	\N	0	0	\N
282	553150878	t	Russian	UTC	09:00:00	t	t	2025-10-05 11:49:26.192469+00	\N	\N	0	0	\N
283	410073721	t	Russian	UTC	09:00:00	t	t	2025-10-05 11:49:27.17925+00	\N	\N	0	0	\N
284	1788541968	t	English	UTC	09:00:00	t	t	2025-10-05 12:01:44.218125+00	\N	\N	0	0	\N
285	1113854615	t	Russian	UTC	09:00:00	t	t	2025-10-05 12:08:02.04712+00	\N	\N	0	0	\N
286	1339075345	t	English	UTC	09:00:00	t	t	2025-10-05 12:08:21.904628+00	\N	\N	0	0	\N
287	986976844	t	Russian	UTC	09:00:00	t	t	2025-10-05 12:13:19.915358+00	\N	\N	0	0	\N
288	845513733	t	English	UTC	09:00:00	t	t	2025-10-05 12:14:18.18533+00	\N	\N	0	0	\N
289	1724436404	t	English	UTC	09:00:00	t	t	2025-10-05 12:16:38.102176+00	\N	\N	0	0	\N
290	6832191637	t	English	UTC	09:00:00	t	t	2025-10-05 12:27:38.15347+00	\N	\N	0	0	\N
291	6089340024	t	English	UTC	09:00:00	t	t	2025-10-05 12:28:08.136259+00	\N	\N	0	0	\N
292	1828897567	t	Arabic	UTC	09:00:00	t	t	2025-10-05 12:31:12.718203+00	\N	\N	0	0	\N
294	93075872	t	Russian	UTC	09:00:00	t	t	2025-10-05 12:32:20.81234+00	\N	\N	0	0	\N
295	945033143	t	English	UTC	09:00:00	t	t	2025-10-05 12:32:41.103566+00	\N	\N	0	0	\N
296	1707324289	t	English	UTC	09:00:00	t	t	2025-10-05 12:42:44.098393+00	\N	\N	0	0	\N
297	466211409	t	English	UTC	09:00:00	t	t	2025-10-05 13:05:13.17684+00	\N	\N	0	0	\N
281	6340805709	t	English	UTC	09:00:00	t	t	2025-10-05 11:48:16.750226+00	\N	\N	0	0	\N
293	7395089217	t	Spanish	UTC	09:00:00	t	t	2025-10-05 12:31:21.243802+00	\N	\N	0	0	\N
298	7042614010	t	English	UTC	09:00:00	t	t	2025-10-05 13:08:11.418721+00	\N	\N	0	0	\N
299	1702548913	t	German	UTC	09:00:00	t	t	2025-10-05 13:19:00.517641+00	\N	\N	0	0	\N
300	826331526	t	English	UTC	09:00:00	t	t	2025-10-05 13:32:24.051559+00	\N	\N	0	0	\N
301	1440538120	t	English	UTC	09:00:00	t	t	2025-10-05 13:34:15.404942+00	\N	\N	0	0	\N
302	6969441671	t	English	UTC	09:00:00	t	t	2025-10-05 13:45:25.417783+00	\N	\N	0	0	\N
303	1325123211	t	English	UTC	09:00:00	t	t	2025-10-05 13:45:34.461655+00	\N	\N	0	0	\N
304	6671878888	t	German	UTC	09:00:00	t	t	2025-10-05 13:47:47.102575+00	\N	\N	0	0	\N
305	831101241	t	English	UTC	09:00:00	t	t	2025-10-05 13:58:00.318493+00	\N	\N	0	0	\N
306	6875364694	t	English	UTC	09:00:00	t	t	2025-10-05 13:59:08.774753+00	\N	\N	0	0	\N
307	7559329247	t	English	UTC	09:00:00	t	t	2025-10-05 13:59:27.441352+00	\N	\N	0	0	\N
308	1661250723	t	Russian	UTC	09:00:00	t	t	2025-10-05 14:01:00.632229+00	\N	\N	0	0	\N
309	6760017958	t	English	UTC	09:00:00	t	t	2025-10-05 14:12:49.11865+00	\N	\N	0	0	\N
310	7961366035	t	Spanish	UTC	09:00:00	t	t	2025-10-05 14:26:00.417595+00	\N	\N	0	0	\N
311	8270776040	t	English	UTC	09:00:00	t	t	2025-10-05 14:29:40.818363+00	\N	\N	0	0	\N
312	1833477096	t	English	UTC	09:00:00	t	t	2025-10-05 14:34:33.644613+00	\N	\N	0	0	\N
313	6129181419	t	English	UTC	09:00:00	t	t	2025-10-05 14:38:59.818464+00	\N	\N	0	0	\N
314	7526451334	t	French	UTC	09:00:00	t	t	2025-10-05 14:58:06.717954+00	\N	\N	0	0	\N
315	1590367749	t	English	UTC	09:00:00	t	t	2025-10-05 15:03:15.418558+00	\N	\N	0	0	\N
317	718415371	t	Russian	UTC	09:00:00	t	t	2025-10-05 15:15:35.256147+00	\N	\N	0	0	\N
318	8374751306	t	English	UTC	09:00:00	t	t	2025-10-05 15:19:04.317938+00	\N	\N	0	0	\N
319	8029374130	t	English	UTC	09:00:00	t	t	2025-10-05 15:29:24.118973+00	\N	\N	0	0	\N
320	6593187682	t	German	UTC	09:00:00	t	t	2025-10-05 15:30:20.644649+00	\N	\N	0	0	\N
321	5915843326	t	English	UTC	09:00:00	t	t	2025-10-05 15:34:15.219021+00	\N	\N	0	0	\N
322	484829882	t	English	UTC	09:00:00	t	t	2025-10-05 15:35:23.382809+00	\N	\N	0	0	\N
323	5711428833	t	English	UTC	09:00:00	t	t	2025-10-05 15:38:18.718574+00	\N	\N	0	0	\N
324	6192704594	t	English	UTC	09:00:00	t	t	2025-10-05 15:57:49.31854+00	\N	\N	0	0	\N
325	2085431714	t	English	UTC	09:00:00	t	t	2025-10-05 16:05:35.719076+00	\N	\N	0	0	\N
326	1646933326	t	German	UTC	09:00:00	t	t	2025-10-05 16:08:21.024204+00	\N	\N	0	0	\N
327	6743277176	t	English	UTC	09:00:00	t	t	2025-10-05 16:09:32.411183+00	\N	\N	0	0	\N
328	7438908967	t	Spanish	UTC	09:00:00	t	t	2025-10-05 16:20:23.618429+00	\N	\N	0	0	\N
329	5086119787	t	English	UTC	09:00:00	t	t	2025-10-05 16:22:06.355019+00	\N	\N	0	0	\N
330	881214624	t	English	UTC	09:00:00	t	t	2025-10-05 16:33:45.618463+00	\N	\N	0	0	\N
331	5509697048	t	English	UTC	09:00:00	t	t	2025-10-05 16:52:25.717486+00	\N	\N	0	0	\N
332	943719606	t	English	UTC	09:00:00	t	t	2025-10-05 17:14:31.218125+00	\N	\N	0	0	\N
333	138552259	t	German	UTC	09:00:00	t	t	2025-10-05 17:22:29.418464+00	\N	\N	0	0	\N
334	5487812483	t	English	UTC	09:00:00	t	t	2025-10-05 17:35:38.021406+00	\N	\N	0	0	\N
335	8212448201	t	English	UTC	09:00:00	t	t	2025-10-05 17:42:45.716813+00	\N	\N	0	0	\N
336	7108584268	t	English	UTC	09:00:00	t	t	2025-10-05 17:48:45.790409+00	\N	\N	0	0	\N
337	6445649937	t	English	UTC	09:00:00	t	t	2025-10-05 17:51:23.417678+00	\N	\N	0	0	\N
338	1368962964	t	English	UTC	09:00:00	t	t	2025-10-05 18:01:45.019362+00	\N	\N	0	0	\N
339	879358401	t	German	UTC	09:00:00	t	t	2025-10-05 18:06:43.164875+00	\N	\N	0	0	\N
340	5854312977	t	English	UTC	09:00:00	t	t	2025-10-05 18:13:26.895297+00	\N	\N	0	0	\N
341	8171716646	t	English	UTC	09:00:00	t	t	2025-10-05 18:28:31.085434+00	\N	\N	0	0	\N
342	1515444056	t	German	UTC	09:00:00	t	t	2025-10-05 18:30:52.718402+00	\N	\N	0	0	\N
343	5418614468	t	Russian	UTC	09:00:00	t	t	2025-10-05 18:53:38.44928+00	\N	\N	0	0	\N
344	6187077618	t	Spanish	UTC	09:00:00	t	t	2025-10-05 19:09:14.328422+00	\N	\N	0	0	\N
345	832871142	t	French	UTC	09:00:00	t	t	2025-10-05 19:25:09.217922+00	\N	\N	0	0	\N
346	1835925483	t	English	UTC	09:00:00	t	t	2025-10-05 19:27:49.685596+00	\N	\N	0	0	\N
347	172435367	t	English	UTC	09:00:00	t	t	2025-10-05 19:33:21.017922+00	\N	\N	0	0	\N
348	1977379500	t	English	UTC	09:00:00	t	t	2025-10-05 19:55:37.718172+00	\N	\N	0	0	\N
349	7703588364	t	English	UTC	09:00:00	t	t	2025-10-05 19:59:25.052044+00	\N	\N	0	0	\N
350	820329048	t	English	UTC	09:00:00	t	t	2025-10-05 20:18:53.517529+00	\N	\N	0	0	\N
351	6264755497	t	English	UTC	09:00:00	t	t	2025-10-05 20:44:55.818643+00	\N	\N	0	0	\N
352	986445508	t	English	UTC	09:00:00	t	t	2025-10-05 21:01:26.91878+00	\N	\N	0	0	\N
353	8195637848	t	English	UTC	09:00:00	t	t	2025-10-05 23:42:31.517669+00	\N	\N	0	0	\N
354	8100817449	t	English	UTC	09:00:00	t	t	2025-10-05 23:58:36.7186+00	\N	\N	0	0	\N
355	1503910387	t	English	UTC	09:00:00	t	t	2025-10-06 00:07:31.289779+00	\N	\N	0	0	\N
356	516855627	t	Hebrew	UTC	09:00:00	t	t	2025-10-06 00:50:47.71863+00	\N	\N	0	0	\N
357	1488677371	t	English	UTC	09:00:00	t	t	2025-10-06 01:16:31.319178+00	\N	\N	0	0	\N
358	8424384669	t	English	UTC	09:00:00	t	t	2025-10-06 01:22:04.018026+00	\N	\N	0	0	\N
359	5628128008	t	English	UTC	09:00:00	t	t	2025-10-06 01:58:19.718639+00	\N	\N	0	0	\N
360	921009561	t	English	UTC	09:00:00	t	t	2025-10-06 02:05:18.51755+00	\N	\N	0	0	\N
361	5532249782	t	English	UTC	09:00:00	t	t	2025-10-06 02:29:20.019098+00	\N	\N	0	0	\N
363	1258400779	t	English	UTC	09:00:00	t	t	2025-10-06 03:24:15.318706+00	\N	\N	0	0	\N
364	1469651555	t	English	UTC	09:00:00	t	t	2025-10-06 05:31:28.060132+00	\N	\N	0	0	\N
365	1556184415	t	English	UTC	09:00:00	t	t	2025-10-06 05:38:05.37075+00	\N	\N	0	0	\N
366	1440186698	t	English	UTC	09:00:00	t	t	2025-10-06 06:21:53.362275+00	\N	\N	0	0	\N
367	1115752771	t	Russian	UTC	09:00:00	t	t	2025-10-06 06:44:24.662036+00	\N	\N	0	0	\N
368	802864321	t	Russian	UTC	09:00:00	t	t	2025-10-06 06:58:08.562733+00	\N	\N	0	0	\N
369	1600395688	t	English	UTC	09:00:00	t	t	2025-10-06 07:49:48.073584+00	\N	\N	0	0	\N
370	1092144026	t	English	UTC	09:00:00	t	t	2025-10-06 08:11:14.19967+00	\N	\N	0	0	\N
371	1622457981	t	English	UTC	09:00:00	t	t	2025-10-06 09:11:47.405734+00	\N	\N	0	0	\N
373	732408481	t	Spanish	UTC	09:00:00	t	t	2025-10-06 09:30:38.006993+00	\N	\N	0	0	\N
374	7523695427	t	English	UTC	09:00:00	t	t	2025-10-06 10:15:50.807441+00	\N	\N	0	0	\N
375	6649838701	t	English	UTC	09:00:00	t	t	2025-10-06 10:27:03.606382+00	\N	\N	0	0	\N
376	1391227690	t	Russian	UTC	09:00:00	t	t	2025-10-06 12:03:46.763416+00	\N	\N	0	0	\N
377	75594115	t	Russian	UTC	09:00:00	t	t	2025-10-06 16:06:37.473328+00	\N	\N	0	0	\N
378	1613640391	t	English	UTC	09:00:00	t	t	2025-10-07 00:57:30.565995+00	\N	\N	0	0	\N
379	720362336	t	English	UTC	09:00:00	t	t	2025-10-07 01:18:45.364284+00	\N	\N	0	0	\N
380	7471766035	t	English	UTC	09:00:00	t	t	2025-10-07 02:28:36.46493+00	\N	\N	0	0	\N
381	6692316101	t	English	UTC	09:00:00	t	t	2025-10-08 20:28:59.152305+00	\N	\N	0	0	\N
382	1064962808	t	English	UTC	09:00:00	t	t	2025-10-08 21:22:33.367639+00	\N	\N	0	0	\N
383	6818757024	t	English	UTC	09:00:00	t	t	2025-10-09 01:34:03.613203+00	\N	\N	0	0	\N
384	6181371007	t	Spanish	UTC	09:00:00	t	t	2025-10-09 05:08:22.193552+00	\N	\N	0	0	\N
385	8079344188	t	Spanish	UTC	09:00:00	t	t	2025-10-11 00:33:33.784378+00	\N	\N	0	0	\N
386	423887044	t	Russian	UTC	09:00:00	t	t	2025-10-11 05:39:31.412149+00	\N	\N	0	0	\N
387	242970791	t	Russian	UTC	09:00:00	t	t	2025-10-11 12:25:15.015054+00	\N	\N	0	0	\N
388	7625442224	t	English	UTC	09:00:00	t	t	2025-10-11 15:25:31.100598+00	\N	\N	0	0	\N
389	8027268302	t	English	UTC	09:00:00	t	t	2025-10-12 04:44:46.880945+00	\N	\N	0	0	\N
390	7547433819	t	English	UTC	09:00:00	t	t	2025-10-12 21:36:58.404439+00	\N	\N	0	0	\N
391	7896537249	t	English	UTC	09:00:00	t	t	2025-10-12 23:36:28.27+00	\N	\N	0	0	\N
395	8215050105	t	English	UTC	09:00:00	t	t	2025-10-13 13:44:28.010612+00	\N	\N	0	0	\N
392	5936946943	t	Russian	UTC	09:00:00	t	t	2025-10-13 10:39:39.072436+00	\N	\N	0	0	\N
397	5003765976	t	English	UTC	09:00:00	t	t	2025-10-13 18:25:12.182514+00	\N	\N	0	0	\N
399	7564701358	t	English	UTC	09:00:00	t	t	2025-10-14 01:17:50.317666+00	\N	\N	0	0	\N
400	583821364	t	English	UTC	09:00:00	t	t	2025-10-14 03:50:04.09046+00	\N	\N	0	0	\N
401	288330215	t	Russian	UTC	09:00:00	t	t	2025-10-14 12:18:49.292082+00	\N	\N	0	0	\N
402	515460421	t	Russian	UTC	09:00:00	t	t	2025-10-14 13:38:28.674615+00	\N	\N	0	0	\N
403	1172693035	t	English	UTC	09:00:00	t	t	2025-10-14 18:12:20.916037+00	\N	\N	0	0	\N
404	5145179679	t	English	UTC	09:00:00	t	t	2025-10-14 22:21:15.667735+00	\N	\N	0	0	\N
405	6831909579	t	Russian	UTC	09:00:00	t	t	2025-10-15 15:07:37.916157+00	\N	\N	0	0	\N
406	888542869	t	English	UTC	09:00:00	t	t	2025-10-15 22:47:15.389379+00	\N	\N	0	0	\N
407	1906451465	t	Arabic	UTC	09:00:00	t	t	2025-10-16 01:42:36.733057+00	\N	\N	0	0	\N
408	5996231412	t	English	UTC	09:00:00	t	t	2025-10-16 11:33:03.914159+00	\N	\N	0	0	\N
409	458203371	t	Russian	UTC	09:00:00	t	t	2025-10-17 10:00:58.429633+00	\N	\N	0	0	\N
410	990827081	t	German	UTC	09:00:00	t	t	2025-10-17 19:22:09.557282+00	\N	\N	0	0	\N
411	1663951093	t	Spanish	UTC	09:00:00	t	t	2025-10-18 07:48:50.027287+00	\N	\N	0	0	\N
412	430764367	t	English	UTC	09:00:00	t	t	2025-10-18 17:51:53.391498+00	\N	\N	0	0	\N
413	8263108289	t	English	UTC	09:00:00	t	t	2025-10-18 17:58:45.292327+00	\N	\N	0	0	\N
414	368495959	t	Russian	UTC	09:00:00	t	t	2025-10-18 20:35:38.592211+00	\N	\N	0	0	\N
415	589854563	t	Russian	UTC	09:00:00	t	t	2025-10-18 20:36:10.774268+00	\N	\N	0	0	\N
416	958199554	t	Russian	UTC	09:00:00	t	t	2025-10-18 20:41:57.633497+00	\N	\N	0	0	\N
417	649042229	t	Russian	UTC	09:00:00	t	t	2025-10-18 21:02:33.791703+00	\N	\N	0	0	\N
418	275735842	t	English	UTC	09:00:00	t	t	2025-10-18 21:17:58.792024+00	\N	\N	0	0	\N
419	420279837	t	Russian	UTC	09:00:00	t	t	2025-10-18 23:47:39.617907+00	\N	\N	0	0	\N
398	8451800463	t	Hebrew	UTC	09:00:00	t	t	2025-10-13 20:06:54.382976+00	\N	\N	0	0	\N
421	145488954	t	English	UTC	09:00:00	t	t	2025-10-19 23:51:34.879336+00	\N	\N	0	0	\N
422	1809852419	t	English	UTC	09:00:00	t	t	2025-10-20 22:58:41.015881+00	\N	\N	0	0	\N
423	1077412096	t	Spanish	UTC	09:00:00	t	t	2025-10-22 18:12:35.327928+00	\N	\N	0	0	\N
424	6181054389	t	English	UTC	09:00:00	t	t	2025-10-23 12:37:51.62942+00	\N	\N	0	0	\N
425	7650609791	t	English	UTC	09:00:00	t	t	2025-10-23 14:55:17.000976+00	\N	\N	0	0	\N
427	774455	t	English	UTC	09:00:00	t	t	2025-10-25 12:16:15.666191+00	\N	\N	0	0	\N
428	206397663	t	Russian	UTC	09:00:00	t	t	2025-10-26 02:26:37.055649+00	\N	\N	0	0	\N
429	933046226	t	English	UTC	09:00:00	t	t	2025-10-26 15:52:48.428516+00	\N	\N	0	0	\N
430	1222951298	t	English	UTC	09:00:00	t	t	2025-10-26 18:24:41.396575+00	\N	\N	0	0	\N
431	7080616729	t	Russian	UTC	09:00:00	t	t	2025-10-27 10:54:37.038018+00	\N	\N	0	0	\N
433	6834647836	t	Hebrew	UTC	09:00:00	t	t	2025-10-27 20:24:12.080822+00	\N	\N	0	0	\N
434	6842171874	t	Spanish	UTC	09:00:00	t	t	2025-10-28 12:30:18.804934+00	\N	\N	0	0	\N
435	150927061	t	Russian	UTC	09:00:00	t	t	2025-10-29 18:26:02.968834+00	\N	\N	0	0	\N
316	6458566821	t	English	UTC	09:00:00	t	t	2025-10-05 15:14:52.751981+00	\N	\N	0	0	\N
437	264846544	t	Russian	UTC	09:00:00	t	t	2025-10-29 20:30:27.118649+00	\N	\N	0	0	\N
438	1072201482	t	German	UTC	09:00:00	t	t	2025-10-30 05:19:25.51+00	\N	\N	0	0	\N
439	257118001	t	Russian	UTC	09:00:00	t	t	2025-10-30 10:38:25.932223+00	\N	\N	0	0	\N
440	8043230106	t	Russian	UTC	09:00:00	t	t	2025-10-30 23:21:33.048454+00	\N	\N	0	0	\N
442	5610316170	t	English	UTC	09:00:00	t	t	2025-11-01 00:12:12.876323+00	\N	\N	0	0	\N
443	8202955608	t	English	UTC	09:00:00	t	t	2025-11-02 12:41:26.623979+00	\N	\N	0	0	\N
444	7487795512	t	English	UTC	09:00:00	t	t	2025-11-02 13:33:16.242848+00	\N	\N	0	0	\N
445	6197011645	t	English	UTC	09:00:00	t	t	2025-11-02 18:42:34.031764+00	\N	\N	0	0	\N
446	680582708	t	Russian	UTC	09:00:00	t	t	2025-11-04 08:47:21.993169+00	\N	\N	0	0	\N
\.


--
-- Data for Name: test_broadcasts; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.test_broadcasts (id, admin_id, test_content, test_image_url, target_languages, created_at, sent_at, status, notes) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.users (id, telegram_user_id, username, first_name, last_name, language_code, created_at, last_interaction, is_bot, is_premium, is_blocked, total_wisdom_requests, total_quiz_attempts, last_wisdom_topic, user_data, updated_at) FROM stdin;
6	123	\N	\N	\N	en	2025-09-01 17:25:43.921029+00	2025-09-03 11:51:56.971125+00	f	f	f	0	0	\N	{"id": 123}	2025-09-03 11:51:56.971125+00
69	456	test_user	\N	\N	en	2025-09-03 12:04:09.883525+00	2025-09-03 12:04:09.883525+00	f	f	f	0	0	\N	{"id": 456, "username": "test_user", "language_code": "en"}	2025-09-03 12:04:09.883525+00
70	31126146	iam1ocky	Dmitriy	Galkin	en	2025-09-03 13:38:42.946361+00	2025-09-03 13:38:42.946361+00	f	f	f	0	0	\N	{"id": 31126146, "is_bot": false, "username": "iam1ocky", "last_name": "Galkin", "first_name": "Dmitriy", "language_code": "en"}	2025-09-03 13:38:42.946361+00
72	67518954	mouetteification	Lara	Martynova	ru	2025-09-03 20:04:59.546284+00	2025-09-03 20:04:59.546284+00	f	t	f	0	0	\N	{"id": 67518954, "is_bot": false, "username": "mouetteification", "last_name": "Martynova", "first_name": "Lara", "is_premium": true, "language_code": "ru"}	2025-09-03 20:04:59.546284+00
73	6952108531	\N	Ο Χρισ	\N	en	2025-09-03 20:18:44.802194+00	2025-09-03 20:18:44.802194+00	f	f	f	0	0	\N	{"id": 6952108531, "is_bot": false, "first_name": "Ο Χρισ", "language_code": "en"}	2025-09-03 20:18:44.802194+00
74	5287789980	\N	Rashad	Bakar	en	2025-09-03 21:31:40.948241+00	2025-09-03 21:31:40.948241+00	f	f	f	0	0	\N	{"id": 5287789980, "is_bot": false, "last_name": "Bakar", "first_name": "Rashad", "language_code": "en"}	2025-09-03 21:31:40.948241+00
75	6363994226	Onlyeslam1	Barham~♡	〔🖤🕊️☝🏻〕	en	2025-09-03 23:43:06.463158+00	2025-09-03 23:43:06.463158+00	f	f	f	0	0	\N	{"id": 6363994226, "is_bot": false, "username": "Onlyeslam1", "last_name": "〔🖤🕊️☝🏻〕", "first_name": "Barham~♡", "language_code": "en"}	2025-09-03 23:43:06.463158+00
11	12345	\N	\N	\N	en	2025-09-01 20:41:15.679793+00	2025-09-01 20:41:15.679793+00	f	f	f	0	0	\N	{"id": 12345}	2025-09-01 20:41:15.679793+00
76	8148436015	\N	Jane	Rose	en	2025-09-04 00:27:54.932283+00	2025-09-04 00:27:54.932283+00	f	f	f	0	0	\N	{"id": 8148436015, "is_bot": false, "last_name": "Rose", "first_name": "Jane", "language_code": "en"}	2025-09-04 00:27:54.932283+00
77	427948100	zaharia_m	Захарья	Мататьяу	ru	2025-09-04 06:14:15.84572+00	2025-09-04 06:14:15.84572+00	f	f	f	0	0	\N	{"id": 427948100, "is_bot": false, "username": "zaharia_m", "last_name": "Мататьяу", "first_name": "Захарья", "language_code": "ru"}	2025-09-04 06:14:15.84572+00
14	822722753	kiloony	нюта	\N	ru	2025-09-02 06:41:55.815111+00	2025-09-02 06:41:55.815111+00	f	t	f	0	0	\N	{"id": 822722753, "is_bot": false, "username": "kiloony", "first_name": "нюта", "is_premium": true, "language_code": "ru"}	2025-09-02 06:41:55.815111+00
78	6534457085	\N	Jack	\N	ar	2025-09-04 17:43:49.246828+00	2025-09-04 17:43:49.246828+00	f	f	f	0	0	\N	{"id": 6534457085, "is_bot": false, "first_name": "Jack", "language_code": "ar"}	2025-09-04 17:43:49.246828+00
142	982704568	REPENT120	Biruk	\N	en	2025-09-05 17:43:56.27419+00	2025-09-05 17:43:56.27419+00	f	f	f	0	0	\N	{"id": 982704568, "is_bot": false, "username": "REPENT120", "first_name": "Biruk", "language_code": "en"}	2025-09-05 17:43:56.27419+00
144	6587666086	fintechvisioner	Fintech	Visioner	ru	2025-09-05 21:23:39.286955+00	2025-09-05 21:23:53.765589+00	f	t	f	0	0	\N	{"id": 6587666086, "is_bot": false, "username": "fintechvisioner", "last_name": "Visioner", "first_name": "Fintech", "is_premium": true, "language_code": "ru"}	2025-09-05 21:23:53.765589+00
146	7064637241	\N	Deeq	\N	en	2025-09-06 09:18:35.500096+00	2025-09-06 09:18:35.500096+00	f	f	f	0	0	\N	{"id": 7064637241, "is_bot": false, "first_name": "Deeq", "language_code": "en"}	2025-09-06 09:18:35.500096+00
147	1555718844	Saharadayanne	Dayanne שלוס	\N	es	2025-09-06 20:33:20.205925+00	2025-09-06 20:33:20.205925+00	f	f	f	0	0	\N	{"id": 1555718844, "is_bot": false, "username": "Saharadayanne", "first_name": "Dayanne שלוס", "language_code": "es"}	2025-09-06 20:33:20.205925+00
148	7105471939	goharcity	S	Y	fa	2025-09-06 22:51:29.822483+00	2025-09-06 22:51:29.822483+00	f	f	f	0	0	\N	{"id": 7105471939, "is_bot": false, "username": "goharcity", "last_name": "Y", "first_name": "S", "language_code": "fa"}	2025-09-06 22:51:29.822483+00
149	5114151095	jblmel	ЖБ	Л	en	2025-09-07 13:30:06.094586+00	2025-09-07 13:30:06.094586+00	f	f	f	0	0	\N	{"id": 5114151095, "is_bot": false, "username": "jblmel", "last_name": "Л", "first_name": "ЖБ", "language_code": "en"}	2025-09-07 13:30:06.094586+00
150	7560435904	Revivaldoesntcamebysleeping	Mulei	Revival	en	2025-09-08 02:53:06.667581+00	2025-09-08 02:53:06.667581+00	f	f	f	0	0	\N	{"id": 7560435904, "is_bot": false, "username": "Revivaldoesntcamebysleeping", "last_name": "Revival", "first_name": "Mulei", "language_code": "en"}	2025-09-08 02:53:06.667581+00
151	177509235	maxgolovkin	Max	Golovkin	ru	2025-09-08 06:31:55.382665+00	2025-09-08 06:31:55.382665+00	f	t	f	0	0	\N	{"id": 177509235, "is_bot": false, "username": "maxgolovkin", "last_name": "Golovkin", "first_name": "Max", "is_premium": true, "language_code": "ru"}	2025-09-08 06:31:55.382665+00
152	5118483797	hasanboyev_0904	hasanboyev	\N	uz	2025-09-08 09:24:51.033502+00	2025-09-08 09:24:51.033502+00	f	f	f	0	0	\N	{"id": 5118483797, "is_bot": false, "username": "hasanboyev_0904", "first_name": "hasanboyev", "language_code": "uz"}	2025-09-08 09:24:51.033502+00
153	6269732115	Ocean2134	Ocean	\N	ru	2025-09-08 11:26:33.816902+00	2025-09-08 11:26:33.816902+00	f	f	f	0	0	\N	{"id": 6269732115, "is_bot": false, "username": "Ocean2134", "first_name": "Ocean", "language_code": "ru"}	2025-09-08 11:26:33.816902+00
37	354007772	RyabcevVS	Вячеслав	Рябцев	ru	2025-09-02 16:15:14.086824+00	2025-09-02 16:15:14.086824+00	f	t	f	0	0	\N	{"id": 354007772, "is_bot": false, "username": "RyabcevVS", "last_name": "Рябцев", "first_name": "Вячеслав", "is_premium": true, "language_code": "ru"}	2025-09-02 16:15:14.086824+00
156	6029332831	\N	Musk	\N	en	2025-09-09 13:01:02.885677+00	2025-09-09 13:01:02.885677+00	f	f	f	0	0	\N	{"id": 6029332831, "is_bot": false, "first_name": "Musk", "language_code": "en"}	2025-09-09 13:01:02.885677+00
111	1826148571	amirhossainasghari	Amir.H.Asghari	\N	fa	2025-09-05 07:48:35.789145+00	2025-09-05 07:48:35.789145+00	f	f	f	0	0	\N	{"id": 1826148571, "is_bot": false, "username": "amirhossainasghari", "first_name": "Amir.H.Asghari", "language_code": "fa"}	2025-09-05 07:48:35.789145+00
5	7057240608	zohan	Zohan	\N	ru	2025-09-01 17:25:38.628294+00	2025-09-05 11:18:47.126487+00	f	t	f	0	0	\N	{"id": 7057240608, "is_bot": false, "username": "zohan", "first_name": "Zohan", "is_premium": true, "language_code": "ru"}	2025-09-05 11:18:47.126487+00
52	5030166891	whymethis	Nick	\N	en	2025-09-03 05:46:39.442473+00	2025-09-03 05:46:39.442473+00	f	t	f	0	0	\N	{"id": 5030166891, "is_bot": false, "username": "whymethis", "first_name": "Nick", "is_premium": true, "language_code": "en"}	2025-09-03 05:46:39.442473+00
7	6630727156	david_vibe	David V.	\N	ru	2025-09-01 17:29:48.195236+00	2025-10-13 13:26:05.722509+00	f	t	f	0	0	\N	{"id": 6630727156, "is_bot": false, "username": "david_vibe", "first_name": "David V.", "is_premium": true, "language_code": "ru"}	2025-10-13 13:26:05.722509+00
1	215335	nedochetov	Aleksandr	Nedochetov	ru	2025-09-01 17:25:35.548776+00	2025-10-31 12:41:16.898928+00	f	t	f	0	0	\N	{"id": 215335, "is_bot": false, "username": "nedochetov", "last_name": "Nedochetov", "first_name": "Aleksandr", "is_premium": true, "language_code": "ru"}	2025-10-31 12:41:16.898928+00
54	123456	\N	Test	\N	en	2025-09-03 09:30:29.763514+00	2025-09-03 09:30:52.535876+00	f	f	f	0	0	\N	{"id": 123456, "first_name": "Test"}	2025-09-03 09:30:52.535876+00
59	454009966	nonamehasa	Василий	\N	en	2025-09-03 09:32:19.165872+00	2025-09-03 09:32:19.165872+00	f	f	f	0	0	\N	{"id": 454009966, "is_bot": false, "username": "nonamehasa", "first_name": "Василий", "language_code": "en"}	2025-09-03 09:32:19.165872+00
127	111111111	test_servicecontainer	\N	\N	en	2025-09-05 11:53:51.418781+00	2025-09-05 11:53:51.418781+00	f	f	f	0	0	\N	{"id": 111111111, "username": "test_servicecontainer"}	2025-09-05 11:53:51.418781+00
159	371684516	fugarov	Nikolay	Fugarov	ru	2025-09-09 21:18:59.522704+00	2025-09-09 21:18:59.938784+00	f	t	f	0	0	\N	{"id": 371684516, "is_bot": false, "username": "fugarov", "last_name": "Fugarov", "first_name": "Nikolay", "is_premium": true, "language_code": "ru"}	2025-09-09 21:18:59.938784+00
161	171878750	\N	Sophie	🪬🤲	ru	2025-09-10 05:34:19.562311+00	2025-09-10 05:34:19.562311+00	f	f	f	0	0	\N	{"id": 171878750, "is_bot": false, "last_name": "🪬🤲", "first_name": "Sophie", "language_code": "ru"}	2025-09-10 05:34:19.562311+00
164	1856803179	Furnishatableinc	Restore	Alighn	en	2025-09-11 10:09:59.690248+00	2025-09-11 10:09:59.690248+00	f	f	f	0	0	\N	{"id": 1856803179, "is_bot": false, "username": "Furnishatableinc", "last_name": "Alighn", "first_name": "Restore", "language_code": "en"}	2025-09-11 10:09:59.690248+00
165	822889431	YitzhakNewton	Kumao(熊雄)	\N	en	2025-09-11 12:51:28.183649+00	2025-09-11 12:51:28.183649+00	f	f	f	0	0	\N	{"id": 822889431, "is_bot": false, "username": "YitzhakNewton", "first_name": "Kumao(熊雄)", "language_code": "en"}	2025-09-11 12:51:28.183649+00
166	5330685646	\N	Tushal D	\N	en	2025-09-11 13:37:21.397793+00	2025-09-11 13:37:21.397793+00	f	f	f	0	0	\N	{"id": 5330685646, "is_bot": false, "first_name": "Tushal D", "language_code": "en"}	2025-09-11 13:37:21.397793+00
167	6411996480	nana34021	A✨	\N	fr	2025-09-11 20:25:59.915838+00	2025-09-11 20:25:59.915838+00	f	f	f	0	0	\N	{"id": 6411996480, "is_bot": false, "username": "nana34021", "first_name": "A✨", "language_code": "fr"}	2025-09-11 20:25:59.915838+00
168	984329227	anyasok	anya🎗️	\N	en	2025-09-14 11:20:53.166329+00	2025-09-14 11:20:53.166329+00	f	t	f	0	0	\N	{"id": 984329227, "is_bot": false, "username": "anyasok", "first_name": "anya🎗️", "is_premium": true, "language_code": "en"}	2025-09-14 11:20:53.166329+00
169	6309222119	notbland	Ron	\N	en	2025-09-14 20:27:25.504248+00	2025-09-14 20:27:25.504248+00	f	t	f	0	0	\N	{"id": 6309222119, "is_bot": false, "username": "notbland", "first_name": "Ron", "is_premium": true, "language_code": "en"}	2025-09-14 20:27:25.504248+00
170	943605976	brnlix	baran	\N	en	2025-09-14 22:24:16.178703+00	2025-09-14 22:24:16.178703+00	f	f	f	0	0	\N	{"id": 943605976, "is_bot": false, "username": "brnlix", "first_name": "baran", "language_code": "en"}	2025-09-14 22:24:16.178703+00
171	1170190175	miryamsaritvalenski	Miryam Sarit	Valenski	en	2025-09-15 10:25:56.891481+00	2025-09-15 10:25:56.891481+00	f	f	f	0	0	\N	{"id": 1170190175, "is_bot": false, "username": "miryamsaritvalenski", "last_name": "Valenski", "first_name": "Miryam Sarit", "language_code": "en"}	2025-09-15 10:25:56.891481+00
172	8364612041	\N	Aman	\N	en	2025-09-15 11:00:53.258566+00	2025-09-15 11:00:53.258566+00	f	f	f	0	0	\N	{"id": 8364612041, "is_bot": false, "first_name": "Aman", "language_code": "en"}	2025-09-15 11:00:53.258566+00
173	7094910035	\N	Hii	\N	en	2025-09-15 16:38:24.772027+00	2025-09-15 16:38:24.772027+00	f	f	f	0	0	\N	{"id": 7094910035, "is_bot": false, "first_name": "Hii", "language_code": "en"}	2025-09-15 16:38:24.772027+00
174	6044608391	JerryShafow	🇮🇳 Dr Aditi Wayne	🇮🇳📚	en	2025-09-15 20:59:25.089471+00	2025-09-15 20:59:25.089471+00	f	t	f	0	0	\N	{"id": 6044608391, "is_bot": false, "username": "JerryShafow", "last_name": "🇮🇳📚", "first_name": "🇮🇳 Dr Aditi Wayne", "is_premium": true, "language_code": "en"}	2025-09-15 20:59:25.089471+00
175	2125464300	\N	Naaaz	\N	en	2025-09-15 21:40:16.384081+00	2025-09-15 21:40:16.384081+00	f	f	f	0	0	\N	{"id": 2125464300, "is_bot": false, "first_name": "Naaaz", "language_code": "en"}	2025-09-15 21:40:16.384081+00
176	1953435121	\N	Stranger	\N	en	2025-09-16 08:40:36.939707+00	2025-09-16 08:40:36.939707+00	f	f	f	0	0	\N	{"id": 1953435121, "is_bot": false, "first_name": "Stranger", "language_code": "en"}	2025-09-16 08:40:36.939707+00
177	1564068820	Salafi5601	ELEVEN	\N	en	2025-09-17 12:08:04.818799+00	2025-09-17 12:08:04.818799+00	f	f	f	0	0	\N	{"id": 1564068820, "is_bot": false, "username": "Salafi5601", "first_name": "ELEVEN", "language_code": "en"}	2025-09-17 12:08:04.818799+00
178	7660474342	Hailchr	Bur	\N	ru	2025-09-17 16:38:30.099926+00	2025-09-17 16:38:30.099926+00	f	f	f	0	0	\N	{"id": 7660474342, "is_bot": false, "username": "Hailchr", "first_name": "Bur", "language_code": "ru"}	2025-09-17 16:38:30.099926+00
179	1552107375	gotype	Брат Васыль	\N	en	2025-09-18 23:10:35.085019+00	2025-09-18 23:10:35.085019+00	f	f	f	0	0	\N	{"id": 1552107375, "is_bot": false, "username": "gotype", "first_name": "Брат Васыль", "language_code": "en"}	2025-09-18 23:10:35.085019+00
180	7930538909	BoilzzzL	nlonv	Zageeee	id	2025-09-19 01:35:32.93073+00	2025-09-19 01:35:32.93073+00	f	f	f	0	0	\N	{"id": 7930538909, "is_bot": false, "username": "BoilzzzL", "last_name": "Zageeee", "first_name": "nlonv", "language_code": "id"}	2025-09-19 01:35:32.93073+00
181	422150282	Farlaway	Victoria	Lavreniuk	fr	2025-09-19 02:53:04.253392+00	2025-09-19 02:53:04.253392+00	f	f	f	0	0	\N	{"id": 422150282, "is_bot": false, "username": "Farlaway", "last_name": "Lavreniuk", "first_name": "Victoria", "language_code": "fr"}	2025-09-19 02:53:04.253392+00
182	840665822	\N	Rahul	Sarvaiya	en	2025-09-19 04:56:36.264187+00	2025-09-19 04:56:36.264187+00	f	f	f	0	0	\N	{"id": 840665822, "is_bot": false, "last_name": "Sarvaiya", "first_name": "Rahul", "language_code": "en"}	2025-09-19 04:56:36.264187+00
183	6652298761	\N	Laksh	Gawde	en	2025-09-19 07:27:56.030623+00	2025-09-19 07:27:56.030623+00	f	f	f	0	0	\N	{"id": 6652298761, "is_bot": false, "last_name": "Gawde", "first_name": "Laksh", "language_code": "en"}	2025-09-19 07:27:56.030623+00
184	588617031	heusbandd	ddd	\N	ru	2025-09-19 08:05:32.882523+00	2025-09-19 08:05:32.882523+00	f	f	f	0	0	\N	{"id": 588617031, "is_bot": false, "username": "heusbandd", "first_name": "ddd", "language_code": "ru"}	2025-09-19 08:05:32.882523+00
185	207866676	natalymusikhina	Nataly	Musikhina/ Safonova	ru	2025-09-19 08:22:54.556393+00	2025-09-19 08:22:54.556393+00	f	t	f	0	0	\N	{"id": 207866676, "is_bot": false, "username": "natalymusikhina", "last_name": "Musikhina/ Safonova", "first_name": "Nataly", "is_premium": true, "language_code": "ru"}	2025-09-19 08:22:54.556393+00
186	109048024	valeria_nikolya	Valeria	\N	ru	2025-09-19 15:01:27.37394+00	2025-09-19 15:01:27.37394+00	f	f	f	0	0	\N	{"id": 109048024, "is_bot": false, "username": "valeria_nikolya", "first_name": "Valeria", "language_code": "ru"}	2025-09-19 15:01:27.37394+00
187	327241593	JTerzo	Yulya	\N	ru	2025-09-19 15:17:52.499431+00	2025-09-19 15:17:52.499431+00	f	t	f	0	0	\N	{"id": 327241593, "is_bot": false, "username": "JTerzo", "first_name": "Yulya", "is_premium": true, "language_code": "ru"}	2025-09-19 15:17:52.499431+00
188	160723514	sonchys	Sonya	\N	ru	2025-09-19 15:37:20.516919+00	2025-09-19 15:37:20.516919+00	f	t	f	0	0	\N	{"id": 160723514, "is_bot": false, "username": "sonchys", "first_name": "Sonya", "is_premium": true, "language_code": "ru"}	2025-09-19 15:37:20.516919+00
190	6328396822	owrism	Gg	\N	en	2025-09-20 18:53:24.512787+00	2025-09-20 18:53:24.512787+00	f	f	f	0	0	\N	{"id": 6328396822, "is_bot": false, "username": "owrism", "first_name": "Gg", "language_code": "en"}	2025-09-20 18:53:24.512787+00
191	6445848544	THE_FlRMAMENT	ⵣ 𝗞𝗔𝗪𝗔𝗭𝗔𝗞𝗜 ꑭ	\N	fr	2025-09-20 20:19:24.488505+00	2025-09-20 20:19:24.488505+00	f	f	f	0	0	\N	{"id": 6445848544, "is_bot": false, "username": "THE_FlRMAMENT", "first_name": "ⵣ 𝗞𝗔𝗪𝗔𝗭𝗔𝗞𝗜 ꑭ", "language_code": "fr"}	2025-09-20 20:19:24.488505+00
192	7921564756	Gaubu_daubu	Gaubu	Daubu	en	2025-09-20 20:20:27.627633+00	2025-09-20 20:20:27.627633+00	f	f	f	0	0	\N	{"id": 7921564756, "is_bot": false, "username": "Gaubu_daubu", "last_name": "Daubu", "first_name": "Gaubu", "language_code": "en"}	2025-09-20 20:20:27.627633+00
193	7107917224	\N	Grey guy	\N	de	2025-09-20 21:14:28.149737+00	2025-09-20 21:14:28.149737+00	f	f	f	0	0	\N	{"id": 7107917224, "is_bot": false, "first_name": "Grey guy", "language_code": "de"}	2025-09-20 21:14:28.149737+00
194	47284045	dacrime	Alexey Toropov	\N	ru	2025-09-22 16:59:58.906966+00	2025-09-22 16:59:58.906966+00	f	t	f	0	0	\N	{"id": 47284045, "is_bot": false, "username": "dacrime", "first_name": "Alexey Toropov", "is_premium": true, "language_code": "ru"}	2025-09-22 16:59:58.906966+00
195	8414586612	\N	Lisa	De Wet	en	2025-09-22 19:35:36.441686+00	2025-09-22 19:35:36.441686+00	f	f	f	0	0	\N	{"id": 8414586612, "is_bot": false, "last_name": "De Wet", "first_name": "Lisa", "language_code": "en"}	2025-09-22 19:35:36.441686+00
196	528842488	dianabllz	D	\N	uk	2025-09-23 00:23:47.683001+00	2025-09-23 00:23:47.683001+00	f	t	f	0	0	\N	{"id": 528842488, "is_bot": false, "username": "dianabllz", "first_name": "D", "is_premium": true, "language_code": "uk"}	2025-09-23 00:23:47.683001+00
197	7662402291	HolySpiritOurComforter_Advocate	Steven	Schick	en	2025-09-23 04:24:28.821294+00	2025-09-23 04:24:28.821294+00	f	f	f	0	0	\N	{"id": 7662402291, "is_bot": false, "username": "HolySpiritOurComforter_Advocate", "last_name": "Schick", "first_name": "Steven", "language_code": "en"}	2025-09-23 04:24:28.821294+00
198	7578030596	wineguy82	Eric	O’Connor	en	2025-09-24 08:57:14.154432+00	2025-09-24 08:57:14.154432+00	f	f	f	0	0	\N	{"id": 7578030596, "is_bot": false, "username": "wineguy82", "last_name": "O’Connor", "first_name": "Eric", "language_code": "en"}	2025-09-24 08:57:14.154432+00
199	5464572799	\N	zhou	Angkk	en	2025-09-25 11:43:07.908184+00	2025-09-25 11:43:07.908184+00	f	f	f	0	0	\N	{"id": 5464572799, "is_bot": false, "last_name": "Angkk", "first_name": "zhou", "language_code": "en"}	2025-09-25 11:43:07.908184+00
200	1005837694	Reiver3	ניקולאי	\N	ru	2025-09-27 06:24:17.365667+00	2025-09-27 06:24:17.365667+00	f	t	f	0	0	\N	{"id": 1005837694, "is_bot": false, "username": "Reiver3", "first_name": "ניקולאי", "is_premium": true, "language_code": "ru"}	2025-09-27 06:24:17.365667+00
201	7539436948	Gzooop	Gzooop	\N	en	2025-09-27 22:17:01.965927+00	2025-09-27 22:17:01.965927+00	f	f	f	0	0	\N	{"id": 7539436948, "is_bot": false, "username": "Gzooop", "first_name": "Gzooop", "language_code": "en"}	2025-09-27 22:17:01.965927+00
202	6368188743	zavidonov	Тимур	Завидонов	ru	2025-09-28 08:31:25.687566+00	2025-09-28 08:31:25.687566+00	f	f	f	0	0	\N	{"id": 6368188743, "is_bot": false, "username": "zavidonov", "last_name": "Завидонов", "first_name": "Тимур", "language_code": "ru"}	2025-09-28 08:31:25.687566+00
203	1782586181	Bestfx8472	Jefferson	Rodrigues	pt-br	2025-09-28 09:35:05.821606+00	2025-09-28 09:35:05.821606+00	f	f	f	0	0	\N	{"id": 1782586181, "is_bot": false, "username": "Bestfx8472", "last_name": "Rodrigues", "first_name": "Jefferson", "language_code": "pt-br"}	2025-09-28 09:35:05.821606+00
208	6650435700	RA_8008	R..	\N	en	2025-09-29 05:09:41.693116+00	2025-09-29 05:09:41.693116+00	f	f	f	0	0	\N	{"id": 6650435700, "is_bot": false, "username": "RA_8008", "first_name": "R..", "language_code": "en"}	2025-09-29 05:09:41.693116+00
210	741786918	snegowskaya	Irina	\N	ru	2025-09-30 14:07:49.924903+00	2025-09-30 14:07:49.924903+00	f	t	f	0	0	\N	{"id": 741786918, "is_bot": false, "username": "snegowskaya", "first_name": "Irina", "is_premium": true, "language_code": "ru"}	2025-09-30 14:07:49.924903+00
211	1297394659	\N	Kush	Sharma	en	2025-09-30 19:04:59.429031+00	2025-09-30 19:04:59.429031+00	f	f	f	0	0	\N	{"id": 1297394659, "is_bot": false, "last_name": "Sharma", "first_name": "Kush", "language_code": "en"}	2025-09-30 19:04:59.429031+00
212	8405872912	Ramchilaka	Moon	\N	en	2025-10-02 13:45:09.519451+00	2025-10-02 13:45:09.519451+00	f	f	f	0	0	\N	{"id": 8405872912, "is_bot": false, "username": "Ramchilaka", "first_name": "Moon", "language_code": "en"}	2025-10-02 13:45:09.519451+00
213	261113926	estherroiz	בלאַזן	\N	en	2025-10-02 19:01:48.630231+00	2025-10-02 19:01:48.630231+00	f	f	f	0	0	\N	{"id": 261113926, "is_bot": false, "username": "estherroiz", "first_name": "בלאַזן", "language_code": "en"}	2025-10-02 19:01:48.630231+00
214	126595368	beni131313133	Beni33	\N	en	2025-10-03 15:06:25.142236+00	2025-10-03 15:15:31.089001+00	f	f	f	0	0	\N	{"id": 126595368, "is_bot": false, "username": "beni131313133", "first_name": "Beni33", "language_code": "en"}	2025-10-03 15:15:31.089001+00
216	6888754964	\N	Marcus	\N	de	2025-10-03 17:02:02.288491+00	2025-10-03 17:02:02.288491+00	f	f	f	0	0	\N	{"id": 6888754964, "is_bot": false, "first_name": "Marcus", "language_code": "de"}	2025-10-03 17:02:02.288491+00
217	5681426744	hjfh6477	I	M	en	2025-10-03 17:10:03.768834+00	2025-10-03 17:10:03.768834+00	f	f	f	0	0	\N	{"id": 5681426744, "is_bot": false, "username": "hjfh6477", "last_name": "M", "first_name": "I", "language_code": "en"}	2025-10-03 17:10:03.768834+00
218	129542059	\N	V	S	en	2025-10-03 17:34:31.724326+00	2025-10-03 17:34:31.724326+00	f	f	f	0	0	\N	{"id": 129542059, "is_bot": false, "last_name": "S", "first_name": "V", "language_code": "en"}	2025-10-03 17:34:31.724326+00
219	5747645852	solnunn	ន០ɭ• סוֹל 🪔	\N	es	2025-10-03 20:09:14.872687+00	2025-10-03 20:09:14.872687+00	f	t	f	0	0	\N	{"id": 5747645852, "is_bot": false, "username": "solnunn", "first_name": "ន០ɭ• סוֹל 🪔", "is_premium": true, "language_code": "es"}	2025-10-03 20:09:14.872687+00
220	6978463557	Rusplakh	Ruslan	Plakhutin	ru	2025-10-03 20:30:18.95622+00	2025-10-03 20:30:18.95622+00	f	f	f	0	0	\N	{"id": 6978463557, "is_bot": false, "username": "Rusplakh", "last_name": "Plakhutin", "first_name": "Ruslan", "language_code": "ru"}	2025-10-03 20:30:18.95622+00
221	946710923	JABS_79	Anderson	Blanco	es	2025-10-03 20:32:22.157462+00	2025-10-03 20:32:22.157462+00	f	f	f	0	0	\N	{"id": 946710923, "is_bot": false, "username": "JABS_79", "last_name": "Blanco", "first_name": "Anderson", "language_code": "es"}	2025-10-03 20:32:22.157462+00
222	5249566335	MrsSurikata	Viktoriya	Kozina	ru	2025-10-03 20:52:43.470314+00	2025-10-03 20:52:43.470314+00	f	f	f	0	0	\N	{"id": 5249566335, "is_bot": false, "username": "MrsSurikata", "last_name": "Kozina", "first_name": "Viktoriya", "language_code": "ru"}	2025-10-03 20:52:43.470314+00
223	6831339695	MintLover	🐰 DD	🐰	en	2025-10-03 20:59:57.643085+00	2025-10-03 20:59:57.643085+00	f	f	f	0	0	\N	{"id": 6831339695, "is_bot": false, "username": "MintLover", "last_name": "🐰", "first_name": "🐰 DD", "language_code": "en"}	2025-10-03 20:59:57.643085+00
224	5554678952	\N	Praveen	K	en	2025-10-03 21:03:39.250282+00	2025-10-03 21:03:39.250282+00	f	f	f	0	0	\N	{"id": 5554678952, "is_bot": false, "last_name": "K", "first_name": "Praveen", "language_code": "en"}	2025-10-03 21:03:39.250282+00
225	5615101684	Vlanako	Куратор Natali	\N	ru	2025-10-03 21:14:17.760703+00	2025-10-03 21:14:17.760703+00	f	t	f	0	0	\N	{"id": 5615101684, "is_bot": false, "username": "Vlanako", "first_name": "Куратор Natali", "is_premium": true, "language_code": "ru"}	2025-10-03 21:14:17.760703+00
226	7144105860	malovaart	Malovaart	\N	en	2025-10-03 21:24:03.639521+00	2025-10-03 21:24:03.639521+00	f	f	f	0	0	\N	{"id": 7144105860, "is_bot": false, "username": "malovaart", "first_name": "Malovaart", "language_code": "en"}	2025-10-03 21:24:03.639521+00
227	250152350	nedochetova_ma	Мария	Недочетова	ru	2025-10-03 21:45:29.711391+00	2025-10-03 21:45:29.711391+00	f	t	f	0	0	\N	{"id": 250152350, "is_bot": false, "username": "nedochetova_ma", "last_name": "Недочетова", "first_name": "Мария", "is_premium": true, "language_code": "ru"}	2025-10-03 21:45:29.711391+00
228	745427964	\N	Mark	\N	ru	2025-10-03 23:27:19.578423+00	2025-10-03 23:27:19.578423+00	f	f	f	0	0	\N	{"id": 745427964, "is_bot": false, "first_name": "Mark", "language_code": "ru"}	2025-10-03 23:27:19.578423+00
229	543447442	Ptxko	haha	\N	fa	2025-10-04 07:41:09.889007+00	2025-10-04 07:41:09.889007+00	f	f	f	0	0	\N	{"id": 543447442, "is_bot": false, "username": "Ptxko", "first_name": "haha", "language_code": "fa"}	2025-10-04 07:41:09.889007+00
230	5249381610	\N	Dom	\N	en	2025-10-04 08:08:25.059518+00	2025-10-04 08:08:25.059518+00	f	f	f	0	0	\N	{"id": 5249381610, "is_bot": false, "first_name": "Dom", "language_code": "en"}	2025-10-04 08:08:25.059518+00
231	5284659496	Mikha_Al	Михо	Эль	ru	2025-10-04 08:42:30.080622+00	2025-10-04 08:42:30.080622+00	f	f	f	0	0	\N	{"id": 5284659496, "is_bot": false, "username": "Mikha_Al", "last_name": "Эль", "first_name": "Михо", "language_code": "ru"}	2025-10-04 08:42:30.080622+00
232	7775146035	\N	Aleksandar	Ciric	en	2025-10-04 09:13:29.544002+00	2025-10-04 09:13:29.544002+00	f	f	f	0	0	\N	{"id": 7775146035, "is_bot": false, "last_name": "Ciric", "first_name": "Aleksandar", "language_code": "en"}	2025-10-04 09:13:29.544002+00
233	62036930	VladislavMusikhin	Vlad	Musikhin	ru	2025-10-04 10:06:55.480767+00	2025-10-04 10:06:55.480767+00	f	f	f	0	0	\N	{"id": 62036930, "is_bot": false, "username": "VladislavMusikhin", "last_name": "Musikhin", "first_name": "Vlad", "language_code": "ru"}	2025-10-04 10:06:55.480767+00
269	6350653649	\N	habarik	\N	en	2025-10-05 05:06:30.787735+00	2025-10-05 05:06:30.787735+00	f	f	f	0	0	\N	{"id": 6350653649, "is_bot": false, "first_name": "habarik", "language_code": "en"}	2025-10-05 05:06:30.787735+00
234	1667124224	hawkeyex303	Mr. Zombie Reagan	\N	en	2025-10-04 12:39:03.165373+00	2025-10-04 12:39:03.165373+00	f	t	f	0	0	\N	{"id": 1667124224, "is_bot": false, "username": "hawkeyex303", "first_name": "Mr. Zombie Reagan", "is_premium": true, "language_code": "en"}	2025-10-04 12:39:03.165373+00
235	287079394	paap1002	paap	\N	en	2025-10-04 15:09:12.256275+00	2025-10-04 15:09:12.256275+00	f	f	f	0	0	\N	{"id": 287079394, "is_bot": false, "username": "paap1002", "first_name": "paap", "language_code": "en"}	2025-10-04 15:09:12.256275+00
236	1546881779	\N	Leprechuan	Bob	en	2025-10-04 15:47:55.702118+00	2025-10-04 16:11:23.157795+00	f	t	f	0	0	\N	{"id": 1546881779, "is_bot": false, "last_name": "Bob", "first_name": "Leprechuan", "is_premium": true, "language_code": "en"}	2025-10-04 16:11:23.157795+00
238	165852222	elimeleh5708	נתן	\N	ru	2025-10-04 16:47:12.948891+00	2025-10-04 16:47:12.948891+00	f	t	f	0	0	\N	{"id": 165852222, "is_bot": false, "username": "elimeleh5708", "first_name": "נתן", "is_premium": true, "language_code": "ru"}	2025-10-04 16:47:12.948891+00
239	1958518123	\N	Anke	\N	de	2025-10-04 16:48:39.729135+00	2025-10-04 16:48:39.729135+00	f	f	f	0	0	\N	{"id": 1958518123, "is_bot": false, "first_name": "Anke", "language_code": "de"}	2025-10-04 16:48:39.729135+00
240	1309402200	\N	Juri	Nasirow	de	2025-10-04 17:11:13.42488+00	2025-10-04 17:11:13.42488+00	f	f	f	0	0	\N	{"id": 1309402200, "is_bot": false, "last_name": "Nasirow", "first_name": "Juri", "language_code": "de"}	2025-10-04 17:11:13.42488+00
241	1597736081	zad1sa	sss	\N	ru	2025-10-04 17:12:21.156353+00	2025-10-04 17:12:21.156353+00	f	t	f	0	0	\N	{"id": 1597736081, "is_bot": false, "username": "zad1sa", "first_name": "sss", "is_premium": true, "language_code": "ru"}	2025-10-04 17:12:21.156353+00
242	7390994963	blobofu	Bjblia	\N	ru	2025-10-04 17:42:43.828693+00	2025-10-04 17:42:43.828693+00	f	f	f	0	0	\N	{"id": 7390994963, "is_bot": false, "username": "blobofu", "first_name": "Bjblia", "language_code": "ru"}	2025-10-04 17:42:43.828693+00
243	5193896065	NardCS	𓊈𝑵꯭𝑨꯭𝑻꯭𝑯꯭𝒀 𑁍	𝑪꯭𝑯꯭𝑰꯭𝑴꯭𝑫꯭𝑰𓊉	en	2025-10-04 20:30:30.672244+00	2025-10-04 20:30:30.672244+00	f	f	f	0	0	\N	{"id": 5193896065, "is_bot": false, "username": "NardCS", "last_name": "𝑪꯭𝑯꯭𝑰꯭𝑴꯭𝑫꯭𝑰𓊉", "first_name": "𓊈𝑵꯭𝑨꯭𝑻꯭𝑯꯭𝒀 𑁍", "language_code": "en"}	2025-10-04 20:30:30.672244+00
244	6892428416	nonamefruit	No Name	\N	ru	2025-10-04 22:35:11.302492+00	2025-10-04 22:35:11.302492+00	f	t	f	0	0	\N	{"id": 6892428416, "is_bot": false, "username": "nonamefruit", "first_name": "No Name", "is_premium": true, "language_code": "ru"}	2025-10-04 22:35:11.302492+00
245	1659448634	DIOSAMA684	Yo	\N	es	2025-10-04 22:38:43.679194+00	2025-10-04 22:38:43.679194+00	f	f	f	0	0	\N	{"id": 1659448634, "is_bot": false, "username": "DIOSAMA684", "first_name": "Yo", "language_code": "es"}	2025-10-04 22:38:43.679194+00
246	1378251732	Hugo_us100	DAVID	\N	en	2025-10-04 23:11:41.441758+00	2025-10-04 23:11:41.441758+00	f	f	f	0	0	\N	{"id": 1378251732, "is_bot": false, "username": "Hugo_us100", "first_name": "DAVID", "language_code": "en"}	2025-10-04 23:11:41.441758+00
247	5990098796	\N	Howard	Feingold	en	2025-10-04 23:44:29.324304+00	2025-10-04 23:44:29.324304+00	f	f	f	0	0	\N	{"id": 5990098796, "is_bot": false, "last_name": "Feingold", "first_name": "Howard", "language_code": "en"}	2025-10-04 23:44:29.324304+00
248	7544606394	Newbieeeeeeeeeeeee	RH	\N	en	2025-10-05 00:50:45.662333+00	2025-10-05 00:50:45.662333+00	f	f	f	0	0	\N	{"id": 7544606394, "is_bot": false, "username": "Newbieeeeeeeeeeeee", "first_name": "RH", "language_code": "en"}	2025-10-05 00:50:45.662333+00
249	1708316144	\N	Michael	Dunaevsky	en	2025-10-05 01:17:46.120167+00	2025-10-05 01:17:46.120167+00	f	f	f	0	0	\N	{"id": 1708316144, "is_bot": false, "last_name": "Dunaevsky", "first_name": "Michael", "language_code": "en"}	2025-10-05 01:17:46.120167+00
250	7645010451	\N	Martin	Berman	en	2025-10-05 01:30:19.909945+00	2025-10-05 01:30:19.909945+00	f	f	f	0	0	\N	{"id": 7645010451, "is_bot": false, "last_name": "Berman", "first_name": "Martin", "language_code": "en"}	2025-10-05 01:30:19.909945+00
251	6369643886	nblfhmi7	nabil	\N	en	2025-10-05 01:43:00.116871+00	2025-10-05 01:43:00.116871+00	f	f	f	0	0	\N	{"id": 6369643886, "is_bot": false, "username": "nblfhmi7", "first_name": "nabil", "language_code": "en"}	2025-10-05 01:43:00.116871+00
252	965200380	ElenikaAl	Elena	\N	de	2025-10-05 01:49:31.312495+00	2025-10-05 01:49:31.312495+00	f	f	f	0	0	\N	{"id": 965200380, "is_bot": false, "username": "ElenikaAl", "first_name": "Elena", "language_code": "de"}	2025-10-05 01:49:31.312495+00
253	6471286973	\N	boster12	\N	es	2025-10-05 01:54:17.803212+00	2025-10-05 01:54:17.803212+00	f	f	f	0	0	\N	{"id": 6471286973, "is_bot": false, "first_name": "boster12", "language_code": "es"}	2025-10-05 01:54:17.803212+00
254	6808247296	\N	Jada	McWilliams	en	2025-10-05 01:57:28.094984+00	2025-10-05 01:57:28.094984+00	f	f	f	0	0	\N	{"id": 6808247296, "is_bot": false, "last_name": "McWilliams", "first_name": "Jada", "language_code": "en"}	2025-10-05 01:57:28.094984+00
255	8019989846	WeMakeAi	Ben 🎶	\N	he	2025-10-05 02:05:59.731127+00	2025-10-05 02:05:59.731127+00	f	f	f	0	0	\N	{"id": 8019989846, "is_bot": false, "username": "WeMakeAi", "first_name": "Ben 🎶", "language_code": "he"}	2025-10-05 02:05:59.731127+00
256	1541512996	Ben379	Ben	\N	en	2025-10-05 02:14:35.24365+00	2025-10-05 02:14:35.24365+00	f	f	f	0	0	\N	{"id": 1541512996, "is_bot": false, "username": "Ben379", "first_name": "Ben", "language_code": "en"}	2025-10-05 02:14:35.24365+00
257	6220451088	\N	Yohann	De'Farge	en	2025-10-05 02:30:47.620978+00	2025-10-05 02:30:47.620978+00	f	f	f	0	0	\N	{"id": 6220451088, "is_bot": false, "last_name": "De'Farge", "first_name": "Yohann", "language_code": "en"}	2025-10-05 02:30:47.620978+00
258	1229686563	calisunny	Marina	\N	en	2025-10-05 02:44:05.149659+00	2025-10-05 02:44:05.149659+00	f	f	f	0	0	\N	{"id": 1229686563, "is_bot": false, "username": "calisunny", "first_name": "Marina", "language_code": "en"}	2025-10-05 02:44:05.149659+00
259	8370380793	\N	Mega	Mind	en	2025-10-05 02:45:00.613715+00	2025-10-05 02:45:00.613715+00	f	f	f	0	0	\N	{"id": 8370380793, "is_bot": false, "last_name": "Mind", "first_name": "Mega", "language_code": "en"}	2025-10-05 02:45:00.613715+00
260	5322833967	\N	Yolanda	Hesch	en	2025-10-05 03:06:30.535486+00	2025-10-05 03:06:30.99374+00	f	f	f	0	0	\N	{"id": 5322833967, "is_bot": false, "last_name": "Hesch", "first_name": "Yolanda", "language_code": "en"}	2025-10-05 03:06:30.99374+00
262	6204287807	\N	Tomer	Zalait	en	2025-10-05 03:10:52.57748+00	2025-10-05 03:10:52.57748+00	f	f	f	0	0	\N	{"id": 6204287807, "is_bot": false, "last_name": "Zalait", "first_name": "Tomer", "language_code": "en"}	2025-10-05 03:10:52.57748+00
263	691739278	\N	Alex	\N	en	2025-10-05 03:27:21.296289+00	2025-10-05 03:27:21.296289+00	f	f	f	0	0	\N	{"id": 691739278, "is_bot": false, "first_name": "Alex", "language_code": "en"}	2025-10-05 03:27:21.296289+00
264	6101379779	Isaiah1819	Faraha	\N	en	2025-10-05 04:02:59.896376+00	2025-10-05 04:02:59.896376+00	f	f	f	0	0	\N	{"id": 6101379779, "is_bot": false, "username": "Isaiah1819", "first_name": "Faraha", "language_code": "en"}	2025-10-05 04:02:59.896376+00
265	1560020634	Jerrycandle	Darlington	Cheii	en	2025-10-05 04:05:04.809548+00	2025-10-05 04:05:04.809548+00	f	f	f	0	0	\N	{"id": 1560020634, "is_bot": false, "username": "Jerrycandle", "last_name": "Cheii", "first_name": "Darlington", "language_code": "en"}	2025-10-05 04:05:04.809548+00
266	7183012526	\N	Dileep	46	en	2025-10-05 04:56:36.445096+00	2025-10-05 04:56:36.445096+00	f	f	f	0	0	\N	{"id": 7183012526, "is_bot": false, "last_name": "46", "first_name": "Dileep", "language_code": "en"}	2025-10-05 04:56:36.445096+00
267	535705843	adelep1	adelep OYO SparkChain.AI RICH Meshchain.Ai 💛 Sons of Ton 🆙 UXUY	🧵🐐🦆🐤GraGraPOTUS 🔵 ONUSClick🥠🌱SEED🐤 + (adelep1) + Gra-Gra 🍒🐲👾 BIT	en	2025-10-05 05:01:22.952737+00	2025-10-05 05:01:22.952737+00	f	f	f	0	0	\N	{"id": 535705843, "is_bot": false, "username": "adelep1", "last_name": "🧵🐐🦆🐤GraGraPOTUS 🔵 ONUSClick🥠🌱SEED🐤 + (adelep1) + Gra-Gra 🍒🐲👾 BIT", "first_name": "adelep OYO SparkChain.AI RICH Meshchain.Ai 💛 Sons of Ton 🆙 UXUY", "language_code": "en"}	2025-10-05 05:01:22.952737+00
268	1593123837	\N	Kfir	\N	en	2025-10-05 05:02:15.180554+00	2025-10-05 05:02:15.180554+00	f	f	f	0	0	\N	{"id": 1593123837, "is_bot": false, "first_name": "Kfir", "language_code": "en"}	2025-10-05 05:02:15.180554+00
270	346704101	\N	Ivan	Studebaker	en	2025-10-05 06:10:44.451604+00	2025-10-05 06:10:44.451604+00	f	f	f	0	0	\N	{"id": 346704101, "is_bot": false, "last_name": "Studebaker", "first_name": "Ivan", "language_code": "en"}	2025-10-05 06:10:44.451604+00
271	704610936	katzsonya	Кристина	\N	ru	2025-10-05 11:13:09.427362+00	2025-10-05 11:13:09.427362+00	f	f	f	0	0	\N	{"id": 704610936, "is_bot": false, "username": "katzsonya", "first_name": "Кристина", "language_code": "ru"}	2025-10-05 11:13:09.427362+00
272	6177341806	goldashaffer	Alex-Golda	Shaffer	ru	2025-10-05 11:14:42.218291+00	2025-10-05 11:14:42.218291+00	f	t	f	0	0	\N	{"id": 6177341806, "is_bot": false, "username": "goldashaffer", "last_name": "Shaffer", "first_name": "Alex-Golda", "is_premium": true, "language_code": "ru"}	2025-10-05 11:14:42.218291+00
273	382947638	alekhin_aaa	עקיבא	\N	ru	2025-10-05 11:14:56.13466+00	2025-10-05 11:14:56.13466+00	f	t	f	0	0	\N	{"id": 382947638, "is_bot": false, "username": "alekhin_aaa", "first_name": "עקיבא", "is_premium": true, "language_code": "ru"}	2025-10-05 11:14:56.13466+00
274	434450668	lizzibreezy	Елизавета	Рейнлиб	ru	2025-10-05 11:16:54.129993+00	2025-10-05 11:16:54.129993+00	f	t	f	0	0	\N	{"id": 434450668, "is_bot": false, "username": "lizzibreezy", "last_name": "Рейнлиб", "first_name": "Елизавета", "is_premium": true, "language_code": "ru"}	2025-10-05 11:16:54.129993+00
275	690147786	WhqjYIEqI	Svitlana	Vladova	uk	2025-10-05 11:17:22.433138+00	2025-10-05 11:17:22.433138+00	f	f	f	0	0	\N	{"id": 690147786, "is_bot": false, "username": "WhqjYIEqI", "last_name": "Vladova", "first_name": "Svitlana", "language_code": "uk"}	2025-10-05 11:17:22.433138+00
276	369477807	dara_khen	Dara Khen	\N	ru	2025-10-05 11:19:43.986877+00	2025-10-05 11:19:43.986877+00	f	f	f	0	0	\N	{"id": 369477807, "is_bot": false, "username": "dara_khen", "first_name": "Dara Khen", "language_code": "ru"}	2025-10-05 11:19:43.986877+00
277	1207798300	adelinafain	Аделина	Файн	ru	2025-10-05 11:20:23.155177+00	2025-10-05 11:20:23.155177+00	f	f	f	0	0	\N	{"id": 1207798300, "is_bot": false, "username": "adelinafain", "last_name": "Файн", "first_name": "Аделина", "language_code": "ru"}	2025-10-05 11:20:23.155177+00
278	250329368	NataKonstantinova	Наталья	Константинова	ru	2025-10-05 11:30:57.022416+00	2025-10-05 11:30:57.022416+00	f	f	f	0	0	\N	{"id": 250329368, "is_bot": false, "username": "NataKonstantinova", "last_name": "Константинова", "first_name": "Наталья", "language_code": "ru"}	2025-10-05 11:30:57.022416+00
279	6352288632	Buoedhi720228man	Budiman 72	Alam	id	2025-10-05 11:31:52.604684+00	2025-10-05 11:31:52.604684+00	f	f	f	0	0	\N	{"id": 6352288632, "is_bot": false, "username": "Buoedhi720228man", "last_name": "Alam", "first_name": "Budiman 72", "language_code": "id"}	2025-10-05 11:31:52.604684+00
280	1013230906	OKKULTsycirity	OKKULTseycirity	\N	de	2025-10-05 11:41:34.917577+00	2025-10-05 11:41:34.917577+00	f	f	f	0	0	\N	{"id": 1013230906, "is_bot": false, "username": "OKKULTsycirity", "first_name": "OKKULTseycirity", "language_code": "de"}	2025-10-05 11:41:34.917577+00
282	553150878	celtic30	Игорь	\N	ru	2025-10-05 11:49:26.129775+00	2025-10-05 11:49:26.129775+00	f	f	f	0	0	\N	{"id": 553150878, "is_bot": false, "username": "celtic30", "first_name": "Игорь", "language_code": "ru"}	2025-10-05 11:49:26.129775+00
283	410073721	Marta_Tymoshchuk	Marta	\N	ru	2025-10-05 11:49:27.11683+00	2025-10-05 11:49:27.11683+00	f	f	f	0	0	\N	{"id": 410073721, "is_bot": false, "username": "Marta_Tymoshchuk", "first_name": "Marta", "language_code": "ru"}	2025-10-05 11:49:27.11683+00
284	1788541968	\N	Dorothy	Scanlan	en	2025-10-05 12:01:43.931342+00	2025-10-05 12:01:43.931342+00	f	f	f	0	0	\N	{"id": 1788541968, "is_bot": false, "last_name": "Scanlan", "first_name": "Dorothy", "language_code": "en"}	2025-10-05 12:01:43.931342+00
285	1113854615	KatyaShnurenco	Katea	Snurenco	ru	2025-10-05 12:08:01.727473+00	2025-10-05 12:08:01.727473+00	f	f	f	0	0	\N	{"id": 1113854615, "is_bot": false, "username": "KatyaShnurenco", "last_name": "Snurenco", "first_name": "Katea", "language_code": "ru"}	2025-10-05 12:08:01.727473+00
286	1339075345	Run_for_Quality	Jan	van den Bos	nl	2025-10-05 12:08:21.841812+00	2025-10-05 12:08:21.841812+00	f	f	f	0	0	\N	{"id": 1339075345, "is_bot": false, "username": "Run_for_Quality", "last_name": "van den Bos", "first_name": "Jan", "language_code": "nl"}	2025-10-05 12:08:21.841812+00
287	986976844	sophie_sup	Sophie	\N	ru	2025-10-05 12:13:19.769747+00	2025-10-05 12:13:19.769747+00	f	f	f	0	0	\N	{"id": 986976844, "is_bot": false, "username": "sophie_sup", "first_name": "Sophie", "language_code": "ru"}	2025-10-05 12:13:19.769747+00
288	845513733	hiramongoma	Hiram	Ongoma	en	2025-10-05 12:14:18.123228+00	2025-10-05 12:14:18.123228+00	f	f	f	0	0	\N	{"id": 845513733, "is_bot": false, "username": "hiramongoma", "last_name": "Ongoma", "first_name": "Hiram", "language_code": "en"}	2025-10-05 12:14:18.123228+00
289	1724436404	DN774	David	Nicol ️	en	2025-10-05 12:16:37.953165+00	2025-10-05 12:16:37.953165+00	f	f	f	0	0	\N	{"id": 1724436404, "is_bot": false, "username": "DN774", "last_name": "Nicol ️", "first_name": "David", "language_code": "en"}	2025-10-05 12:16:37.953165+00
290	6832191637	\N	Tim	Hathaway	en	2025-10-05 12:27:37.91941+00	2025-10-05 12:27:37.91941+00	f	f	f	0	0	\N	{"id": 6832191637, "is_bot": false, "last_name": "Hathaway", "first_name": "Tim", "language_code": "en"}	2025-10-05 12:27:37.91941+00
291	6089340024	ilajipsy	Ila	Jipsy	it	2025-10-05 12:28:08.072466+00	2025-10-05 12:28:08.072466+00	f	f	f	0	0	\N	{"id": 6089340024, "is_bot": false, "username": "ilajipsy", "last_name": "Jipsy", "first_name": "Ila", "language_code": "it"}	2025-10-05 12:28:08.072466+00
292	1828897567	Alhaju_Ahmed	أحمد	عبدالحميد	ar	2025-10-05 12:31:12.525712+00	2025-10-05 12:31:12.525712+00	f	f	f	0	0	\N	{"id": 1828897567, "is_bot": false, "username": "Alhaju_Ahmed", "last_name": "عبدالحميد", "first_name": "أحمد", "language_code": "ar"}	2025-10-05 12:31:12.525712+00
294	93075872	AnnaFirzon	Anna	\N	ru	2025-10-05 12:32:20.751241+00	2025-10-05 12:32:20.751241+00	f	t	f	0	0	\N	{"id": 93075872, "is_bot": false, "username": "AnnaFirzon", "first_name": "Anna", "is_premium": true, "language_code": "ru"}	2025-10-05 12:32:20.751241+00
295	945033143	\N	Veersingh	Korram	en	2025-10-05 12:32:41.037826+00	2025-10-05 12:32:41.037826+00	f	f	f	0	0	\N	{"id": 945033143, "is_bot": false, "last_name": "Korram", "first_name": "Veersingh", "language_code": "en"}	2025-10-05 12:32:41.037826+00
296	1707324289	gatgachweah	Gat-Gach-weah ll	\N	am	2025-10-05 12:42:43.924781+00	2025-10-05 12:42:43.924781+00	f	f	f	0	0	\N	{"id": 1707324289, "is_bot": false, "username": "gatgachweah", "first_name": "Gat-Gach-weah ll", "language_code": "am"}	2025-10-05 12:42:43.924781+00
297	466211409	YMyha	Yulia	Mykhaylova	uk	2025-10-05 13:05:13.015191+00	2025-10-05 13:05:13.015191+00	f	f	f	0	0	\N	{"id": 466211409, "is_bot": false, "username": "YMyha", "last_name": "Mykhaylova", "first_name": "Yulia", "language_code": "uk"}	2025-10-05 13:05:13.015191+00
298	7042614010	\N	Kandyce	Richards	en	2025-10-05 13:08:11.117214+00	2025-10-05 13:08:11.117214+00	f	f	f	0	0	\N	{"id": 7042614010, "is_bot": false, "last_name": "Richards", "first_name": "Kandyce", "language_code": "en"}	2025-10-05 13:08:11.117214+00
299	1702548913	\N	Joana	Kisewalter	de	2025-10-05 13:19:00.218201+00	2025-10-05 13:19:00.218201+00	f	f	f	0	0	\N	{"id": 1702548913, "is_bot": false, "last_name": "Kisewalter", "first_name": "Joana", "language_code": "de"}	2025-10-05 13:19:00.218201+00
300	826331526	czar087	Moshe	\N	en	2025-10-05 13:32:23.902454+00	2025-10-05 13:32:23.902454+00	f	f	f	0	0	\N	{"id": 826331526, "is_bot": false, "username": "czar087", "first_name": "Moshe", "language_code": "en"}	2025-10-05 13:32:23.902454+00
301	1440538120	\N	M.	\N	fa	2025-10-05 13:34:15.268298+00	2025-10-05 13:34:15.268298+00	f	f	f	0	0	\N	{"id": 1440538120, "is_bot": false, "first_name": "M.", "language_code": "fa"}	2025-10-05 13:34:15.268298+00
293	7395089217	\N	Carlos Ivan	\N	es	2025-10-05 12:31:21.135176+00	2025-10-24 09:58:28.072185+00	f	f	f	0	0	\N	{"id": 7395089217, "is_bot": false, "first_name": "Carlos Ivan", "language_code": "es"}	2025-10-24 09:58:28.072185+00
302	6969441671	\N	Alex	K	en	2025-10-05 13:45:25.154808+00	2025-10-05 13:45:25.154808+00	f	f	f	0	0	\N	{"id": 6969441671, "is_bot": false, "last_name": "K", "first_name": "Alex", "language_code": "en"}	2025-10-05 13:45:25.154808+00
303	1325123211	\N	Lena	Frenklakh	en	2025-10-05 13:45:34.402277+00	2025-10-05 13:45:34.402277+00	f	f	f	0	0	\N	{"id": 1325123211, "is_bot": false, "last_name": "Frenklakh", "first_name": "Lena", "language_code": "en"}	2025-10-05 13:45:34.402277+00
304	6671878888	buena1vibra	Susi	K	de	2025-10-05 13:47:46.947983+00	2025-10-05 13:47:46.947983+00	f	f	f	0	0	\N	{"id": 6671878888, "is_bot": false, "username": "buena1vibra", "last_name": "K", "first_name": "Susi", "language_code": "de"}	2025-10-05 13:47:46.947983+00
305	831101241	Lindy2016	Linda	\N	nl	2025-10-05 13:58:00.027399+00	2025-10-05 13:58:00.027399+00	f	f	f	0	0	\N	{"id": 831101241, "is_bot": false, "username": "Lindy2016", "first_name": "Linda", "language_code": "nl"}	2025-10-05 13:58:00.027399+00
306	6875364694	Akhilbeby	Σr.ΡεΛcε☮	\N	en	2025-10-05 13:59:08.71432+00	2025-10-05 13:59:08.71432+00	f	f	f	0	0	\N	{"id": 6875364694, "is_bot": false, "username": "Akhilbeby", "first_name": "Σr.ΡεΛcε☮", "language_code": "en"}	2025-10-05 13:59:08.71432+00
307	7559329247	Solomonshahvar	Solomon	Shahvar	fa	2025-10-05 13:59:27.338018+00	2025-10-05 13:59:27.338018+00	f	f	f	0	0	\N	{"id": 7559329247, "is_bot": false, "username": "Solomonshahvar", "last_name": "Shahvar", "first_name": "Solomon", "language_code": "fa"}	2025-10-05 13:59:27.338018+00
308	1661250723	Maral_Kairat2005	Марал	Кайрат	ru	2025-10-05 14:01:00.483426+00	2025-10-05 14:01:00.483426+00	f	f	f	0	0	\N	{"id": 1661250723, "is_bot": false, "username": "Maral_Kairat2005", "last_name": "Кайрат", "first_name": "Марал", "language_code": "ru"}	2025-10-05 14:01:00.483426+00
309	6760017958	\N	L.	Andrei	ro	2025-10-05 14:12:48.845893+00	2025-10-05 14:12:48.845893+00	f	f	f	0	0	\N	{"id": 6760017958, "is_bot": false, "last_name": "Andrei", "first_name": "L.", "language_code": "ro"}	2025-10-05 14:12:48.845893+00
310	7961366035	\N	גבריאל	הז	es	2025-10-05 14:26:00.209192+00	2025-10-05 14:26:00.209192+00	f	f	f	0	0	\N	{"id": 7961366035, "is_bot": false, "last_name": "הז", "first_name": "גבריאל", "language_code": "es"}	2025-10-05 14:26:00.209192+00
311	8270776040	\N	IBM	\N	en	2025-10-05 14:29:40.643734+00	2025-10-05 14:29:40.643734+00	f	f	f	0	0	\N	{"id": 8270776040, "is_bot": false, "first_name": "IBM", "language_code": "en"}	2025-10-05 14:29:40.643734+00
312	1833477096	\N	Madame	Tussauds	en	2025-10-05 14:34:33.542853+00	2025-10-05 14:34:33.542853+00	f	f	f	0	0	\N	{"id": 1833477096, "is_bot": false, "last_name": "Tussauds", "first_name": "Madame", "language_code": "en"}	2025-10-05 14:34:33.542853+00
313	6129181419	\N	Nancy	Nancy	en	2025-10-05 14:38:59.425261+00	2025-10-05 14:38:59.425261+00	f	f	f	0	0	\N	{"id": 6129181419, "is_bot": false, "last_name": "Nancy", "first_name": "Nancy", "language_code": "en"}	2025-10-05 14:38:59.425261+00
314	7526451334	\N	Marco	\N	fr	2025-10-05 14:58:06.424843+00	2025-10-05 14:58:06.424843+00	f	f	f	0	0	\N	{"id": 7526451334, "is_bot": false, "first_name": "Marco", "language_code": "fr"}	2025-10-05 14:58:06.424843+00
315	1590367749	\N	Janeal	Scott	en	2025-10-05 15:03:14.961342+00	2025-10-05 15:03:14.961342+00	f	f	f	0	0	\N	{"id": 1590367749, "is_bot": false, "last_name": "Scott", "first_name": "Janeal", "language_code": "en"}	2025-10-05 15:03:14.961342+00
317	718415371	\N	Лена	Мурашкина (Норец)	ru	2025-10-05 15:15:35.195+00	2025-10-05 15:15:35.195+00	f	f	f	0	0	\N	{"id": 718415371, "is_bot": false, "last_name": "Мурашкина (Норец)", "first_name": "Лена", "language_code": "ru"}	2025-10-05 15:15:35.195+00
318	8374751306	\N	.	W	en	2025-10-05 15:19:03.95733+00	2025-10-05 15:19:03.95733+00	f	f	f	0	0	\N	{"id": 8374751306, "is_bot": false, "last_name": "W", "first_name": ".", "language_code": "en"}	2025-10-05 15:19:03.95733+00
319	8029374130	Pastorjoel360	Joel	Ostean ☦️	en	2025-10-05 15:29:23.807529+00	2025-10-05 15:29:23.807529+00	f	f	f	0	0	\N	{"id": 8029374130, "is_bot": false, "username": "Pastorjoel360", "last_name": "Ostean ☦️", "first_name": "Joel", "language_code": "en"}	2025-10-05 15:29:23.807529+00
320	6593187682	\N	Hurst	\N	de	2025-10-05 15:30:20.578844+00	2025-10-05 15:30:20.578844+00	f	f	f	0	0	\N	{"id": 6593187682, "is_bot": false, "first_name": "Hurst", "language_code": "de"}	2025-10-05 15:30:20.578844+00
321	5915843326	\N	Provet B	Sitanggang	id	2025-10-05 15:34:14.919188+00	2025-10-05 15:34:14.919188+00	f	f	f	0	0	\N	{"id": 5915843326, "is_bot": false, "last_name": "Sitanggang", "first_name": "Provet B", "language_code": "id"}	2025-10-05 15:34:14.919188+00
322	484829882	\N	lisa	luganska	uk	2025-10-05 15:35:23.319975+00	2025-10-05 15:35:23.319975+00	f	t	f	0	0	\N	{"id": 484829882, "is_bot": false, "last_name": "luganska", "first_name": "lisa", "is_premium": true, "language_code": "uk"}	2025-10-05 15:35:23.319975+00
323	5711428833	Masoodkirmai	Masood	Kirmani	en	2025-10-05 15:38:18.396984+00	2025-10-05 15:38:18.396984+00	f	f	f	0	0	\N	{"id": 5711428833, "is_bot": false, "username": "Masoodkirmai", "last_name": "Kirmani", "first_name": "Masood", "language_code": "en"}	2025-10-05 15:38:18.396984+00
324	6192704594	ezifeanyi	Okoroafor	\N	en	2025-10-05 15:57:48.99134+00	2025-10-05 15:57:48.99134+00	f	f	f	0	0	\N	{"id": 6192704594, "is_bot": false, "username": "ezifeanyi", "first_name": "Okoroafor", "language_code": "en"}	2025-10-05 15:57:48.99134+00
325	2085431714	\N	Clark	\N	en	2025-10-05 16:05:35.479388+00	2025-10-05 16:05:35.479388+00	f	f	f	0	0	\N	{"id": 2085431714, "is_bot": false, "first_name": "Clark", "language_code": "en"}	2025-10-05 16:05:35.479388+00
326	1646933326	\N	Sergej	\N	de	2025-10-05 16:08:20.719956+00	2025-10-05 16:08:20.719956+00	f	f	f	0	0	\N	{"id": 1646933326, "is_bot": false, "first_name": "Sergej", "language_code": "de"}	2025-10-05 16:08:20.719956+00
327	6743277176	\N	Chuka	Chu	en	2025-10-05 16:09:32.334195+00	2025-10-05 16:09:32.334195+00	f	f	f	0	0	\N	{"id": 6743277176, "is_bot": false, "last_name": "Chu", "first_name": "Chuka", "language_code": "en"}	2025-10-05 16:09:32.334195+00
328	7438908967	HydraCross	Alma 🇮🇱	\N	es	2025-10-05 16:20:23.40108+00	2025-10-05 16:20:23.40108+00	f	f	f	0	0	\N	{"id": 7438908967, "is_bot": false, "username": "HydraCross", "first_name": "Alma 🇮🇱", "language_code": "es"}	2025-10-05 16:20:23.40108+00
329	5086119787	\N	Juan	Corrales	en	2025-10-05 16:22:06.196741+00	2025-10-05 16:22:06.196741+00	f	f	f	0	0	\N	{"id": 5086119787, "is_bot": false, "last_name": "Corrales", "first_name": "Juan", "language_code": "en"}	2025-10-05 16:22:06.196741+00
330	881214624	ZdBuchling	ZD	\N	en	2025-10-05 16:33:45.31819+00	2025-10-05 16:33:45.31819+00	f	f	f	0	0	\N	{"id": 881214624, "is_bot": false, "username": "ZdBuchling", "first_name": "ZD", "language_code": "en"}	2025-10-05 16:33:45.31819+00
331	5509697048	curie67	🧠🔐🔧🔨	\N	en	2025-10-05 16:52:25.419573+00	2025-10-05 16:52:25.419573+00	f	f	f	0	0	\N	{"id": 5509697048, "is_bot": false, "username": "curie67", "first_name": "🧠🔐🔧🔨", "language_code": "en"}	2025-10-05 16:52:25.419573+00
332	943719606	\N	Kate	Lazniuk	en	2025-10-05 17:14:30.930488+00	2025-10-05 17:14:30.930488+00	f	f	f	0	0	\N	{"id": 943719606, "is_bot": false, "last_name": "Lazniuk", "first_name": "Kate", "language_code": "en"}	2025-10-05 17:14:30.930488+00
333	138552259	Max_Musterspieli	Max	\N	de	2025-10-05 17:22:29.115803+00	2025-10-05 17:22:29.115803+00	f	f	f	0	0	\N	{"id": 138552259, "is_bot": false, "username": "Max_Musterspieli", "first_name": "Max", "language_code": "de"}	2025-10-05 17:22:29.115803+00
334	1302088591	\N	Mary	E.	en	2025-10-05 17:23:45.274596+00	2025-10-05 17:23:45.274596+00	f	f	f	0	0	\N	{"id": 1302088591, "is_bot": false, "last_name": "E.", "first_name": "Mary", "language_code": "en"}	2025-10-05 17:23:45.274596+00
335	5487812483	FOSA431	FOSA	\N	en	2025-10-05 17:35:37.624633+00	2025-10-05 17:35:37.624633+00	f	f	f	0	0	\N	{"id": 5487812483, "is_bot": false, "username": "FOSA431", "first_name": "FOSA", "language_code": "en"}	2025-10-05 17:35:37.624633+00
336	8212448201	\N	Mike	L	nl	2025-10-05 17:42:45.567334+00	2025-10-05 17:42:45.567334+00	f	f	f	0	0	\N	{"id": 8212448201, "is_bot": false, "last_name": "L", "first_name": "Mike", "language_code": "nl"}	2025-10-05 17:42:45.567334+00
337	7108584268	\N	Netali	Aronoff	en	2025-10-05 17:48:45.626675+00	2025-10-05 17:48:45.626675+00	f	f	f	0	0	\N	{"id": 7108584268, "is_bot": false, "last_name": "Aronoff", "first_name": "Netali", "language_code": "en"}	2025-10-05 17:48:45.626675+00
338	6445649937	\N	Bbb	Bb	en	2025-10-05 17:51:23.129588+00	2025-10-05 17:51:23.129588+00	f	f	f	0	0	\N	{"id": 6445649937, "is_bot": false, "last_name": "Bb", "first_name": "Bbb", "language_code": "en"}	2025-10-05 17:51:23.129588+00
339	1368962964	radbi72	David Aharon Curtis	רדב״י	en	2025-10-05 18:01:44.418131+00	2025-10-05 18:01:44.418131+00	f	t	f	0	0	\N	{"id": 1368962964, "is_bot": false, "username": "radbi72", "last_name": "רדב״י", "first_name": "David Aharon Curtis", "is_premium": true, "language_code": "en"}	2025-10-05 18:01:44.418131+00
340	879358401	KIY1SVT	Alvise	Codiferro	de	2025-10-05 18:06:42.945048+00	2025-10-05 18:06:42.945048+00	f	f	f	0	0	\N	{"id": 879358401, "is_bot": false, "username": "KIY1SVT", "last_name": "Codiferro", "first_name": "Alvise", "language_code": "de"}	2025-10-05 18:06:42.945048+00
341	5854312977	\N	Troy	Zeiner	en	2025-10-05 18:13:26.739582+00	2025-10-05 18:13:26.739582+00	f	f	f	0	0	\N	{"id": 5854312977, "is_bot": false, "last_name": "Zeiner", "first_name": "Troy", "language_code": "en"}	2025-10-05 18:13:26.739582+00
342	8171716646	\N	Rebecca	\N	en	2025-10-05 18:28:30.927862+00	2025-10-05 18:28:30.927862+00	f	f	f	0	0	\N	{"id": 8171716646, "is_bot": false, "first_name": "Rebecca", "language_code": "en"}	2025-10-05 18:28:30.927862+00
343	1515444056	\N	István	\N	de	2025-10-05 18:30:52.429484+00	2025-10-05 18:30:52.429484+00	f	f	f	0	0	\N	{"id": 1515444056, "is_bot": false, "first_name": "István", "language_code": "de"}	2025-10-05 18:30:52.429484+00
344	5418614468	\N	Dr. Eliyahu (Eli)	Lizorkin	ru	2025-10-05 18:53:38.295592+00	2025-10-05 18:53:38.295592+00	f	f	f	0	0	\N	{"id": 5418614468, "is_bot": false, "last_name": "Lizorkin", "first_name": "Dr. Eliyahu (Eli)", "language_code": "ru"}	2025-10-05 18:53:38.295592+00
345	6187077618	Arykittymeow	Arykitty	\N	es	2025-10-05 19:09:14.167433+00	2025-10-05 19:09:14.167433+00	f	t	f	0	0	\N	{"id": 6187077618, "is_bot": false, "username": "Arykittymeow", "first_name": "Arykitty", "is_premium": true, "language_code": "es"}	2025-10-05 19:09:14.167433+00
346	832871142	Andy56788	Andrés	Ruiz	fr	2025-10-05 19:25:08.947314+00	2025-10-05 19:25:08.947314+00	f	f	f	0	0	\N	{"id": 832871142, "is_bot": false, "username": "Andy56788", "last_name": "Ruiz", "first_name": "Andrés", "language_code": "fr"}	2025-10-05 19:25:08.947314+00
347	1835925483	Zv_56325	Username	\N	en	2025-10-05 19:27:49.523465+00	2025-10-05 19:27:49.523465+00	f	f	f	0	0	\N	{"id": 1835925483, "is_bot": false, "username": "Zv_56325", "first_name": "Username", "language_code": "en"}	2025-10-05 19:27:49.523465+00
348	172435367	njegos777	Njegoš	\N	en	2025-10-05 19:33:20.67566+00	2025-10-05 19:33:20.67566+00	f	f	f	0	0	\N	{"id": 172435367, "is_bot": false, "username": "njegos777", "first_name": "Njegoš", "language_code": "en"}	2025-10-05 19:33:20.67566+00
349	1977379500	United_Status_of_Asia	Christian	Church24	en	2025-10-05 19:55:37.43336+00	2025-10-05 19:55:37.43336+00	f	f	f	0	0	\N	{"id": 1977379500, "is_bot": false, "username": "United_Status_of_Asia", "last_name": "Church24", "first_name": "Christian", "language_code": "en"}	2025-10-05 19:55:37.43336+00
350	7703588364	\N	G	Jj	en	2025-10-05 19:59:24.872786+00	2025-10-05 19:59:24.872786+00	f	f	f	0	0	\N	{"id": 7703588364, "is_bot": false, "last_name": "Jj", "first_name": "G", "language_code": "en"}	2025-10-05 19:59:24.872786+00
351	820329048	\N	Olena	Fedoriak	uk	2025-10-05 20:18:53.181452+00	2025-10-05 20:18:53.181452+00	f	f	f	0	0	\N	{"id": 820329048, "is_bot": false, "last_name": "Fedoriak", "first_name": "Olena", "language_code": "uk"}	2025-10-05 20:18:53.181452+00
352	6264755497	\N	Gabriel	\N	en	2025-10-05 20:44:55.522531+00	2025-10-05 20:44:55.522531+00	f	t	f	0	0	\N	{"id": 6264755497, "is_bot": false, "first_name": "Gabriel", "is_premium": true, "language_code": "en"}	2025-10-05 20:44:55.522531+00
353	986445508	Emissary_Emmanuel	Emmanuel	Uzoma-Ikembasi	en	2025-10-05 21:01:26.525177+00	2025-10-05 21:01:26.525177+00	f	f	f	0	0	\N	{"id": 986445508, "is_bot": false, "username": "Emissary_Emmanuel", "last_name": "Uzoma-Ikembasi", "first_name": "Emmanuel", "language_code": "en"}	2025-10-05 21:01:26.525177+00
354	8195637848	\N	Ruby	Richmond	en	2025-10-05 23:42:31.263488+00	2025-10-05 23:42:31.263488+00	f	t	f	0	0	\N	{"id": 8195637848, "is_bot": false, "last_name": "Richmond", "first_name": "Ruby", "is_premium": true, "language_code": "en"}	2025-10-05 23:42:31.263488+00
355	8100817449	\N	Yaneth	Angel	en	2025-10-05 23:58:36.518874+00	2025-10-05 23:58:36.518874+00	f	f	f	0	0	\N	{"id": 8100817449, "is_bot": false, "last_name": "Angel", "first_name": "Yaneth", "language_code": "en"}	2025-10-05 23:58:36.518874+00
356	1503910387	Torsten_Nenzen	Torsten	Nenzen	en	2025-10-06 00:07:31.144829+00	2025-10-06 00:07:31.144829+00	f	f	f	0	0	\N	{"id": 1503910387, "is_bot": false, "username": "Torsten_Nenzen", "last_name": "Nenzen", "first_name": "Torsten", "language_code": "en"}	2025-10-06 00:07:31.144829+00
357	516855627	\N	Sharon	\N	he	2025-10-06 00:50:47.01828+00	2025-10-06 00:50:47.01828+00	f	f	f	0	0	\N	{"id": 516855627, "is_bot": false, "first_name": "Sharon", "language_code": "he"}	2025-10-06 00:50:47.01828+00
358	1488677371	SomaPneumaPaideia	Ina	Draper	en	2025-10-06 01:16:31.032976+00	2025-10-06 01:16:31.032976+00	f	f	f	0	0	\N	{"id": 1488677371, "is_bot": false, "username": "SomaPneumaPaideia", "last_name": "Draper", "first_name": "Ina", "language_code": "en"}	2025-10-06 01:16:31.032976+00
359	8424384669	asarifulsheikh	Md	Ariful	en	2025-10-06 01:22:03.731999+00	2025-10-06 01:22:03.731999+00	f	f	f	0	0	\N	{"id": 8424384669, "is_bot": false, "username": "asarifulsheikh", "last_name": "Ariful", "first_name": "Md", "language_code": "en"}	2025-10-06 01:22:03.731999+00
360	5628128008	\N	Jenny	Munak	en	2025-10-06 01:58:19.537696+00	2025-10-06 01:58:19.537696+00	f	f	f	0	0	\N	{"id": 5628128008, "is_bot": false, "last_name": "Munak", "first_name": "Jenny", "language_code": "en"}	2025-10-06 01:58:19.537696+00
361	921009561	SW100BS	SW100BS	\N	en	2025-10-06 02:05:18.233014+00	2025-10-06 02:05:18.233014+00	f	f	f	0	0	\N	{"id": 921009561, "is_bot": false, "username": "SW100BS", "first_name": "SW100BS", "language_code": "en"}	2025-10-06 02:05:18.233014+00
362	5532249782	ZeppelinAngel	VAOB	\N	en	2025-10-06 02:29:19.741805+00	2025-10-06 02:31:07.11731+00	f	f	f	0	0	\N	{"id": 5532249782, "is_bot": false, "username": "ZeppelinAngel", "first_name": "VAOB", "language_code": "en"}	2025-10-06 02:31:07.11731+00
364	1258400779	AbdullahWeshah	Abdullah	\N	en	2025-10-06 03:24:15.067852+00	2025-10-06 03:24:15.067852+00	f	f	f	0	0	\N	{"id": 1258400779, "is_bot": false, "username": "AbdullahWeshah", "first_name": "Abdullah", "language_code": "en"}	2025-10-06 03:24:15.067852+00
365	1469651555	Zalman3	Dorin	\N	it	2025-10-06 05:31:27.919305+00	2025-10-06 05:31:27.919305+00	f	f	f	0	0	\N	{"id": 1469651555, "is_bot": false, "username": "Zalman3", "first_name": "Dorin", "language_code": "it"}	2025-10-06 05:31:27.919305+00
366	1556184415	\N	schalk	van den bergh	en	2025-10-06 05:38:05.223767+00	2025-10-06 05:38:05.223767+00	f	f	f	0	0	\N	{"id": 1556184415, "is_bot": false, "last_name": "van den bergh", "first_name": "schalk", "language_code": "en"}	2025-10-06 05:38:05.223767+00
367	1440186698	Charpiovezan	Charlanne Kelly	Piovezan	pt-br	2025-10-06 06:21:53.183009+00	2025-10-06 06:21:53.183009+00	f	f	f	0	0	\N	{"id": 1440186698, "is_bot": false, "username": "Charpiovezan", "last_name": "Piovezan", "first_name": "Charlanne Kelly", "language_code": "pt-br"}	2025-10-06 06:21:53.183009+00
368	1115752771	Dmitriy03L	Dmitriy	\N	ru	2025-10-06 06:44:24.487331+00	2025-10-06 06:44:24.487331+00	f	f	f	0	0	\N	{"id": 1115752771, "is_bot": false, "username": "Dmitriy03L", "first_name": "Dmitriy", "language_code": "ru"}	2025-10-06 06:44:24.487331+00
369	802864321	CEO5277	Shimon	\N	ru	2025-10-06 06:58:08.363384+00	2025-10-06 06:58:08.363384+00	f	f	f	0	0	\N	{"id": 802864321, "is_bot": false, "username": "CEO5277", "first_name": "Shimon", "language_code": "ru"}	2025-10-06 06:58:08.363384+00
370	1600395688	\N	Judith	Kiss	en	2025-10-06 07:49:47.815779+00	2025-10-06 07:49:47.815779+00	f	f	f	0	0	\N	{"id": 1600395688, "is_bot": false, "last_name": "Kiss", "first_name": "Judith", "language_code": "en"}	2025-10-06 07:49:47.815779+00
371	1092144026	Svetla8	Svitlana	\N	uk	2025-10-06 08:11:14.049461+00	2025-10-06 08:11:14.049461+00	f	t	f	0	0	\N	{"id": 1092144026, "is_bot": false, "username": "Svetla8", "first_name": "Svitlana", "is_premium": true, "language_code": "uk"}	2025-10-06 08:11:14.049461+00
372	1622457981	\N	John	Abraham	en	2025-10-06 09:11:47.105746+00	2025-10-06 09:11:47.105746+00	f	f	f	0	0	\N	{"id": 1622457981, "is_bot": false, "last_name": "Abraham", "first_name": "John", "language_code": "en"}	2025-10-06 09:11:47.105746+00
281	6340805709	\N	Ivan	Pagan	en	2025-10-05 11:48:16.219523+00	2025-10-06 09:15:10.741901+00	f	f	f	0	0	\N	{"id": 6340805709, "is_bot": false, "last_name": "Pagan", "first_name": "Ivan", "language_code": "en"}	2025-10-06 09:15:10.741901+00
374	732408481	Caritoxp	KdyBrito	\N	es	2025-10-06 09:30:37.760597+00	2025-10-06 09:30:37.760597+00	f	f	f	0	0	\N	{"id": 732408481, "is_bot": false, "username": "Caritoxp", "first_name": "KdyBrito", "language_code": "es"}	2025-10-06 09:30:37.760597+00
375	7523695427	dryteuiop	Xnzayrpcad	Jzjfongjiw	en	2025-10-06 10:15:50.575065+00	2025-10-06 10:15:50.575065+00	f	f	f	0	0	\N	{"id": 7523695427, "is_bot": false, "username": "dryteuiop", "last_name": "Jzjfongjiw", "first_name": "Xnzayrpcad", "language_code": "en"}	2025-10-06 10:15:50.575065+00
376	6649838701	\N	Elvia (Simcha)	Flórez	en	2025-10-06 10:27:03.394334+00	2025-10-06 10:27:03.394334+00	f	f	f	0	0	\N	{"id": 6649838701, "is_bot": false, "last_name": "Flórez", "first_name": "Elvia (Simcha)", "language_code": "en"}	2025-10-06 10:27:03.394334+00
377	1391227690	mishiev_i	ימואל	מישייב	ru	2025-10-06 12:03:46.459602+00	2025-10-06 12:03:46.459602+00	f	f	f	0	0	\N	{"id": 1391227690, "is_bot": false, "username": "mishiev_i", "last_name": "מישייב", "first_name": "ימואל", "language_code": "ru"}	2025-10-06 12:03:46.459602+00
378	75594115	mex_online	Михаил	\N	ru	2025-10-06 16:06:37.119462+00	2025-10-06 16:06:37.119462+00	f	t	f	0	0	\N	{"id": 75594115, "is_bot": false, "username": "mex_online", "first_name": "Михаил", "is_premium": true, "language_code": "ru"}	2025-10-06 16:06:37.119462+00
379	1613640391	pkkr1971	Pran	Kumar	en	2025-10-07 00:57:30.372376+00	2025-10-07 00:57:30.372376+00	f	f	f	0	0	\N	{"id": 1613640391, "is_bot": false, "username": "pkkr1971", "last_name": "Kumar", "first_name": "Pran", "language_code": "en"}	2025-10-07 00:57:30.372376+00
380	720362336	yosel1603	Yosel	Rodriguez Pérez	pt-br	2025-10-07 01:18:45.151704+00	2025-10-07 01:18:45.151704+00	f	f	f	0	0	\N	{"id": 720362336, "is_bot": false, "username": "yosel1603", "last_name": "Rodriguez Pérez", "first_name": "Yosel", "language_code": "pt-br"}	2025-10-07 01:18:45.151704+00
381	7471766035	\N	Carlo Jose	Delmonte	en	2025-10-07 02:28:36.236509+00	2025-10-07 02:28:36.236509+00	f	f	f	0	0	\N	{"id": 7471766035, "is_bot": false, "last_name": "Delmonte", "first_name": "Carlo Jose", "language_code": "en"}	2025-10-07 02:28:36.236509+00
382	6692316101	guruji_og	ㅤ𝗚𝗨𝗥𝗨𝗝𝗜ㅤ	\N	en	2025-10-08 20:28:58.972932+00	2025-10-08 20:28:58.972932+00	f	t	f	0	0	\N	{"id": 6692316101, "is_bot": false, "username": "guruji_og", "first_name": "ㅤ𝗚𝗨𝗥𝗨𝗝𝗜ㅤ", "is_premium": true, "language_code": "en"}	2025-10-08 20:28:58.972932+00
383	1064962808	marylidze	Maríe	\N	en	2025-10-08 21:22:33.09472+00	2025-10-08 21:22:33.09472+00	f	f	f	0	0	\N	{"id": 1064962808, "is_bot": false, "username": "marylidze", "first_name": "Maríe", "language_code": "en"}	2025-10-08 21:22:33.09472+00
384	6818757024	deniasma	Denias	\N	en	2025-10-09 01:34:03.205498+00	2025-10-09 01:34:03.205498+00	f	t	f	0	0	\N	{"id": 6818757024, "is_bot": false, "username": "deniasma", "first_name": "Denias", "is_premium": true, "language_code": "en"}	2025-10-09 01:34:03.205498+00
385	6181371007	\N	Angela Maria	Gaviria Berrío	es	2025-10-09 05:08:22.013974+00	2025-10-09 05:08:22.013974+00	f	f	f	0	0	\N	{"id": 6181371007, "is_bot": false, "last_name": "Gaviria Berrío", "first_name": "Angela Maria", "language_code": "es"}	2025-10-09 05:08:22.013974+00
386	8079344188	\N	Marjorie	\N	es	2025-10-11 00:33:33.583658+00	2025-10-11 00:33:33.583658+00	f	f	f	0	0	\N	{"id": 8079344188, "is_bot": false, "first_name": "Marjorie", "language_code": "es"}	2025-10-11 00:33:33.583658+00
387	423887044	Kuzina_pmu	Katerina	Kuzina	ru	2025-10-11 05:39:31.174655+00	2025-10-11 05:39:31.174655+00	f	t	f	0	0	\N	{"id": 423887044, "is_bot": false, "username": "Kuzina_pmu", "last_name": "Kuzina", "first_name": "Katerina", "is_premium": true, "language_code": "ru"}	2025-10-11 05:39:31.174655+00
388	242970791	zhukovamashera	Маша	Жукова	ru	2025-10-11 12:25:14.859571+00	2025-10-11 12:25:14.859571+00	f	t	f	0	0	\N	{"id": 242970791, "is_bot": false, "username": "zhukovamashera", "last_name": "Жукова", "first_name": "Маша", "is_premium": true, "language_code": "ru"}	2025-10-11 12:25:14.859571+00
389	7625442224	\N	Hamzaa	Abdulkariim	en	2025-10-11 15:25:30.9574+00	2025-10-11 15:25:30.9574+00	f	f	f	0	0	\N	{"id": 7625442224, "is_bot": false, "last_name": "Abdulkariim", "first_name": "Hamzaa", "language_code": "en"}	2025-10-11 15:25:30.9574+00
390	8027268302	\N	Gary	Dugger	en	2025-10-12 04:44:46.651448+00	2025-10-12 04:44:46.651448+00	f	f	f	0	0	\N	{"id": 8027268302, "is_bot": false, "last_name": "Dugger", "first_name": "Gary", "language_code": "en"}	2025-10-12 04:44:46.651448+00
391	7547433819	Brandon_Sklenar1a	Brandon	Sklenar	en	2025-10-12 21:36:58.20466+00	2025-10-12 21:36:58.20466+00	f	f	f	0	0	\N	{"id": 7547433819, "is_bot": false, "username": "Brandon_Sklenar1a", "last_name": "Sklenar", "first_name": "Brandon", "language_code": "en"}	2025-10-12 21:36:58.20466+00
392	7896537249	BIZGROWFAIZ	MUHAMMAD FAIZ ALAM	SAYYED	en	2025-10-12 23:36:28.132587+00	2025-10-12 23:36:28.132587+00	f	f	f	0	0	\N	{"id": 7896537249, "is_bot": false, "username": "BIZGROWFAIZ", "last_name": "SAYYED", "first_name": "MUHAMMAD FAIZ ALAM", "language_code": "en"}	2025-10-12 23:36:28.132587+00
396	8215050105	\N	żyd	\N	pl	2025-10-13 13:44:27.871015+00	2025-10-13 13:44:27.871015+00	f	f	f	0	0	\N	{"id": 8215050105, "is_bot": false, "first_name": "żyd", "language_code": "pl"}	2025-10-13 13:44:27.871015+00
393	5936946943	\N	Ksenia	\N	ru	2025-10-13 10:39:38.926883+00	2025-10-13 17:54:34.502607+00	f	f	f	0	0	\N	{"id": 5936946943, "is_bot": false, "first_name": "Ksenia", "language_code": "ru"}	2025-10-13 17:54:34.502607+00
398	5003765976	Nitesh12234	San's-merci	\N	en	2025-10-13 18:25:11.876192+00	2025-10-13 18:25:11.876192+00	f	f	f	0	0	\N	{"id": 5003765976, "is_bot": false, "username": "Nitesh12234", "first_name": "San's-merci", "language_code": "en"}	2025-10-13 18:25:11.876192+00
400	7564701358	\N	Md Riyad	Islam	en	2025-10-14 01:17:50.16826+00	2025-10-14 01:17:50.16826+00	f	f	f	0	0	\N	{"id": 7564701358, "is_bot": false, "last_name": "Islam", "first_name": "Md Riyad", "language_code": "en"}	2025-10-14 01:17:50.16826+00
401	583821364	\N	Elisa	Prado	pt-br	2025-10-14 03:50:03.852569+00	2025-10-14 03:50:03.852569+00	f	f	f	0	0	\N	{"id": 583821364, "is_bot": false, "last_name": "Prado", "first_name": "Elisa", "language_code": "pt-br"}	2025-10-14 03:50:03.852569+00
402	288330215	markzhukovsky	Mark	Zhukovsky	ru	2025-10-14 12:18:49.019636+00	2025-10-14 12:18:49.019636+00	f	f	f	0	0	\N	{"id": 288330215, "is_bot": false, "username": "markzhukovsky", "last_name": "Zhukovsky", "first_name": "Mark", "language_code": "ru"}	2025-10-14 12:18:49.019636+00
403	515460421	Silverique	📿 Anastasia	\N	ru	2025-10-14 13:38:28.475302+00	2025-10-14 13:38:28.475302+00	f	t	f	0	0	\N	{"id": 515460421, "is_bot": false, "username": "Silverique", "first_name": "📿 Anastasia", "is_premium": true, "language_code": "ru"}	2025-10-14 13:38:28.475302+00
404	1172693035	wj137	.	\N	en	2025-10-14 18:12:20.744394+00	2025-10-14 18:12:20.744394+00	f	f	f	0	0	\N	{"id": 1172693035, "is_bot": false, "username": "wj137", "first_name": ".", "language_code": "en"}	2025-10-14 18:12:20.744394+00
405	5145179679	NatyTeteia	Natalia	Maria	pt-br	2025-10-14 22:21:15.489147+00	2025-10-14 22:21:15.489147+00	f	f	f	0	0	\N	{"id": 5145179679, "is_bot": false, "username": "NatyTeteia", "last_name": "Maria", "first_name": "Natalia", "language_code": "pt-br"}	2025-10-14 22:21:15.489147+00
406	6831909579	KnizhnikiFoundation	Shmulik	Sahmanov	ru	2025-10-15 15:07:37.719712+00	2025-10-15 15:07:37.719712+00	f	f	f	0	0	\N	{"id": 6831909579, "is_bot": false, "username": "KnizhnikiFoundation", "last_name": "Sahmanov", "first_name": "Shmulik", "language_code": "ru"}	2025-10-15 15:07:37.719712+00
407	888542869	\N	🎗	\N	en	2025-10-15 22:47:15.03529+00	2025-10-15 22:47:15.03529+00	f	f	f	0	0	\N	{"id": 888542869, "is_bot": false, "first_name": "🎗", "language_code": "en"}	2025-10-15 22:47:15.03529+00
408	1906451465	ADEMBNY	Adem	Developer	ar	2025-10-16 01:42:36.546201+00	2025-10-16 01:42:36.546201+00	f	t	f	0	0	\N	{"id": 1906451465, "is_bot": false, "username": "ADEMBNY", "last_name": "Developer", "first_name": "Adem", "is_premium": true, "language_code": "ar"}	2025-10-16 01:42:36.546201+00
409	5996231412	\N	FX	\N	en	2025-10-16 11:33:03.676126+00	2025-10-16 11:33:03.676126+00	f	f	f	0	0	\N	{"id": 5996231412, "is_bot": false, "first_name": "FX", "language_code": "en"}	2025-10-16 11:33:03.676126+00
410	458203371	gshakhabutinov	Gadji	Shahabutinov	ru	2025-10-17 10:00:58.269097+00	2025-10-17 10:00:58.269097+00	f	f	f	0	0	\N	{"id": 458203371, "is_bot": false, "username": "gshakhabutinov", "last_name": "Shahabutinov", "first_name": "Gadji", "language_code": "ru"}	2025-10-17 10:00:58.269097+00
411	990827081	\N	Вагрант	Кахане хай!	de	2025-10-17 19:22:09.35518+00	2025-10-17 19:22:09.35518+00	f	f	f	0	0	\N	{"id": 990827081, "is_bot": false, "last_name": "Кахане хай!", "first_name": "Вагрант", "language_code": "de"}	2025-10-17 19:22:09.35518+00
412	1663951093	PaulaAdriana	Paula	Adriana	es	2025-10-18 07:48:49.81926+00	2025-10-18 07:48:49.81926+00	f	f	f	0	0	\N	{"id": 1663951093, "is_bot": false, "username": "PaulaAdriana", "last_name": "Adriana", "first_name": "Paula", "language_code": "es"}	2025-10-18 07:48:49.81926+00
413	430764367	vforin	в	\N	en	2025-10-18 17:51:53.091598+00	2025-10-18 17:51:53.091598+00	f	f	f	0	0	\N	{"id": 430764367, "is_bot": false, "username": "vforin", "first_name": "в", "language_code": "en"}	2025-10-18 17:51:53.091598+00
414	8263108289	lilidipyay	lilidip	\N	en	2025-10-18 17:58:44.794255+00	2025-10-18 17:58:44.794255+00	f	f	f	0	0	\N	{"id": 8263108289, "is_bot": false, "username": "lilidipyay", "first_name": "lilidip", "language_code": "en"}	2025-10-18 17:58:44.794255+00
415	368495959	danprov	Provalov	Daniel	ru	2025-10-18 20:35:38.215343+00	2025-10-18 20:35:38.215343+00	f	f	f	0	0	\N	{"id": 368495959, "is_bot": false, "username": "danprov", "last_name": "Daniel", "first_name": "Provalov", "language_code": "ru"}	2025-10-18 20:35:38.215343+00
416	589854563	livinabrk	Snezh	Auors	ru	2025-10-18 20:36:10.710241+00	2025-10-18 20:36:10.710241+00	f	f	f	0	0	\N	{"id": 589854563, "is_bot": false, "username": "livinabrk", "last_name": "Auors", "first_name": "Snezh", "language_code": "ru"}	2025-10-18 20:36:10.710241+00
417	958199554	IlyaKhodarevsky	Илья	Ходаревский	ru	2025-10-18 20:41:57.420693+00	2025-10-18 20:41:57.420693+00	f	t	f	0	0	\N	{"id": 958199554, "is_bot": false, "username": "IlyaKhodarevsky", "last_name": "Ходаревский", "first_name": "Илья", "is_premium": true, "language_code": "ru"}	2025-10-18 20:41:57.420693+00
418	649042229	lizagri798	Liza	\N	ru	2025-10-18 21:02:33.391621+00	2025-10-18 21:02:33.391621+00	f	t	f	0	0	\N	{"id": 649042229, "is_bot": false, "username": "lizagri798", "first_name": "Liza", "is_premium": true, "language_code": "ru"}	2025-10-18 21:02:33.391621+00
419	275735842	martino009	martins	\N	en	2025-10-18 21:17:57.675891+00	2025-10-18 21:17:57.675891+00	f	f	f	0	0	\N	{"id": 275735842, "is_bot": false, "username": "martino009", "first_name": "martins", "language_code": "en"}	2025-10-18 21:17:57.675891+00
420	420279837	Munakra	𝓖𝓮𝓷𝓲𝔂𝓪	𝓑𝓻𝓪𝔃𝓲𝓵𝓮𝓿𝓼𝓴𝓪𝔂𝓪	ru	2025-10-18 23:47:39.36287+00	2025-10-18 23:47:39.36287+00	f	t	f	0	0	\N	{"id": 420279837, "is_bot": false, "username": "Munakra", "last_name": "𝓑𝓻𝓪𝔃𝓲𝓵𝓮𝓿𝓼𝓴𝓪𝔂𝓪", "first_name": "𝓖𝓮𝓷𝓲𝔂𝓪", "is_premium": true, "language_code": "ru"}	2025-10-18 23:47:39.36287+00
399	8451800463	\N	❤️👁🕊🌦👑🤝🏼🔺️🔻🕎🔥✡️📜🛐	\N	he	2025-10-13 20:06:54.205784+00	2025-10-19 12:11:11.970099+00	f	f	f	0	0	\N	{"id": 8451800463, "is_bot": false, "first_name": "❤️👁🕊🌦👑🤝🏼🔺️🔻🕎🔥✡️📜🛐", "language_code": "he"}	2025-10-19 12:11:11.970099+00
422	145488954	reb_yankel	Mashpia	\N	en	2025-10-19 23:51:34.667289+00	2025-10-19 23:51:34.667289+00	f	f	f	0	0	\N	{"id": 145488954, "is_bot": false, "username": "reb_yankel", "first_name": "Mashpia", "language_code": "en"}	2025-10-19 23:51:34.667289+00
423	1809852419	\N	A	S	en	2025-10-20 22:58:40.797256+00	2025-10-20 22:58:40.797256+00	f	f	f	0	0	\N	{"id": 1809852419, "is_bot": false, "last_name": "S", "first_name": "A", "language_code": "en"}	2025-10-20 22:58:40.797256+00
424	1077412096	Laaburrixion	Osman Sarcos	\N	es	2025-10-22 18:12:35.095558+00	2025-10-22 18:12:35.095558+00	f	f	f	0	0	\N	{"id": 1077412096, "is_bot": false, "username": "Laaburrixion", "first_name": "Osman Sarcos", "language_code": "es"}	2025-10-22 18:12:35.095558+00
425	6181054389	\N	Bonat	\N	en	2025-10-23 12:37:51.286453+00	2025-10-23 12:37:51.286453+00	f	f	f	0	0	\N	{"id": 6181054389, "is_bot": false, "first_name": "Bonat", "language_code": "en"}	2025-10-23 12:37:51.286453+00
426	7650609791	\N	Wabela Shifa	Atazo	en	2025-10-23 14:55:16.75528+00	2025-10-23 14:55:16.75528+00	f	f	f	0	0	\N	{"id": 7650609791, "is_bot": false, "last_name": "Atazo", "first_name": "Wabela Shifa", "language_code": "en"}	2025-10-23 14:55:16.75528+00
428	774455	britishpop	Maxi	Frolof	en	2025-10-25 12:16:15.335849+00	2025-10-25 12:16:15.335849+00	f	t	f	0	0	\N	{"id": 774455, "is_bot": false, "username": "britishpop", "last_name": "Frolof", "first_name": "Maxi", "is_premium": true, "language_code": "en"}	2025-10-25 12:16:15.335849+00
429	206397663	over_chernova	Чернова	Катерина	ru	2025-10-26 02:26:36.755931+00	2025-10-26 02:26:36.755931+00	f	t	f	0	0	\N	{"id": 206397663, "is_bot": false, "username": "over_chernova", "last_name": "Катерина", "first_name": "Чернова", "is_premium": true, "language_code": "ru"}	2025-10-26 02:26:36.755931+00
430	933046226	cardosogyn	Michel	\N	pt-br	2025-10-26 15:52:48.183076+00	2025-10-26 15:52:48.183076+00	f	f	f	0	0	\N	{"id": 933046226, "is_bot": false, "username": "cardosogyn", "first_name": "Michel", "language_code": "pt-br"}	2025-10-26 15:52:48.183076+00
431	1222951298	\N	AL	\N	en	2025-10-26 18:24:41.15023+00	2025-10-26 18:24:41.15023+00	f	f	f	0	0	\N	{"id": 1222951298, "is_bot": false, "first_name": "AL", "language_code": "en"}	2025-10-26 18:24:41.15023+00
432	7080616729	kofman_tg	Леонид	Кофман	ru	2025-10-27 10:54:36.81294+00	2025-10-27 10:54:36.81294+00	f	t	f	0	0	\N	{"id": 7080616729, "is_bot": false, "username": "kofman_tg", "last_name": "Кофман", "first_name": "Леонид", "is_premium": true, "language_code": "ru"}	2025-10-27 10:54:36.81294+00
434	6834647836	Aviv2222	א	\N	he	2025-10-27 20:24:11.869066+00	2025-10-27 20:24:11.869066+00	f	f	f	0	0	\N	{"id": 6834647836, "is_bot": false, "username": "Aviv2222", "first_name": "א", "language_code": "he"}	2025-10-27 20:24:11.869066+00
435	6842171874	Moshehjayim09	Mosheh Jayim	\N	es	2025-10-28 12:30:18.487103+00	2025-10-28 12:30:18.487103+00	f	f	f	0	0	\N	{"id": 6842171874, "is_bot": false, "username": "Moshehjayim09", "first_name": "Mosheh Jayim", "language_code": "es"}	2025-10-28 12:30:18.487103+00
436	150927061	Imdoingwe11	Yana	\N	ru	2025-10-29 18:26:02.664372+00	2025-10-29 18:26:02.664372+00	f	t	f	0	0	\N	{"id": 150927061, "is_bot": false, "username": "Imdoingwe11", "first_name": "Yana", "is_premium": true, "language_code": "ru"}	2025-10-29 18:26:02.664372+00
316	6458566821	Scholar_Newman	Scholar	Newman	en	2025-10-05 15:14:52.539856+00	2025-10-29 18:40:22.857064+00	f	f	f	0	0	\N	{"id": 6458566821, "is_bot": false, "username": "Scholar_Newman", "last_name": "Newman", "first_name": "Scholar", "language_code": "en"}	2025-10-29 18:40:22.857064+00
438	264846544	eksbazhenova	Ekaterina	Bazhenova	ru	2025-10-29 20:30:26.779114+00	2025-10-29 20:30:26.779114+00	f	t	f	0	0	\N	{"id": 264846544, "is_bot": false, "username": "eksbazhenova", "last_name": "Bazhenova", "first_name": "Ekaterina", "is_premium": true, "language_code": "ru"}	2025-10-29 20:30:26.779114+00
439	1072201482	KERIM1983	Kerim	B.	de	2025-10-30 05:19:25.210245+00	2025-10-30 05:19:25.210245+00	f	f	f	0	0	\N	{"id": 1072201482, "is_bot": false, "username": "KERIM1983", "last_name": "B.", "first_name": "Kerim", "language_code": "de"}	2025-10-30 05:19:25.210245+00
440	257118001	i_baranov	Ivan	B	ru	2025-10-30 10:38:25.697663+00	2025-10-30 10:38:25.697663+00	f	t	f	0	0	\N	{"id": 257118001, "is_bot": false, "username": "i_baranov", "last_name": "B", "first_name": "Ivan", "is_premium": true, "language_code": "ru"}	2025-10-30 10:38:25.697663+00
441	8043230106	thegoldz	Камиль	\N	ru	2025-10-30 23:21:32.766119+00	2025-10-30 23:21:32.766119+00	f	f	f	0	0	\N	{"id": 8043230106, "is_bot": false, "username": "thegoldz", "first_name": "Камиль", "language_code": "ru"}	2025-10-30 23:21:32.766119+00
443	5610316170	gentleeyes	Gittel Leah גיטל לאה - (Gail)	\N	en	2025-11-01 00:12:12.608207+00	2025-11-01 00:12:12.608207+00	f	t	f	0	0	\N	{"id": 5610316170, "is_bot": false, "username": "gentleeyes", "first_name": "Gittel Leah גיטל לאה - (Gail)", "is_premium": true, "language_code": "en"}	2025-11-01 00:12:12.608207+00
444	8202955608	\N	DF	\N	pt-br	2025-11-02 12:41:26.424277+00	2025-11-02 12:41:26.424277+00	f	f	f	0	0	\N	{"id": 8202955608, "is_bot": false, "first_name": "DF", "language_code": "pt-br"}	2025-11-02 12:41:26.424277+00
445	7487795512	\N	Lèo	\N	en	2025-11-02 13:33:16.088013+00	2025-11-02 13:33:16.088013+00	f	f	f	0	0	\N	{"id": 7487795512, "is_bot": false, "first_name": "Lèo", "language_code": "en"}	2025-11-02 13:33:16.088013+00
446	6197011645	\N	Javid	\N	en	2025-11-02 18:42:33.886124+00	2025-11-02 18:42:33.886124+00	f	f	f	0	0	\N	{"id": 6197011645, "is_bot": false, "first_name": "Javid", "language_code": "en"}	2025-11-02 18:42:33.886124+00
447	680582708	\N	Людмила	\N	ru	2025-11-04 08:47:21.823409+00	2025-11-04 08:47:21.823409+00	f	t	f	0	0	\N	{"id": 680582708, "is_bot": false, "first_name": "Людмила", "is_premium": true, "language_code": "ru"}	2025-11-04 08:47:21.823409+00
\.


--
-- Name: replit_database_migrations_v1_id_seq; Type: SEQUENCE SET; Schema: _system; Owner: neondb_owner
--

SELECT pg_catalog.setval('_system.replit_database_migrations_v1_id_seq', 18, true);


--
-- Name: admin_users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.admin_users_id_seq', 1, false);


--
-- Name: audit_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.audit_log_id_seq', 1, false);


--
-- Name: delivery_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.delivery_log_id_seq', 1, false);


--
-- Name: newsletter_broadcasts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.newsletter_broadcasts_id_seq', 277, true);


--
-- Name: newsletter_subscriptions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.newsletter_subscriptions_id_seq', 446, true);


--
-- Name: test_broadcasts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.test_broadcasts_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.users_id_seq', 447, true);


--
-- Name: replit_database_migrations_v1 replit_database_migrations_v1_pkey; Type: CONSTRAINT; Schema: _system; Owner: neondb_owner
--

ALTER TABLE ONLY _system.replit_database_migrations_v1
    ADD CONSTRAINT replit_database_migrations_v1_pkey PRIMARY KEY (id);


--
-- Name: admin_users admin_users_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.admin_users
    ADD CONSTRAINT admin_users_pkey PRIMARY KEY (id);


--
-- Name: admin_users admin_users_telegram_user_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.admin_users
    ADD CONSTRAINT admin_users_telegram_user_id_key UNIQUE (telegram_user_id);


--
-- Name: audit_log audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_pkey PRIMARY KEY (id);


--
-- Name: delivery_log delivery_log_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.delivery_log
    ADD CONSTRAINT delivery_log_pkey PRIMARY KEY (id);


--
-- Name: newsletter_broadcasts newsletter_broadcasts_broadcast_date_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.newsletter_broadcasts
    ADD CONSTRAINT newsletter_broadcasts_broadcast_date_key UNIQUE (broadcast_date);


--
-- Name: newsletter_broadcasts newsletter_broadcasts_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.newsletter_broadcasts
    ADD CONSTRAINT newsletter_broadcasts_pkey PRIMARY KEY (id);


--
-- Name: newsletter_subscriptions newsletter_subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.newsletter_subscriptions
    ADD CONSTRAINT newsletter_subscriptions_pkey PRIMARY KEY (id);


--
-- Name: test_broadcasts test_broadcasts_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.test_broadcasts
    ADD CONSTRAINT test_broadcasts_pkey PRIMARY KEY (id);


--
-- Name: newsletter_broadcasts unique_broadcast_date_type; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.newsletter_broadcasts
    ADD CONSTRAINT unique_broadcast_date_type UNIQUE (broadcast_date, broadcast_type);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_telegram_user_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_telegram_user_id_key UNIQUE (telegram_user_id);


--
-- Name: idx_replit_database_migrations_v1_build_id; Type: INDEX; Schema: _system; Owner: neondb_owner
--

CREATE UNIQUE INDEX idx_replit_database_migrations_v1_build_id ON _system.replit_database_migrations_v1 USING btree (build_id);


--
-- Name: idx_admin_users_role; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_admin_users_role ON public.admin_users USING btree (role, is_active);


--
-- Name: idx_admin_users_telegram_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_admin_users_telegram_id ON public.admin_users USING btree (telegram_user_id);


--
-- Name: idx_audit_event_type; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_audit_event_type ON public.audit_log USING btree (event_type);


--
-- Name: idx_audit_resource; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_audit_resource ON public.audit_log USING btree (resource);


--
-- Name: idx_audit_timestamp; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_audit_timestamp ON public.audit_log USING btree ("timestamp");


--
-- Name: idx_audit_user; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_audit_user ON public.audit_log USING btree (user_identifier);


--
-- Name: idx_broadcasts_created; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_broadcasts_created ON public.newsletter_broadcasts USING btree (created_at DESC);


--
-- Name: idx_broadcasts_date; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_broadcasts_date ON public.newsletter_broadcasts USING btree (broadcast_date DESC);


--
-- Name: idx_broadcasts_status; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_broadcasts_status ON public.newsletter_broadcasts USING btree (status, scheduled_at);


--
-- Name: idx_delivery_log_broadcast; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_delivery_log_broadcast ON public.delivery_log USING btree (broadcast_id, status);


--
-- Name: idx_delivery_log_status_scheduled; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_delivery_log_status_scheduled ON public.delivery_log USING btree (status, scheduled_at) WHERE ((status)::text = 'pending'::text);


--
-- Name: idx_delivery_log_user; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_delivery_log_user ON public.delivery_log USING btree (user_id, delivered_at DESC);


--
-- Name: idx_newsletter_subscriptions_user_id_unique; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE UNIQUE INDEX idx_newsletter_subscriptions_user_id_unique ON public.newsletter_subscriptions USING btree (user_id);


--
-- Name: idx_quiz_topics_recent; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_quiz_topics_recent ON public.newsletter_broadcasts USING btree (quiz_topic, created_at) WHERE (quiz_topic IS NOT NULL);


--
-- Name: idx_subscriptions_delivery_time; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_subscriptions_delivery_time ON public.newsletter_subscriptions USING btree (delivery_time, timezone) WHERE (is_active = true);


--
-- Name: idx_subscriptions_language; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_subscriptions_language ON public.newsletter_subscriptions USING btree (language) WHERE (is_active = true);


--
-- Name: idx_subscriptions_user_active; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_subscriptions_user_active ON public.newsletter_subscriptions USING btree (user_id, is_active);


--
-- Name: idx_unique_daily_broadcast; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE UNIQUE INDEX idx_unique_daily_broadcast ON public.newsletter_broadcasts USING btree (broadcast_date, broadcast_type) WHERE (broadcast_type IS NOT NULL);


--
-- Name: idx_users_created; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_users_created ON public.users USING btree (created_at DESC);


--
-- Name: idx_users_last_interaction; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_users_last_interaction ON public.users USING btree (last_interaction DESC);


--
-- Name: idx_users_telegram_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_users_telegram_id ON public.users USING btree (telegram_user_id);


--
-- Name: idx_users_username; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_users_username ON public.users USING btree (username) WHERE (username IS NOT NULL);


--
-- Name: delivery_log update_broadcast_delivery_stats; Type: TRIGGER; Schema: public; Owner: neondb_owner
--

CREATE TRIGGER update_broadcast_delivery_stats AFTER UPDATE ON public.delivery_log FOR EACH ROW EXECUTE FUNCTION public.update_broadcast_stats();


--
-- Name: users update_users_updated_at; Type: TRIGGER; Schema: public; Owner: neondb_owner
--

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: delivery_log delivery_log_broadcast_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.delivery_log
    ADD CONSTRAINT delivery_log_broadcast_id_fkey FOREIGN KEY (broadcast_id) REFERENCES public.newsletter_broadcasts(id) ON DELETE CASCADE;


--
-- Name: delivery_log delivery_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.delivery_log
    ADD CONSTRAINT delivery_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(telegram_user_id) ON DELETE CASCADE;


--
-- Name: newsletter_subscriptions newsletter_subscriptions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.newsletter_subscriptions
    ADD CONSTRAINT newsletter_subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(telegram_user_id) ON DELETE CASCADE;


--
-- Name: test_broadcasts test_broadcasts_admin_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.test_broadcasts
    ADD CONSTRAINT test_broadcasts_admin_id_fkey FOREIGN KEY (admin_id) REFERENCES public.admin_users(telegram_user_id);


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON SEQUENCES TO neon_superuser WITH GRANT OPTION;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLES TO neon_superuser WITH GRANT OPTION;


--
-- PostgreSQL database dump complete
--

