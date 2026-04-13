from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Remote_User', '0009_clientregister_schema_fix'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='cyber_threat_identification',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('fid', models.CharField(max_length=300)),
                        ('tweet_text', models.CharField(max_length=3000)),
                        ('timestamp', models.CharField(max_length=300)),
                        ('source', models.CharField(max_length=300)),
                        ('symbols', models.CharField(max_length=300)),
                        ('company_names', models.CharField(max_length=300)),
                        ('url', models.CharField(max_length=3000)),
                        ('source_ip', models.CharField(max_length=300)),
                        ('protocol', models.CharField(max_length=300)),
                        ('dest_ip', models.CharField(max_length=300)),
                        ('Prediction', models.CharField(max_length=300)),
                    ],
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "CREATE TABLE IF NOT EXISTS Remote_User_cyber_threat_identification ("
                        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                        "fid varchar(300) NOT NULL, "
                        "tweet_text varchar(3000) NOT NULL, "
                        "timestamp varchar(300) NOT NULL, "
                        "source varchar(300) NOT NULL, "
                        "symbols varchar(300) NOT NULL, "
                        "company_names varchar(300) NOT NULL, "
                        "url varchar(3000) NOT NULL, "
                        "source_ip varchar(300) NOT NULL, "
                        "protocol varchar(300) NOT NULL, "
                        "dest_ip varchar(300) NOT NULL, "
                        "Prediction varchar(300) NOT NULL"
                        ")"
                    ),
                    reverse_sql="DROP TABLE IF EXISTS Remote_User_cyber_threat_identification",
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='detection_accuracy',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('names', models.CharField(max_length=300)),
                        ('ratio', models.CharField(max_length=300)),
                    ],
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "CREATE TABLE IF NOT EXISTS Remote_User_detection_accuracy ("
                        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                        "names varchar(300) NOT NULL, "
                        "ratio varchar(300) NOT NULL"
                        ")"
                    ),
                    reverse_sql="DROP TABLE IF EXISTS Remote_User_detection_accuracy",
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='detection_ratio',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('names', models.CharField(max_length=300)),
                        ('ratio', models.CharField(max_length=300)),
                    ],
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "CREATE TABLE IF NOT EXISTS Remote_User_detection_ratio ("
                        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                        "names varchar(300) NOT NULL, "
                        "ratio varchar(300) NOT NULL"
                        ")"
                    ),
                    reverse_sql="DROP TABLE IF EXISTS Remote_User_detection_ratio",
                ),
            ],
        ),
    ]