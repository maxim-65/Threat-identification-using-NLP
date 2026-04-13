import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / 'db.sqlite3'


def main() -> None:
    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()
    cur.execute('PRAGMA foreign_keys=OFF')
    cur.execute('BEGIN')

    rebuilds = [
        (
            'django_content_type',
            'CREATE TABLE django_content_type (id INTEGER PRIMARY KEY AUTOINCREMENT, app_label varchar(100) NOT NULL, model varchar(100) NOT NULL)',
            'id,app_label,model',
        ),
        (
            'auth_permission',
            'CREATE TABLE auth_permission (id INTEGER PRIMARY KEY AUTOINCREMENT, name varchar(255) NOT NULL, content_type_id int(11) NOT NULL, codename varchar(100) NOT NULL)',
            'id,name,content_type_id,codename',
        ),
        (
            'auth_group',
            'CREATE TABLE auth_group (id INTEGER PRIMARY KEY AUTOINCREMENT, name varchar(80) NOT NULL)',
            'id,name',
        ),
        (
            'auth_user',
            'CREATE TABLE auth_user (id INTEGER PRIMARY KEY AUTOINCREMENT, password varchar(128) NOT NULL, last_login datetime(6) DEFAULT NULL, is_superuser tinyint(1) NOT NULL, username varchar(150) NOT NULL, first_name varchar(30) NOT NULL, last_name varchar(150) NOT NULL, email varchar(254) NOT NULL, is_staff tinyint(1) NOT NULL, is_active tinyint(1) NOT NULL, date_joined datetime(6) NOT NULL)',
            'id,password,last_login,is_superuser,username,first_name,last_name,email,is_staff,is_active,date_joined',
        ),
        (
            'auth_group_permissions',
            'CREATE TABLE auth_group_permissions (id INTEGER PRIMARY KEY AUTOINCREMENT, group_id int(11) NOT NULL, permission_id int(11) NOT NULL)',
            'id,group_id,permission_id',
        ),
        (
            'auth_user_groups',
            'CREATE TABLE auth_user_groups (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id int(11) NOT NULL, group_id int(11) NOT NULL)',
            'id,user_id,group_id',
        ),
        (
            'auth_user_user_permissions',
            'CREATE TABLE auth_user_user_permissions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id int(11) NOT NULL, permission_id int(11) NOT NULL)',
            'id,user_id,permission_id',
        ),
        (
            'django_admin_log',
            'CREATE TABLE django_admin_log (id INTEGER PRIMARY KEY AUTOINCREMENT, action_time datetime(6) NOT NULL, object_id longtext, object_repr varchar(200) NOT NULL, action_flag smallint(5) NOT NULL, change_message longtext NOT NULL, content_type_id int(11) DEFAULT NULL, user_id int(11) NOT NULL)',
            'id,action_time,object_id,object_repr,action_flag,change_message,content_type_id,user_id',
        ),
    ]

    for table, create_sql, cols in rebuilds:
        cur.execute(f'ALTER TABLE {table} RENAME TO {table}_old')
        cur.execute(create_sql)
        cur.execute(f'INSERT INTO {table} ({cols}) SELECT {cols} FROM {table}_old')
        cur.execute(f'DROP TABLE {table}_old')

    indexes = [
        'CREATE UNIQUE INDEX IF NOT EXISTS django_content_type_app_label_model_76bd3d3b_uniq ON django_content_type(app_label, model)',
        'CREATE UNIQUE INDEX IF NOT EXISTS auth_permission_content_type_id_codename_01ab375a_uniq ON auth_permission(content_type_id, codename)',
        'CREATE UNIQUE INDEX IF NOT EXISTS auth_group_name_key ON auth_group(name)',
        'CREATE UNIQUE INDEX IF NOT EXISTS auth_user_username_key ON auth_user(username)',
        'CREATE UNIQUE INDEX IF NOT EXISTS auth_group_permissions_group_id_permission_id_uniq ON auth_group_permissions(group_id, permission_id)',
        'CREATE UNIQUE INDEX IF NOT EXISTS auth_user_groups_user_id_group_id_uniq ON auth_user_groups(user_id, group_id)',
        'CREATE UNIQUE INDEX IF NOT EXISTS auth_user_user_permissions_user_id_permission_id_uniq ON auth_user_user_permissions(user_id, permission_id)',
    ]
    for idx_sql in indexes:
        cur.execute(idx_sql)

    con.commit()
    cur.execute('PRAGMA foreign_keys=ON')
    con.close()
    print('auth/core tables repaired')


if __name__ == '__main__':
    main()
