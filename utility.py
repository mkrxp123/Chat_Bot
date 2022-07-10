import sqlite3
from functools import wraps
sqlite3.enable_callback_tracebacks(True)

# init
def initDataBase(name):
    database = sqlite3.connect(f'./database/{name}.db')
    database.row_factory = sqlite3.Row
    with open(f'./database/schema/{name}.sql', 'r') as f:
        database.cursor().executescript(f.read())
    database.cursor().execute("PRAGMA foreign_keys=ON")
    return database
db = {i: initDataBase(i) for i in ['record', 'image']}


def delOutDatedData(name, table):
    db[name].cursor().execute(f"""
        delete from {table}
        where julianday('now') - julianday(start_time) > duration
    """)
    db[name].commit()
    return
delOutDatedData('record', 'Memo')


def registerUser(auther):
    rst = db['record'].cursor().execute("select UID from Users where UID = ?", (auther.id,)).fetchone()
    if rst:
        return '你已經有建立資料了'
    db['record'].cursor().execute('''
        insert into Users (UID, U_name)
        values (?, ?)
    ''', (auther.id, auther.name))
    db['record'].commit()
    return '資料建立成功'


def registerRequired(function):
    @wraps(function)
    def wrap(*args, **kwargs):
        rst = db['record'].cursor().execute("select UID from Users where UID = ?", (args[0],)).fetchone()
        if rst:
            return function(*args, **kwargs)
        else:
            return False, '請先創立資料，用 !register'
    return wrap


@registerRequired
def addMemo(id, msg, duration):
    try:
        db['record'].cursor().execute('''
            insert into Memo (UID, content, duration)
            values (?, ?, ?)
        ''', (id, msg, duration))
    except:
        return False, 'insert失敗，最多256個字'
    db['record'].commit()
    return True, 'insert成功'


@registerRequired
def getMemo(id):
    try:
        rst = db['record'].cursor().execute('''
            select MID, content, strftime('%Y/%m/%d %H:%M', start_time) as time
            from Memo
            where UID = ?
            order by start_time
        ''', (id,)).fetchall()
    except:
        return False, 'insert失敗，最多256個字'
    response = (True, rst) if rst else (False, '沒有儲存的資料')
    return response


@registerRequired
def delMemo(id, MID):
    rst = db['record'].cursor().execute('''
        select MID from Memo
        where MID = ?    
    ''', (MID,)).fetchone()
    if not rst:
        return False, '沒有這項紀錄'
    try:
        db['record'].cursor().execute('''
            delete from Memo
            where MID = ?
            and UID = ?
        ''', (MID, id))
    except:
        return False, '你想刪除別人訊息，小壞蛋'
        
    db['record'].commit()
    return True, 'insert成功'

