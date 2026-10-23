import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def backfill_created_events(apps, schema_editor):
    """Give tasks that predate the audit trail a 'created' entry so every task has a history."""
    Task = apps.get_model('app', 'Task')
    TaskEvent = apps.get_model('app', 'TaskEvent')
    for task in Task.objects.select_related('board').all():
        event = TaskEvent.objects.create(
            board=task.board,
            task=task,
            ticket=f'{task.board.prefix}-{task.number}',
            task_title=task.title,
            actor=task.board.owner,
            event_type='created',
            changes=[],
        )
        # auto_now_add stamped "now"; use the task's real creation time instead
        TaskEvent.objects.filter(pk=event.pk).update(created_at=task.created_at)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0002_tickets_and_categories'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticket', models.CharField(max_length=30)),
                ('task_title', models.CharField(max_length=200)),
                ('event_type', models.CharField(choices=[('created', 'Created'), ('moved', 'Moved'), ('edited', 'Edited'), ('deleted', 'Deleted')], max_length=10)),
                ('changes', models.JSONField(blank=True, default=list)),
                ('note', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='task_events', to=settings.AUTH_USER_MODEL)),
                ('board', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='app.board')),
                ('task', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='events', to='app.task')),
            ],
            options={
                'ordering': ['-created_at', '-pk'],
            },
        ),
        migrations.RunPython(backfill_created_events, migrations.RunPython.noop),
    ]
