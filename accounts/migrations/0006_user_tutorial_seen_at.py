from django.db import migrations, models


def mark_existing_users(apps, schema_editor):
    from django.utils import timezone
    User = apps.get_model('accounts', 'User')
    User.objects.using(schema_editor.connection.alias).filter(tutorial_seen_at__isnull=True).update(tutorial_seen_at=timezone.now())


class Migration(migrations.Migration):
    dependencies = [('accounts', '0005_alter_user_id')]
    operations = [
        migrations.AddField(
            model_name='user', name='tutorial_seen_at',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.RunPython(mark_existing_users, migrations.RunPython.noop),
    ]
