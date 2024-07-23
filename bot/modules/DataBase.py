import json
import sqlite3 as sq
import datetime

import aiosqlite


class DataBase:
    def __init__(self, path):
        # self.conn = sq.connect(path, check_same_thread=False, timeout=20)
        # self.cursor = self.conn.cursor()
        self.path = path
        self.create_tables()

    links_attributes = {
        "Barona": 'https://barona.fi/tyopaikat/',
        "Eezy": 'https://tyopaikat.eezy.fi',
        "Oikotie": 'https://tyopaikat.oikotie.fi'
    }

    async def get_all_users(self):
        async with aiosqlite.connect(self.path) as conn:
            async with conn.execute('SELECT user_id FROM users') as cursor:
                option = await cursor.fetchall()
                result_array = [row[0] for row in option]
            return result_array




    async def get_user_language(self, user_id):
        async with aiosqlite.connect(self.path) as conn:
            async with conn.execute('SELECT language FROM users WHERE user_id = ?', (user_id,)) as cursor:
                option = await cursor.fetchone()
            return option[0] if option else None

    async def get_user_status(self, user_id):
        async with aiosqlite.connect(self.path) as conn:
            async with conn.execute('SELECT user_status FROM users WHERE user_id = ?', (user_id,)) as cursor:
                option = await cursor.fetchone()
            return option[0] if option else None

    async def set_user_status(self, user_id, status: int):
        async with aiosqlite.connect(self.path) as conn:
            await conn.execute(
                "UPDATE users SET user_status = ? WHERE user_id = ?",
                (status, user_id)
            )
            await conn.commit()

    async def save_user(self, user_id):
        async with aiosqlite.connect(self.path) as conn:
            async with conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                rows = await cursor.fetchall()
                if rows:
                    return
            await conn.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
            await conn.commit()

    async def set_user_language(self, user_id, language):
        async with aiosqlite.connect(self.path) as conn:
            await conn.execute('UPDATE users SET language = (?) WHERE user_id = (?)', (language, user_id))
            await conn.commit()

    async def get_buttons_locked(self, user_telegram_id: int):
        async with aiosqlite.connect(self.path) as conn:
            async with conn.execute('SELECT user_buttons_locked FROM users WHERE user_id = ?', (user_telegram_id,)) as cursor:
                option = await cursor.fetchone()
            return json.loads(option[0]) if option else None

    async def switch_buttons_locked(self, user_telegram_id: int, name: str):
        buttons_locked = await self.get_buttons_locked(user_telegram_id=user_telegram_id)
        if buttons_locked:
            buttons_locked = buttons_locked
        else:
            buttons_locked = []

        if name in buttons_locked:
            buttons_locked.remove(name)
        else:
            buttons_locked.append(name)

        async with aiosqlite.connect(self.path) as conn:
            await conn.execute('UPDATE users SET user_buttons_locked = ? WHERE user_id = ?;',
                               (json.dumps(buttons_locked), user_telegram_id))
            await conn.commit()

    def create_tables(self):
        tables_name = ('Barona', 'Eezy', 'Oikotie')
        fields = (
            '''
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            posted_at DATE,
            slug TEXT,
            title TEXT NOT NULL,
            link TEXT,
            locations JSON,
            deadline DATE,
            description TEXT,
            employment_types JSON,
            language TEXT
            '''
        )

        with sq.connect(self.path) as conn:
            cursor = conn.cursor()
            for table in tables_name:
                cursor.execute(f'''CREATE TABLE IF NOT EXISTS {table} ({fields})''')
            cursor.execute(
                '''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                user_buttons_locked TEXT DEFAULT '[]',
                user_status INT DEFAULT 0,
                barona_id INTEGER DEFAULT 0,
                eezy_id INTEGER DEFAULT 0,
                oikotie_id INTEGER DEFAULT 0,
                language TEXT DEFAULT 'en'
                )'''
            )
            conn.commit()
        return 1

    async def update_user(self, user_id, barona_id=None, eezy_id=None, oikotie_id=None):
        query = "UPDATE users SET "
        sets = []

        if barona_id is not None:
            sets.append(f"barona_id = {barona_id}")

        if eezy_id is not None:
            sets.append(f"eezy_id = {eezy_id}")

        if oikotie_id is not None:
            sets.append(f"oikotie_id = {oikotie_id}")

        if sets:
            query += ", ".join(sets) + f" WHERE user_id = {user_id}"
            async with aiosqlite.connect(self.path) as conn:
                await conn.execute(query)
                await conn.commit()
            return True
        else:
            print("No fields to update provided.")
            return False

    async def clear_old_records(self, table):
        async with aiosqlite.connect(self.path) as conn:
            await conn.execute(f'DELETE FROM {table} WHERE deadline < (?)', (datetime.date.today(),))
            await conn.commit()

    async def get_relevant_records(self, user_id):
        async with aiosqlite.connect(self.path) as conn:
            query = "SELECT barona_id, eezy_id, oikotie_id FROM users WHERE user_id = ?"
            async with conn.execute(query, (user_id,)) as cursor:
                last_viewed_records = await cursor.fetchone()
                if not last_viewed_records:
                    return []

            barona_last_viewed_record, eezy_last_viewed_record, oikotie_last_viewed_record = last_viewed_records

            async with conn.execute(
                    "SELECT * FROM barona WHERE id > ?",
                    (barona_last_viewed_record,)
            ) as cursor:
                barona_rows = await cursor.fetchall()

            async with conn.execute(
                    "SELECT * FROM eezy WHERE id > ?",
                    (eezy_last_viewed_record,)
            ) as cursor:
                eezy_rows = await cursor.fetchall()

            async with conn.execute(
                    "SELECT * FROM oikotie WHERE id > ?",
                    (oikotie_last_viewed_record,)
            ) as cursor:
                oikotie_rows = await cursor.fetchall()

            await self.update_user(
                user_id=user_id,
                barona_id=barona_rows[-1][0] if barona_rows else barona_last_viewed_record,
                eezy_id=eezy_rows[-1][0] if eezy_rows else eezy_last_viewed_record,
                oikotie_id=oikotie_rows[-1][0] if oikotie_rows else oikotie_last_viewed_record
            )

        '''
        ---Returned structure---
        id
        posted
        slug
        title
        link
        locations
        deadline
        desc
        employment type
        lang
        '''

        return barona_rows + eezy_rows + oikotie_rows

    async def save_vacancy(self, table: str,
                           title: str,
                           posted_at: datetime.date = None,
                           slug: str = None,
                           locations: dict = None,
                           deadline: datetime.date = None,
                           description: str = None,
                           employment_types: str = None,
                           language: str = 'fi'):

        async with aiosqlite.connect(self.path) as conn:
            async with conn.execute(f'SELECT * FROM {table} WHERE slug=(?)', (slug,)) as cursor:
                rows = await cursor.fetchall()
                if len(rows) != 0:
                    return False

            if locations is not None:
                try:
                    locations = ", ".join([location["city"] for location in locations])
                except TypeError:
                    locations = ", ".join(location for key, location in locations.items() if location is not None)

            employment_types = json.dumps(employment_types)
            description = description.replace('\n', '')
            link = self.links_attributes.get(table, None) + slug
            await conn.execute(
                f'INSERT INTO {table} '
                f'(posted_at, slug, title, link, locations, deadline, description, employment_types, language) '
                f'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (posted_at, slug, title, link, locations, deadline, description, employment_types, language)
            )
            await conn.commit()

            print(f"{title} SUCCESSFULLY SAVED")
        return None
