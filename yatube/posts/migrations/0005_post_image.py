# Generated by Django 2.2.16 on 2023-01-25 12:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0004_auto_20230125_1502'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, upload_to='posts/', verbose_name='Картинка'),
        ),
    ]
