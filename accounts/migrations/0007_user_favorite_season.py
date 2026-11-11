from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('accounts', '0006_user_tutorial_seen_at')]

    operations = [
        migrations.AddField(
            model_name='user',
            name='favorite_season',
            field=models.CharField(
                choices=[('spring', '봄'), ('summer', '여름'), ('autumn', '가을'), ('winter', '겨울')],
                default='spring',
                max_length=10,
                verbose_name='좋아하는 계절',
            ),
        ),
    ]
