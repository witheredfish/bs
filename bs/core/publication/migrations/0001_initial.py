# Generated by Django 3.2.17 on 2023-04-14 08:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import simple_history.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('project', '0002_auto_20230414_1629'),
    ]

    operations = [
        migrations.CreateModel(
            name='PublicationSource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='名称')),
                ('url', models.URLField(blank=True, null=True, verbose_name='网址')),
            ],
            options={
                'verbose_name': '出版物资源',
                'verbose_name_plural': '出版物资源',
            },
        ),
        migrations.CreateModel(
            name='HistoricalPublication',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('title', models.CharField(max_length=1024, verbose_name='标题')),
                ('author', models.CharField(max_length=1024, verbose_name='作者')),
                ('year', models.PositiveIntegerField(verbose_name='年份')),
                ('journal', models.CharField(max_length=1024, verbose_name='期刊')),
                ('unique_id', models.CharField(blank=True, max_length=255, null=True, verbose_name='独立ID')),
                ('status', models.CharField(choices=[('Active', '活跃'), ('Archived', '存档')], default='Active', max_length=16, verbose_name='状态')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='project.project', verbose_name='项目')),
                ('source', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='publication.publicationsource', verbose_name='来源地址')),
            ],
            options={
                'verbose_name': '历史',
                'verbose_name_plural': 'historical 出版物',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('title', models.CharField(max_length=1024, verbose_name='标题')),
                ('author', models.CharField(max_length=1024, verbose_name='作者')),
                ('year', models.PositiveIntegerField(verbose_name='年份')),
                ('journal', models.CharField(max_length=1024, verbose_name='期刊')),
                ('unique_id', models.CharField(blank=True, max_length=255, null=True, verbose_name='独立ID')),
                ('status', models.CharField(choices=[('Active', '活跃'), ('Archived', '存档')], default='Active', max_length=16, verbose_name='状态')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='project.project', verbose_name='项目')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='publication.publicationsource', verbose_name='来源地址')),
            ],
            options={
                'verbose_name': '出版物',
                'verbose_name_plural': '出版物',
                'unique_together': {('project', 'unique_id')},
            },
        ),
    ]
