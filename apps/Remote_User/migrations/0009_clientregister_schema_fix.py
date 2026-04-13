from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Remote_User', '0008_schema_state_sync'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientregister_model',
            name='gender',
            field=models.CharField(default='', max_length=30),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='clientregister_model',
            name='address',
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
    ]