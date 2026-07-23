from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pedidos", "0008_pedido_acumulado"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pedido",
            name="estado",
            field=models.CharField(
                choices=[
                    ("recibido", "Recibido"),
                    ("preparando", "Preparando"),
                    ("listo", "Listo"),
                    ("entregado", "Entregado"),
                    ("pagado", "Pagado"),
                    ("cancelado", "Cancelado"),
                ],
                default="recibido",
                max_length=10,
            ),
        ),
    ]
