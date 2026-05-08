from django.core.validators import MaxValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0006_alter_category_id_alter_product_id_alter_review_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="discount_percent",
            field=models.PositiveSmallIntegerField(
                default=0,
                validators=[MaxValueValidator(90)],
            ),
        ),
    ]
