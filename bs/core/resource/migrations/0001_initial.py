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
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttributeType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=128, unique=True, verbose_name='属性类型')),
            ],
            options={
                'verbose_name': '属性类型',
                'verbose_name_plural': '属性类型',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ResourceType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=128, unique=True, verbose_name='资源类型')),
                ('description', models.CharField(max_length=255, verbose_name='描述')),
            ],
            options={
                'verbose_name': '资源类型',
                'verbose_name_plural': '资源类型',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ResourceAttributeType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=128, verbose_name='名称')),
                ('is_required', models.BooleanField(default=False, verbose_name='是否可用')),
                ('is_unique_per_resource', models.BooleanField(default=False, verbose_name='是否独立')),
                ('is_value_unique', models.BooleanField(default=False, verbose_name='金额独立')),
                ('attribute_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='resource.attributetype', verbose_name='属性类型')),
            ],
            options={
                'verbose_name': '资源属性类型',
                'verbose_name_plural': '资源属性类型',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=128, unique=True, verbose_name='名称')),
                ('description', models.TextField(verbose_name='描述')),
                ('is_available', models.BooleanField(default=True, verbose_name='是否可获得')),
                ('is_public', models.BooleanField(default=True, verbose_name='是否公共')),
                ('is_allocatable', models.BooleanField(default=True, verbose_name='是否可分配')),
                ('requires_payment', models.BooleanField(default=False, verbose_name='价格')),
                ('allowed_groups', models.ManyToManyField(blank=True, to='auth.Group', verbose_name='分配的小组')),
                ('allowed_users', models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL, verbose_name='分配的成员')),
                ('linked_resources', models.ManyToManyField(blank=True, related_name='_resource_resource_linked_resources_+', to='resource.Resource', verbose_name='关联资源')),
                ('parent_resource', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='resource.resource', verbose_name='主资源')),
                ('resource_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='resource.resourcetype', verbose_name='资源类型')),
            ],
            options={
                'verbose_name': '资源',
                'verbose_name_plural': '资源',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='HistoricalResourceType',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(db_index=True, max_length=128, verbose_name='资源类型')),
                ('description', models.CharField(max_length=255, verbose_name='描述')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '历史',
                'verbose_name_plural': 'historical 资源类型',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalResourceAttributeType',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=128, verbose_name='名称')),
                ('is_required', models.BooleanField(default=False, verbose_name='是否可用')),
                ('is_unique_per_resource', models.BooleanField(default=False, verbose_name='是否独立')),
                ('is_value_unique', models.BooleanField(default=False, verbose_name='金额独立')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('attribute_type', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='resource.attributetype', verbose_name='属性类型')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '历史',
                'verbose_name_plural': 'historical 资源属性类型',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalResourceAttribute',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('value', models.TextField(verbose_name='值')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('resource', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='resource.resource', verbose_name='资源')),
                ('resource_attribute_type', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='resource.resourceattributetype', verbose_name='资源属性类型')),
            ],
            options={
                'verbose_name': '历史',
                'verbose_name_plural': 'historical 资源属性',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalResource',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(db_index=True, max_length=128, verbose_name='名称')),
                ('description', models.TextField(verbose_name='描述')),
                ('is_available', models.BooleanField(default=True, verbose_name='是否可获得')),
                ('is_public', models.BooleanField(default=True, verbose_name='是否公共')),
                ('is_allocatable', models.BooleanField(default=True, verbose_name='是否可分配')),
                ('requires_payment', models.BooleanField(default=False, verbose_name='价格')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('parent_resource', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='resource.resource', verbose_name='主资源')),
                ('resource_type', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='resource.resourcetype', verbose_name='资源类型')),
            ],
            options={
                'verbose_name': '历史',
                'verbose_name_plural': 'historical 资源',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='ResourceAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('value', models.TextField(verbose_name='值')),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='resource.resource', verbose_name='资源')),
                ('resource_attribute_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='resource.resourceattributetype', verbose_name='资源属性类型')),
            ],
            options={
                'verbose_name': '资源属性',
                'verbose_name_plural': '资源属性',
                'unique_together': {('resource_attribute_type', 'resource')},
            },
        ),
    ]