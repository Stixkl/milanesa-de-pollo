# Generated by Django 3.1.12 on 2025-05-23 02:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academic_data', '0002_alter_group_id_alter_studentprofile_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='credits',
            field=models.PositiveIntegerField(default=3, help_text='Number of academic credits for this subject'),
        ),
        migrations.AlterField(
            model_name='group',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='studentprofile',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
