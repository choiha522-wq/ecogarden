from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('accounts', '0007_user_favorite_season')]

    operations = [
        migrations.RemoveField(model_name='user', name='photo_plant_date'),
        migrations.RemoveField(model_name='user', name='photo_plant_count'),
    ]
