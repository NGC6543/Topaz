import sqlite3

DB_NAME = 'notes.db'


class ManageDb:
    def __init__(self):
        ...

    def connect_to_db(self):
        return sqlite3.connect(DB_NAME)

    def create_tables(self):
        sql_statements = [
            '''CREATE TABLE IF NOT EXISTS tag (
                id INTEGER PRIMARY KEY,
                name VARCHAR(24) UNIQUE
                );''',
            '''CREATE TABLE IF NOT EXISTS note_tag (
                tag_id INTEGER,
                note_id INTEGER,
                PRIMARY KEY (tag_id, note_id),
                FOREIGN KEY (tag_id) REFERENCES tag (id),
                FOREIGN KEY (note_id) REFERENCES note (id) ON DELETE CASCADE
                );''',
            '''CREATE TABLE IF NOT EXISTS note (
                id INTEGER PRIMARY KEY,
                title VARCHAR(24),
                text TEXT,
                FOREIGN KEY (id) REFERENCES note_tag (note_id)
                );'''

        ]
        try:
            with self.connect_to_db() as conn:
                cursor = conn.cursor()
                for statement in sql_statements:
                    cursor.execute(statement)
        except sqlite3.Error as e:
            print(f'Error occured: \n {e}')

    def insert_tags_into_table(self, cursor, tags: list):
        """Insert tags into tag table. Just insert new tags
        and get all id for these tags.

        cursor argument need for consistency:
        If the tag insertion fails, the connection should rollback().
        """
        try:
            # Insert data in db
            insert_tag_data = 'INSERT OR IGNORE INTO tag(name) VALUES(?);'
            cursor.executemany(
                insert_tag_data, [(tag,) for tag in tags if tag != '']
            )

            # Get tags from db
            join_tags = ','.join('?' for _ in tags)
            select_data_from_tag = (
                f'SELECT id, name FROM tag WHERE name IN ({join_tags});'
            )
            cursor.execute(select_data_from_tag, tags)
            get_data_from_tag = cursor.fetchall()
            tag_map: dict = {name: tid for tid, name in get_data_from_tag}
            return tag_map
        except sqlite3.Error as e:
            print(f'Error occured: \n {e}')

    def insert_data_in_tables(self, title: str, text: str, tags: list):
        try:
            with self.connect_to_db() as conn:
                cursor = conn.cursor()

                # Insert data into tag table
                tag_map = self.insert_tags_into_table(cursor, tags)

                # Insert data into note table
                insert_data_note = (
                    'INSERT INTO note(title, text) VALUES(?, ?);'
                )
                cursor.execute(insert_data_note, (title, text))
                note_last_row_id = cursor.lastrowid

                # Insert data into intermediate table note_tag
                if tag_map:
                    insert_data_note_tag = (
                        'INSERT INTO note_tag(tag_id, note_id) VALUES(?, ?);'
                    )
                    cursor.executemany(
                        insert_data_note_tag,
                        [
                            (tag_id, note_last_row_id) for tag_id in tag_map.values()
                        ]
                    )
                return note_last_row_id
        except sqlite3.Error as e:
            print(f'Error occured: \n {e}')

    def get_all_data_from_db(self):
        try:
            with self.connect_to_db() as conn:
                cursor = conn.cursor()
                statement = '''
                    SELECT n.id, n.title, n.text,
                    GROUP_CONCAT(t.name, ',') AS tags
                    FROM note n
                    LEFT JOIN note_tag nt ON n.id = nt.note_id
                    LEFT JOIN tag t ON t.id = nt.tag_id
                    GROUP BY n.id;'''
            cursor.execute(statement)
            data_from_db = cursor.fetchall()

            db_dict = {}
            for note_id, title, text, tags in data_from_db:
                db_dict[note_id] = (
                    title, text, tags.split(',') if tags else []
                )
            return db_dict

        except sqlite3.Error as e:
            print(f'Error occured: \n {e}')

    def show_data(self, note_title):
        try:
            with self.connect_to_db() as conn:
                cursor = conn.cursor()
                statement = '''
                    SELECT n.title, n.text, t.name FROM note n
                    LEFT JOIN note_tag nt ON (n.id=nt.note_id)
                    LEFT JOIN tag t ON (t.id=nt.tag_id)
                    WHERE n.title=(?);'''
                cursor.execute(statement, (note_title,))
                data = cursor.fetchall()
                return data
        except sqlite3.Error as e:
            print(f'Error occured: \n {e}')

    def update_data(self, note_id, new_title, text, tags):
        try:
            with self.connect_to_db() as conn:
                cursor = conn.cursor()
                tag_map = self.insert_tags_into_table(cursor, tags)
                get_note_id = cursor.execute(
                    'SELECT id FROM note WHERE id=?',
                    (note_id,)
                ).fetchone()
                # It must be impossible that updated_title doesnt exists
                if not get_note_id:
                    return 'Cannot update'

                statement = '''
                    UPDATE note
                    SET title=?, text=?
                    WHERE id=?'''

                cursor.execute(statement, (new_title, text, note_id))

                # Refresh intermediate table
                cursor.execute(
                    'SELECT tag_id FROM note_tag WHERE note_id=?',
                    (note_id,)
                )
                current_tag_ids = {row[0] for row in cursor.fetchall()}

                if tag_map:
                    new_tag_ids = {tag_map[tag] for tag in tags if tag != ''}

                    tags_to_add = new_tag_ids - current_tag_ids
                    tags_to_remove = current_tag_ids - new_tag_ids
                    if tags_to_add:
                        cursor.executemany(
                            'INSERT INTO note_tag (note_id, tag_id) VALUES (?, ?)',
                            [(note_id, tid) for tid in tags_to_add]
                        )
                    if tags_to_remove:
                        cursor.executemany(
                            "DELETE FROM note_tag WHERE note_id = ? AND tag_id = ?",
                            [(note_id, tid) for tid in tags_to_remove]
                        )
        except sqlite3.Error as e:
            print(f'Error occured: \n {e}')

    def delete_note(self, note_id):
        try:
            with self.connect_to_db() as conn:
                cursor = conn.cursor()
                statement = '''
                    DELETE FROM note
                    WHERE id=(?);'''
                cursor.execute(statement, (note_id,))
                return True
        except sqlite3.Error as e:
            print(f'Error occured: \n {e}')


if __name__ == '__main__':
    init_db = ManageDb()
    init_db.create_tables()
    title = 'ThirdNote'
    text = 'ThirdText'
    tags = ['#history', '#programming', '#hashtag']
    # init_db.insert_data_in_tables(title, text, tags)
    # init_db.show_data('ThirdNote')
    print(init_db.get_all_data_from_db())
    # init_db.update_data('ThirdNoteNew', 'ThirdNoteNew2', 'tesxt', ['#python', '#C++'])
