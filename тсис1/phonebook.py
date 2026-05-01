import csv
import json
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

from connect import connect_db

BASE_FOLDER = Path(__file__).parent

def clean(value):
    if value is None:
        return None

    value = str(value)
    value = value.strip()

    if value == "":
        return None

    return value

def get_phone_type(value):
    value = clean(value)

    if value is None:
        return "mobile"

    value = value.lower()

    if value == "home":
        return "home"

    if value == "work":
        return "work"

    if value == "mobile":
        return "mobile"

    raise ValueError("Phone type must be home, work, or mobile")

def get_group_name(value):
    value = clean(value)

    if value is None:
        return "Other"

    return value

def run_sql_file(filename):
    path = BASE_FOLDER / filename

    file = open(path, "r", encoding="utf-8")
    sql_text = file.read()
    file.close()

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(sql_text)

    connection.commit()
    cursor.close()
    connection.close()

    print(filename, "executed")

def setup_database():
    run_sql_file("schema.sql")
    run_sql_file("procedures.sql")
    print("Database is ready")

def print_contacts(rows):
    if len(rows) == 0:
        print("No contacts found")
        return

    for row in rows:
        print("-" * 50)
        print("ID:", row["id"])
        print("Name:", row["name"])
        print("Email:", row["email"])
        print("Birthday:", row["birthday"])
        print("Group:", row["group_name"])
        print("Phones:", row["phones"])
    print("-" * 50)

def get_group_id(cursor, group_name):
    group_name = get_group_name(group_name)

    cursor.execute(
        "INSERT INTO groups(name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
        (group_name,)
    )

    cursor.execute(
        "SELECT id FROM groups WHERE LOWER(name) = LOWER(%s)",
        (group_name,)
    )

    row = cursor.fetchone()
    group_id = row[0]

    return group_id

def contact_exists(cursor, name):
    cursor.execute(
        "SELECT id FROM contacts WHERE LOWER(name) = LOWER(%s)",
        (name,)
    )

    row = cursor.fetchone()

    if row is None:
        return False
    else:
        return True

def delete_contact(cursor, name):
    cursor.execute(
        "DELETE FROM contacts WHERE LOWER(name) = LOWER(%s)",
        (name,)
    )

def insert_contact(cursor, name, email, birthday, group_id):
    cursor.execute(
        """
        INSERT INTO contacts(name, email, birthday, group_id)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (name, email, birthday, group_id)
    )

    row = cursor.fetchone()
    contact_id = row[0]

    return contact_id

def insert_phones(cursor, contact_id, phones):
    for phone_data in phones:
        phone = clean(phone_data["phone"])
        phone_type = get_phone_type(phone_data["type"])

        if phone is not None:
            cursor.execute(
                """
                INSERT INTO phones(contact_id, phone, type)
                VALUES (%s, %s, %s)
                """,
                (contact_id, phone, phone_type)
            )

def save_contact(name, email, birthday, group_name, phones, overwrite):
    name = clean(name)

    if name is None:
        print("Name cannot be empty")
        return

    email = clean(email)
    birthday = clean(birthday)
    group_name = get_group_name(group_name)

    connection = connect_db()
    cursor = connection.cursor()

    if contact_exists(cursor, name):
        if overwrite:
            delete_contact(cursor, name)
        else:
            print("Contact already exists:", name)
            cursor.close()
            connection.close()
            return

    group_id = get_group_id(cursor, group_name)
    contact_id = insert_contact(cursor, name, email, birthday, group_id)
    insert_phones(cursor, contact_id, phones)

    connection.commit()
    cursor.close()
    connection.close()

    print("Saved:", name)

def add_contact_from_console():
    name = input("Name: ")
    email = input("Email: ")
    birthday = input("Birthday YYYY-MM-DD: ")
    group_name = input("Group: ")

    phones = []

    while True:
        phone = input("Phone, empty to stop: ")

        if phone.strip() == "":
            break

        phone_type = input("Type home/work/mobile: ")

        phones.append({
            "phone": phone,
            "type": phone_type
        })

    save_contact(name, email, birthday, group_name, phones, False)

def add_phone_to_contact():
    name = input("Contact name: ")
    phone = input("New phone: ")
    phone_type = input("Type home/work/mobile: ")
    phone_type = get_phone_type(phone_type)

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        "CALL add_phone(%s, %s, %s)",
        (name, phone, phone_type)
    )

    connection.commit()
    cursor.close()
    connection.close()

    print("Phone added")

def move_contact_to_group():
    name = input("Contact name: ")
    group_name = input("New group: ")

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(
        "CALL move_to_group(%s, %s)",
        (name, group_name)
    )

    connection.commit()
    cursor.close()
    connection.close()

    print("Group changed")

def search_contacts_menu():
    query = input("Search text: ")

    connection = connect_db()
    cursor = connection.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        "SELECT * FROM search_contacts(%s)",
        (query,)
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    print_contacts(rows)

def filter_by_group():
    group_name = input("Group: ")

    connection = connect_db()
    cursor = connection.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        "SELECT * FROM search_contacts(%s) WHERE group_name ILIKE %s",
        (group_name, "%" + group_name + "%")
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    print_contacts(rows)

def search_by_email():
    email = input("Email text: ")

    connection = connect_db()
    cursor = connection.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        "SELECT * FROM search_contacts(%s) WHERE email ILIKE %s",
        (email, "%" + email + "%")
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    print_contacts(rows)

def show_sorted_contacts():
    sort_by = input("Sort by name/birthday/date_added: ")
    sort_by = sort_by.strip().lower()

    if sort_by != "birthday" and sort_by != "date_added":
        sort_by = "name"

    connection = connect_db()
    cursor = connection.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        "SELECT * FROM get_contacts_page(%s, %s, %s)",
        (100, 0, sort_by)
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    print_contacts(rows)

def show_pages():
    page_size_text = input("Page size: ")

    if page_size_text.isdigit():
        page_size = int(page_size_text)
    else:
        page_size = 5

    sort_by = input("Sort by name/birthday/date_added: ")
    sort_by = sort_by.strip().lower()

    if sort_by != "birthday" and sort_by != "date_added":
        sort_by = "name"

    page_number = 0

    while True:
        offset = page_number * page_size

        connection = connect_db()
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            "SELECT * FROM get_contacts_page(%s, %s, %s)",
            (page_size, offset, sort_by)
        )

        rows = cursor.fetchall()

        cursor.close()
        connection.close()

        print("Page:", page_number + 1)
        print_contacts(rows)

        command = input("next/prev/quit: ")
        command = command.strip().lower()

        if command == "next":
            if len(rows) < page_size:
                print("No next page")
            else:
                page_number = page_number + 1

        elif command == "prev":
            if page_number > 0:
                page_number = page_number - 1

        elif command == "quit":
            break

def export_to_json():
    filename = input("Output file [exported_contacts.json]: ")

    if filename.strip() == "":
        filename = "exported_contacts.json"

    connection = connect_db()
    cursor = connection.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM search_contacts('')")
    contacts = cursor.fetchall()

    data = []

    for contact in contacts:
        cursor.execute(
            "SELECT phone, type FROM phones WHERE contact_id = %s ORDER BY id",
            (contact["id"],)
        )

        phone_rows = cursor.fetchall()
        phone_list = []

        for phone_row in phone_rows:
            phone_list.append({
                "phone": phone_row["phone"],
                "type": phone_row["type"]
            })

        item = {
            "name": contact["name"],
            "email": contact["email"],
            "birthday": str(contact["birthday"]) if contact["birthday"] else None,
            "group": contact["group_name"],
            "phones": phone_list
        }

        data.append(item)

    cursor.close()
    connection.close()

    json_text = json.dumps(data, indent=4, ensure_ascii=False)

    path = BASE_FOLDER / filename
    path.write_text(json_text, encoding="utf-8")

    print("Exported:", filename)

def ask_overwrite(name):
    answer = input(name + " exists. Type overwrite to replace, anything else to skip: ")
    answer = answer.strip().lower()

    if answer == "overwrite":
        return True

    return False

def import_from_json():
    filename = input("JSON file [contacts.json]: ")

    if filename.strip() == "":
        filename = "contacts.json"

    path = BASE_FOLDER / filename

    if not path.exists():
        print("File not found")
        return

    text = path.read_text(encoding="utf-8")
    data = json.loads(text)

    for item in data:
        name = clean(item["name"])

        connection = connect_db()
        cursor = connection.cursor()

        already_exists = contact_exists(cursor, name)

        cursor.close()
        connection.close()

        overwrite = False

        if already_exists:
            overwrite = ask_overwrite(name)

            if not overwrite:
                continue

        save_contact(
            item["name"],
            item["email"],
            item["birthday"],
            item["group"],
            item["phones"],
            overwrite
        )

def import_from_csv():
    filename = input("CSV file [contacts.csv]: ")

    if filename.strip() == "":
        filename = "contacts.csv"

    path = BASE_FOLDER / filename

    if not path.exists():
        print("File not found")
        return

    contacts = {}

    file = open(path, "r", encoding="utf-8-sig", newline="")
    reader = csv.DictReader(file)

    for row in reader:
        name = clean(row["name"])

        if name is None:
            continue

        if name not in contacts:
            contacts[name] = {
                "name": name,
                "email": row["email"],
                "birthday": row["birthday"],
                "group": row["group"],
                "phones": []
            }

        phone = clean(row["phone"])

        if phone is not None:
            phone_data = {
                "phone": row["phone"],
                "type": row["type"]
            }

            contacts[name]["phones"].append(phone_data)

    file.close()

    for name in contacts:
        contact = contacts[name]

        connection = connect_db()
        cursor = connection.cursor()

        already_exists = contact_exists(cursor, contact["name"])

        cursor.close()
        connection.close()

        overwrite = False

        if already_exists:
            overwrite = ask_overwrite(contact["name"])

            if not overwrite:
                continue

        save_contact(
            contact["name"],
            contact["email"],
            contact["birthday"],
            contact["group"],
            contact["phones"],
            overwrite
        )

def show_menu():
    print()
    print("TSIS1 PhoneBook")
    print("1  Setup database")
    print("2  Add contact")
    print("3  Add phone")
    print("4  Move contact to group")
    print("5  Search")
    print("6  Filter by group")
    print("7  Search by email")
    print("8  Sort contacts")
    print("9  Paginated view")
    print("10 Export JSON")
    print("11 Import JSON")
    print("12 Import CSV")
    print("0  Exit")

def main():
    while True:
        show_menu()
        choice = input("Choose: ")

        try:
            if choice == "1":
                setup_database()
            elif choice == "2":
                add_contact_from_console()
            elif choice == "3":
                add_phone_to_contact()
            elif choice == "4":
                move_contact_to_group()
            elif choice == "5":
                search_contacts_menu()
            elif choice == "6":
                filter_by_group()
            elif choice == "7":
                search_by_email()
            elif choice == "8":
                show_sorted_contacts()
            elif choice == "9":
                show_pages()
            elif choice == "10":
                export_to_json()
            elif choice == "11":
                import_from_json()
            elif choice == "12":
                import_from_csv()
            elif choice == "0":
                break
            else:
                print("Wrong option")

        except Exception as error:
            print("Error:", error)

if __name__ == "__main__":
    main()
