from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Remote_User', '0007_clientposts_model_names'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='clientregister_model',
                    name='address',
                    field=models.CharField(default='', max_length=30),
                    preserve_default=False,
                ),
                migrations.AddField(
                    model_name='clientregister_model',
                    name='gender',
                    field=models.CharField(default='', max_length=30),
                    preserve_default=False,
                ),
                migrations.AlterField(
                    model_name='clientregister_model',
                    name='phoneno',
                    field=models.CharField(max_length=10),
                ),
                migrations.AlterField(
                    model_name='clientregister_model',
                    name='password',
                    field=models.CharField(max_length=128),
                ),
            ],
            database_operations=[],
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='prediction_audit',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('username', models.CharField(max_length=50)),
                        ('fid', models.CharField(max_length=300)),
                        ('predicted_label', models.CharField(max_length=300)),
                        ('confidence', models.CharField(max_length=20)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                    ],
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "CREATE TABLE IF NOT EXISTS remote_user_prediction_audit ("
                        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                        "username varchar(50) NOT NULL, "
                        "fid varchar(300) NOT NULL, "
                        "predicted_label varchar(300) NOT NULL, "
                        "confidence varchar(20) NOT NULL, "
                        "created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP"
                        ")"
                    ),
                    reverse_sql="DROP TABLE IF EXISTS remote_user_prediction_audit",
                ),
            ],
        ),
    ]
