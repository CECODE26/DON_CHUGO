from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("pedidos", "0007_idempotencia_y_sesiones_cubiertas"),
    ]

    operations = [
        migrations.AddField(
            model_name="pedido",
            name="cantidad_adiciones",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Número de veces que el cliente añadió productos a este pedido.",
            ),
        ),
        migrations.AddField(
            model_name="pedido",
            name="fecha_hora_actualizacion",
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name="PedidoConfirmacion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token", models.CharField(max_length=64, unique=True)),
                ("fecha_hora", models.DateTimeField(auto_now_add=True)),
                ("pedido", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="confirmaciones", to="pedidos.pedido")),
            ],
            options={
                "verbose_name": "Confirmación de pedido",
                "verbose_name_plural": "Confirmaciones de pedido",
            },
        ),
    ]
