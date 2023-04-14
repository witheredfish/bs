# Generated by Django 3.2.17 on 2023-04-14 08:29

from django.conf import settings
import django.core.validators
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
            name='GrantFundingAgency',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=255, verbose_name='名称')),
            ],
            options={
                'verbose_name': '资助机构',
                'verbose_name_plural': '资助机构',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='GrantStatusChoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('name', models.CharField(max_length=64, verbose_name='资助状态')),
            ],
            options={
                'verbose_name': '资助状态',
                'verbose_name_plural': '资助状态',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='HistoricalGrant',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('title', models.CharField(max_length=255, validators=[django.core.validators.MinLengthValidator(3), django.core.validators.MaxLengthValidator(255)], verbose_name='标题')),
                ('grant_number', models.CharField(max_length=255, validators=[django.core.validators.MinLengthValidator(3), django.core.validators.MaxLengthValidator(255)], verbose_name='资助机构的授权编号')),
                ('role', models.CharField(choices=[('PI', '项目负责人'), ('CoPI', '联合负责人'), ('SP', '高级人员')], max_length=10, verbose_name='角色')),
                ('grant_pi_full_name', models.CharField(blank=True, max_length=255, verbose_name='资助项目负责人名称')),
                ('other_funding_agency', models.CharField(blank=True, max_length=255, verbose_name='其他资助机构')),
                ('other_award_number', models.CharField(blank=True, max_length=255, verbose_name='其他奖励')),
                ('grant_start', models.DateField(verbose_name='资助开始时间')),
                ('grant_end', models.DateField(verbose_name='资助结束时间')),
                ('percent_credit', models.FloatField(validators=[django.core.validators.MaxValueValidator(100)], verbose_name='占比')),
                ('direct_funding', models.FloatField(verbose_name='直接资助')),
                ('total_amount_awarded', models.FloatField(verbose_name='资助总和')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('funding_agency', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='grant.grantfundingagency', verbose_name='资助机构')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='project.project', verbose_name='项目')),
                ('status', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='grant.grantstatuschoice', verbose_name='状态')),
            ],
            options={
                'verbose_name': '历史',
                'verbose_name_plural': 'historical 资助',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='Grant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('title', models.CharField(max_length=255, validators=[django.core.validators.MinLengthValidator(3), django.core.validators.MaxLengthValidator(255)], verbose_name='标题')),
                ('grant_number', models.CharField(max_length=255, validators=[django.core.validators.MinLengthValidator(3), django.core.validators.MaxLengthValidator(255)], verbose_name='资助机构的授权编号')),
                ('role', models.CharField(choices=[('PI', '项目负责人'), ('CoPI', '联合负责人'), ('SP', '高级人员')], max_length=10, verbose_name='角色')),
                ('grant_pi_full_name', models.CharField(blank=True, max_length=255, verbose_name='资助项目负责人名称')),
                ('other_funding_agency', models.CharField(blank=True, max_length=255, verbose_name='其他资助机构')),
                ('other_award_number', models.CharField(blank=True, max_length=255, verbose_name='其他奖励')),
                ('grant_start', models.DateField(verbose_name='资助开始时间')),
                ('grant_end', models.DateField(verbose_name='资助结束时间')),
                ('percent_credit', models.FloatField(validators=[django.core.validators.MaxValueValidator(100)], verbose_name='占比')),
                ('direct_funding', models.FloatField(verbose_name='直接资助')),
                ('total_amount_awarded', models.FloatField(verbose_name='资助总和')),
                ('funding_agency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='grant.grantfundingagency', verbose_name='资助机构')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='project.project', verbose_name='项目')),
                ('status', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='grant.grantstatuschoice', verbose_name='状态')),
            ],
            options={
                'verbose_name': '资助',
                'verbose_name_plural': '资助',
                'permissions': (('can_view_all_grants', '可以查看所有资助'),),
            },
        ),
    ]
