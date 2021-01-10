import sqlite3


class SQLighter:

    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def select_all(self):
        """ Получаем все строки """
        with self.connection:
            return self.cursor.execute('SELECT * FROM users').fetchall()

    def select_single(self, id):
        """ Получаем одну строку с номером rownum """
        with self.connection:
            return self.cursor.execute('SELECT * FROM users WHERE id = ?', (id,)).fetchall()[0]

    def count_rows(self):
        """ Считаем количество строк """
        with self.connection:
            return self.cursor.execute('SELECT COUNT(1) FROM users').fetchall()[0]

    def add_line(self, id):
        """ Добовляем запись """
        with self.connection:
            return self.cursor.execute('''INSERT INTO users (id)
                                        VALUES ({})'''.format(id))

    def mark_blocked(self, id):
        """Помечаем что пользователь заблокировал бота"""
        with self.connection:
            return self.cursor.execute('''UPDATE users SET is_available=0 WHERE id={}'''.format(id))

    def mark_unblocked(self, id):
        """Помечаем что пользователь разблокировал бота"""
        with self.connection:
            return self.cursor.execute('''UPDATE users SET is_available=1 WHERE id={}'''.format(id))

    def get_number_of_active_users(self):
        """Считаем количество активных пользователей"""
        with self.connection:
            return self.cursor.execute('SELECT COUNT(1) FROM users WHERE is_available=1').fetchall()[0]

    def close(self):
        """ Закрываем текущее соединение с БД """
        self.connection.close()
