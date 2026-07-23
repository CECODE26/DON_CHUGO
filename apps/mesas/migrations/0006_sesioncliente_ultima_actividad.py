import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mesas", "0005_mesa_nota_cierre"),
    ]

    operations = [
        migrations.AddField(
            model_name="sesioncliente",
            name="ultima_actividad",
            field=models.DateTimeField(
                db_index=True,
                default=django.utils.timezone.now,
            ),
        ),
    ]
