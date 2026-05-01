CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone VARCHAR,
    p_type VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    contact_id_value INTEGER;
BEGIN
    IF p_type NOT IN ('home', 'work', 'mobile') THEN
        RAISE EXCEPTION 'Phone type must be home, work, or mobile';
    END IF;

    SELECT id
    INTO contact_id_value
    FROM contacts
    WHERE LOWER(name) = LOWER(p_contact_name);

    IF contact_id_value IS NULL THEN
        RAISE EXCEPTION 'Contact not found';
    END IF;

    INSERT INTO phones(contact_id, phone, type)
    VALUES (contact_id_value, p_phone, p_type);
END;
$$;

CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    contact_id_value INTEGER;
    group_id_value INTEGER;
BEGIN
    SELECT id
    INTO contact_id_value
    FROM contacts
    WHERE LOWER(name) = LOWER(p_contact_name);

    IF contact_id_value IS NULL THEN
        RAISE EXCEPTION 'Contact not found';
    END IF;

    INSERT INTO groups(name)
    VALUES (p_group_name)
    ON CONFLICT (name) DO NOTHING;

    SELECT id
    INTO group_id_value
    FROM groups
    WHERE LOWER(name) = LOWER(p_group_name);

    UPDATE contacts
    SET group_id = group_id_value
    WHERE id = contact_id_value;
END;
$$;

CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE (
    id INTEGER,
    name VARCHAR,
    email VARCHAR,
    birthday DATE,
    group_name VARCHAR,
    phones TEXT,
    date_added TIMESTAMP
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.name,
        c.email,
        c.birthday,
        g.name,
        COALESCE(STRING_AGG(p.phone || ' (' || p.type || ')', ', ' ORDER BY p.id), ''),
        c.date_added
    FROM contacts c
    LEFT JOIN groups g ON g.id = c.group_id
    LEFT JOIN phones p ON p.contact_id = c.id
    WHERE c.name ILIKE '%' || p_query || '%'
       OR c.email ILIKE '%' || p_query || '%'
       OR g.name ILIKE '%' || p_query || '%'
       OR EXISTS (
            SELECT 1
            FROM phones p2
            WHERE p2.contact_id = c.id
              AND p2.phone ILIKE '%' || p_query || '%'
       )
    GROUP BY c.id, c.name, c.email, c.birthday, g.name, c.date_added
    ORDER BY c.name;
END;
$$;

CREATE OR REPLACE FUNCTION get_contacts_page(
    p_limit INTEGER,
    p_offset INTEGER,
    p_sort_by TEXT DEFAULT 'name'
)
RETURNS TABLE (
    id INTEGER,
    name VARCHAR,
    email VARCHAR,
    birthday DATE,
    group_name VARCHAR,
    phones TEXT,
    date_added TIMESTAMP
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_sort_by = 'birthday' THEN
        RETURN QUERY
        SELECT s.id, s.name, s.email, s.birthday, s.group_name, s.phones, s.date_added
        FROM search_contacts('') s
        ORDER BY s.birthday NULLS LAST, s.name
        LIMIT p_limit OFFSET p_offset;

    ELSIF p_sort_by = 'date_added' THEN
        RETURN QUERY
        SELECT s.id, s.name, s.email, s.birthday, s.group_name, s.phones, s.date_added
        FROM search_contacts('') s
        ORDER BY s.date_added DESC
        LIMIT p_limit OFFSET p_offset;

    ELSE
        RETURN QUERY
        SELECT s.id, s.name, s.email, s.birthday, s.group_name, s.phones, s.date_added
        FROM search_contacts('') s
        ORDER BY s.name
        LIMIT p_limit OFFSET p_offset;
    END IF;
END;
$$;
