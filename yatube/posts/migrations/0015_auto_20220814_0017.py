# Generated by Django 2.2.16 on 2022-08-13 21:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0014_follow'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='follow',
            options={'verbose_name': 'Подписка', 'verbose_name_plural': 'Подписки'},
        ),
    ]