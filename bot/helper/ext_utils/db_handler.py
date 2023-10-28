import psycopg2
from psycopg2 import Error
from bot import AUTHORIZED_CHATS, SUDO_USERS, DB_URI, LOGGER

class DbManger:
    def __init__(self):
        self.err = False

    def connect(self):
        try:
            self.conn = psycopg2.connect(DB_URI)
            self.cur = self.conn.cursor()
        except psycopg2.DatabaseError as error :
            LOGGER.error("Error in dbMang : ", error)
            self.err = True

    def disconnect(self):
        self.cur.close()
        self.conn.close()

    def db_auth(self,chat_id: int):
        self.connect()
        if self.err:
            return "There's some error check log for details"
        sql = f'INSERT INTO users VALUES ({chat_id});'
        self.cur.execute(sql)
        self.conn.commit()
        self.disconnect()
        AUTHORIZED_CHATS.add(chat_id)
        return 'Authorized successfully'

    def db_unauth(self,chat_id: int):
        self.connect()
        if self.err:
            return "There's some error check log for details"
        sql = f'DELETE from users where uid = {chat_id};'
        self.cur.execute(sql)
        self.conn.commit()
        self.disconnect()
        AUTHORIZED_CHATS.remove(chat_id)
        return 'Unauthorized successfully'

    def db_addsudo(self,chat_id: int):
        self.connect()
        if self.err:
            return "There's some error check log for details"
        if chat_id in AUTHORIZED_CHATS:
            sql = f'UPDATE users SET sudo = TRUE where uid = {chat_id};'
            self.cur.execute(sql)
            self.conn.commit()
            self.disconnect()
            SUDO_USERS.add(chat_id)
            return 'Successfully promoted as Sudo'
        else:
            sql = f'INSERT INTO users VALUES ({chat_id},TRUE);'
            self.cur.execute(sql)
            self.conn.commit()
            self.disconnect()
            SUDO_USERS.add(chat_id)
            return 'Successfully Authorized and promoted as Sudo'

    def db_rmsudo(self,chat_id: int):
        self.connect()
        if self.err:
            return "There's some error check log for details"
        sql = f'UPDATE users SET sudo = FALSE where uid = {chat_id};'
        self.cur.execute(sql)
        self.conn.commit()
        self.disconnect()
        SUDO_USERS.remove(chat_id)
        return 'Successfully removed from Sudo'