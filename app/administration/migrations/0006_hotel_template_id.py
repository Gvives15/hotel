from django.db import migrations, models


def set_serene_template(apps, schema_editor):
    Hotel = apps.get_model('administration', 'Hotel')
    try:
        obj = Hotel.objects.filter(slug='the-serene').first()
        if obj and getattr(obj, 'template_id', None) != 'nuevo':
            obj.template_id = 'nuevo'
            obj.save(update_fields=['template_id'])
        obj2 = Hotel.objects.filter(name__iexact='The Serene').first()
        if obj2 and getattr(obj2, 'template_id', None) != 'nuevo':
            obj2.template_id = 'nuevo'
            obj2.save(update_fields=['template_id'])
    except Exception:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('administration', '0005_hotel_plan_name_hotel_subscription_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='hotel',
            name='template_id',
            field=models.CharField(default='client', max_length=50),
        ),
        migrations.RunPython(set_serene_template, migrations.RunPython.noop),
    ]