CREATE TABLE schema_migrations (
    executed_at timestamp without time zone,
    filename character varying,
    checksum character varying
);


CREATE TABLE policy (
    id integer,
    created_at timestamp without time zone,
    internal_id uuid,
    klubb character varying,
    policy_content text
);

INSERT INTO policy VALUES (3, 'Liverpool FC', '{"title": ["Introduktion", "F\\u00f6reningens vision och v\\u00e4rderingar", "Ledarens roll och ansvar", "Tr\\u00e4ning och match", "Kommunikation och samarbete", "Fotbollens spela, lek och l\\u00e4r", "Sammanfattning"], "content": ["Att vara ungdomsledare i en fotbollsklubb som Liverpool FC inneb\\u00e4r att ha en nyckelroll i att utveckla b\\u00e5de unga spelares fotbollskunskaper och deras personliga egenskaper. En bra ledare i Liverpool FC f\\u00f6rst\\u00e5r klubbens starka v\\u00e4rderingar, s\\u00e5som laganda, h\\u00e5rt arbete och passion, och integrerar dessa i sitt dagliga arbete med ungdomarna. Genom att skapa en inkluderande och motiverande milj\\u00f6 bidrar ledaren till att bygga framtidens fotbollsspelare och goda samh\\u00e4llsmedborgare.", "Liverpool FC \\u00e4r en klubb med en stark tradition av att k\\u00e4mpa f\\u00f6r laget och alltid ge sitt b\\u00e4sta. Som ledare i ungdomssektionen \\u00e4r det din uppgift att f\\u00f6rmedla dessa v\\u00e4rderingar till spelarna. Visionen \\u00e4r att inte bara utveckla duktiga fotbollsspelare utan \\u00e4ven bygga starka karakt\\u00e4rer som st\\u00e5r f\\u00f6r \\u00f6dmjukhet, respekt och ansvar. Du beh\\u00f6ver betona vikten av att alltid arbeta tillsammans och att spelarna tar ansvar b\\u00e5de p\\u00e5 och utanf\\u00f6r planen.", "Som ungdomsledare har du ett stort ansvar f\\u00f6r att s\\u00e4kerst\\u00e4lla att varje spelare k\\u00e4nner sig sedd, h\\u00f6rd och v\\u00e4rderad. Din roll \\u00e4r att inspirera och v\\u00e4gleda spelarna, b\\u00e5de individuellt och som ett lag. Du beh\\u00f6ver skapa en trygg och positiv milj\\u00f6 d\\u00e4r varje individ kan v\\u00e4xa. Ett stort fokus ligger p\\u00e5 att st\\u00f6tta deras utveckling p\\u00e5 ett l\\u00e5ngsiktigt och h\\u00e5llbart s\\u00e4tt. Du f\\u00f6rv\\u00e4ntas vara ett f\\u00f6red\\u00f6me som lever upp till de v\\u00e4rderingar du l\\u00e4r ut, och samtidigt vara flexibel och anpassa din ledarstil till varje spelares unika behov.", "P\\u00e5 tr\\u00e4ningar och under matcher \\u00e4r det viktigt att fokusera p\\u00e5 utveckling snarare \\u00e4n resultat. Tr\\u00e4ningarna ska vara strukturerade och roliga, med ett fokus p\\u00e5 att utveckla grundl\\u00e4ggande fotbollstekniker och spelf\\u00f6rst\\u00e5else. Matcher \\u00e4r till f\\u00f6r att spelarna ska f\\u00e5 praktisera det de l\\u00e4rt sig och utveckla sin speluppfattning under verkliga f\\u00f6rh\\u00e5llanden. Uppmuntra alltid laget att arbeta tillsammans och att varje spelare tar ansvar f\\u00f6r sin roll p\\u00e5 planen. Det \\u00e4r genom samarbetet och laginsatsen som b\\u00e5de individer och laget kan v\\u00e4xa.", "\\u00d6ppen och tydlig kommunikation \\u00e4r en grundpelare i allt ledarskap. Du beh\\u00f6ver skapa en milj\\u00f6 d\\u00e4r spelarna k\\u00e4nner sig trygga att uttrycka sig och d\\u00e4r de vet att deras \\u00e5sikter v\\u00e4rderas. Samarbete med f\\u00f6r\\u00e4ldrar och andra ledare \\u00e4r ocks\\u00e5 viktigt f\\u00f6r att skapa en gemensam f\\u00f6rst\\u00e5else f\\u00f6r barnens utveckling. Arbeta f\\u00f6r en transparent dialog d\\u00e4r b\\u00e5de framsteg och utmaningar tas upp p\\u00e5 ett konstruktivt s\\u00e4tt. Ett framg\\u00e5ngsrikt samarbete bygger p\\u00e5 att alla, b\\u00e5de spelare och ledare, delar klubbens gemensamma m\\u00e5l och v\\u00e4rderingar.", "Som en del av svensk fotbolls filosofi \\"Spela, lek och l\\u00e4r\\" \\u00e4r det viktigt att du ser till att fotbollen \\u00e4r rolig och utvecklande f\\u00f6r ungdomarna. Syftet \\u00e4r att skapa en gl\\u00e4djefylld fotbollsmilj\\u00f6 d\\u00e4r spelarna utvecklar sina f\\u00e4rdigheter genom att leka och utforska fotbollen p\\u00e5 ett naturligt s\\u00e4tt. Resultat ska inte st\\u00e5 i fokus, utan snarare spelarnas l\\u00e5ngsiktiga utveckling, b\\u00e5de som idrottare och individer. Alla spelare ska f\\u00e5 lika m\\u00f6jligheter att utvecklas och k\\u00e4nna gl\\u00e4dje \\u00f6ver att spela fotboll. Detta leder till en positiv inst\\u00e4llning till sporten som kan f\\u00f6lja med dem livet ut.", "Som ungdomsledare i Liverpool FC har du ett ansvar att fostra unga spelare i enlighet med klubbens v\\u00e4rderingar om laganda, h\\u00e5rt arbete och \\u00f6dmjukhet. Genom att prioritera utveckling framf\\u00f6r resultat och skapa en inkluderande och motiverande milj\\u00f6, kan du hj\\u00e4lpa spelarna att v\\u00e4xa b\\u00e5de som fotbollsspelare och m\\u00e4nniskor. Ledarskapet kr\\u00e4ver en balans mellan att inspirera och ge konstruktiv kritik, och att alltid vara en f\\u00f6rebild som lever enligt de v\\u00e4rderingar klubben st\\u00e5r f\\u00f6r."], "questions": [{"text": "Som ledare i Liverpool FC ska fokus alltid vara p\\u00e5 utveckling snarare \\u00e4n resultat.", "correct_answer": true}, {"text": "Det \\u00e4r viktigt att alla spelare i laget f\\u00e5r lika mycket speltid och m\\u00f6jligheter, oavsett deras prestation.", "correct_answer": true}, {"text": "Enligt \'Spela, lek och l\\u00e4r\' ska matchresultaten prioriteras \\u00f6ver spelarnas l\\u00e5ngsiktiga utveckling.", "correct_answer": false}]}', datetime.datetime(2024, 9, 29, 19, 42, 2, 118762), '06c9aa89-8506-4b4f-aaa4-33d246afe25e');

CREATE TABLE signature (
    id integer,
    datum timestamp without time zone,
    internal_id uuid,
    email character varying,
    position character varying,
    namn character varying,
    klubb character varying
);

INSERT INTO signature VALUES (29, 'Allison Becker', 'Liverpool FC', 'Position saknas', 'oscarkvissberg@gmail.com', datetime.datetime(2024, 9, 29, 20, 53, 22, 286411), 'ac53dd60-055d-4526-972f-605544e4fd2d');

CREATE TABLE sent_email (
    date timestamp without time zone,
    id integer,
    internal_id uuid,
    status character varying,
    email character varying,
    klubb character varying,
    name character varying
);

INSERT INTO sent_email VALUES (103, 'Liverpool FC', 'Mohammed Salah', 'oscarkvissberg@gmail.com', datetime.datetime(2024, 9, 29, 20, 3, 2, 123036), 'Skickad', 'f5fefc17-4e4b-44c0-8efd-b40d4f8a6dd1');
INSERT INTO sent_email VALUES (104, 'Liverpool FC', 'Diogo Jota', 'oscarkvissberg@gmail.com', datetime.datetime(2024, 9, 29, 20, 10, 23, 259415), 'Skickad', '03539d6a-96ec-4a83-a433-7ccafa047b52');
INSERT INTO sent_email VALUES (105, 'Liverpool FC', 'Virgil Van Dijik', 'oscarkvissberg@gmail.com', datetime.datetime(2024, 9, 29, 20, 37, 49, 429924), 'Skickad', '3b50f308-c739-4abc-b8f3-83b8ff251ea4');
INSERT INTO sent_email VALUES (106, 'Liverpool FC', 'Darwin Nunez', 'oscarkvissberg@gmail.com', datetime.datetime(2024, 9, 29, 20, 46, 18, 933422), 'Skickad', 'e6d60c09-3d8f-44ab-9314-a08cf63a8cad');
INSERT INTO sent_email VALUES (108, 'Liverpool FC', 'Oscar Kvissberg', 'oscarkvissberg@gmail.com', datetime.datetime(2024, 9, 29, 20, 59, 2, 936025), 'Påmind', '9c453c4d-0af2-49ce-8204-0344d9b23e4a');
INSERT INTO sent_email VALUES (109, 'Liverpool FC', 'Andy Robertsson', 'oscarkvissberg@gmail.com', datetime.datetime(2024, 9, 29, 21, 2, 16, 440182), 'Skickad', '6be98545-5dd6-4b47-b6f7-81f989694e2b');
INSERT INTO sent_email VALUES (110, 'Liverpool FC', 'test', 'oscarkvissberg@gmail.com', datetime.datetime(2024, 9, 29, 21, 7, 32, 336331), 'Påmind', '43e48131-bd33-44ec-9142-94f2734d825c');

CREATE TABLE club (
    id integer,
    name character varying
);


