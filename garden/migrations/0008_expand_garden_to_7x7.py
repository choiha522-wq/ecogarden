from django.db import migrations


def center_existing_plots(apps, schema_editor):
    GardenPlot = apps.get_model('garden', 'GardenPlot')
    alias = schema_editor.connection.alias
    plots = GardenPlot.objects.using(alias).all().only('pk', 'slot_index')

    # Move to temporary indexes first so the per-user unique constraint cannot collide.
    for plot in plots.iterator():
        GardenPlot.objects.using(alias).filter(pk=plot.pk).update(slot_index=plot.slot_index + 100)

    for plot in GardenPlot.objects.using(alias).filter(slot_index__gte=100, slot_index__lt=125).only('pk', 'slot_index').iterator():
        old_row, old_col = divmod(plot.slot_index - 100, 5)
        centered_slot = (old_row + 1) * 7 + old_col + 1
        GardenPlot.objects.using(alias).filter(pk=plot.pk).update(slot_index=centered_slot)


class Migration(migrations.Migration):
    dependencies = [('garden', '0007_feedback_collection_weekly_themes')]

    operations = [migrations.RunPython(center_existing_plots, migrations.RunPython.noop)]
