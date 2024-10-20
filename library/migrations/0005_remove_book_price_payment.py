# Generated by Django 5.1 on 2024-09-27 03:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0004_book_price'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='book',
            name='price',
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('card_number', models.CharField(max_length=16)),
                ('expiry_date', models.CharField(max_length=7)),
                ('cvv', models.CharField(max_length=3)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('book_request', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='library.bookrequest')),
            ],
        ),
    ]