import re

import django.db.models.deletion
from django.db import migrations, models


def _default_prefix(name):
    words = re.findall(r'[A-Za-z0-9]+', name or '')
    if len(words) >= 2:
        prefix = ''.join(w[0] for w in words)[:4]
    elif words:
        prefix = words[0][:3]
    else:
        prefix = 'TSK'
    return prefix.upper()


def number_existing_tasks(apps, schema_editor):
    """Give every existing board a prefix and every existing task a ticket number."""
    Board = apps.get_model('app', 'Board')
    Task = apps.get_model('app', 'Task')
    for board in Board.objects.all():
        board.prefix = _default_prefix(board.name)
        count = 0
        for task in Task.objects.filter(board=board).order_by('created_at', 'pk'):
            count += 1
            task.number = count
            task.save(update_fields=['number'])
        board.ticket_counter = count
        board.save(update_fields=['prefix', 'ticket_counter'])


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='board',
            name='prefix',
            field=models.CharField(default='TSK', max_length=6),
        ),
        migrations.AddField(
            model_name='board',
            name='ticket_counter',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('color', models.CharField(default='#e5e7eb', max_length=20)),
                ('board', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='categories', to='app.board')),
            ],
            options={
                'verbose_name_plural': 'categories',
                'ordering': ['name'],
                'unique_together': {('board', 'name')},
            },
        ),
        migrations.AddField(
            model_name='task',
            name='number',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='task',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tasks', to='app.category'),
        ),
        migrations.RunPython(number_existing_tasks, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name='task',
            unique_together={('board', 'number')},
        ),
    ]
