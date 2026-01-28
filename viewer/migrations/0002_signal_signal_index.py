from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('viewer', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='signal',
            name='signal_index',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterModelOptions(
            name='signal',
            options={'ordering': ['signal_index']},
        ),
    ]
