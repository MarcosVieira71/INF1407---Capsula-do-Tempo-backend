from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='capsula',
            name='senha',
            field=models.CharField(max_length=128, null=True, blank=True),
        ),
    ]
