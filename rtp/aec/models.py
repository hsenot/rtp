from django.contrib.gis.db import models


class federal_electorate_2016(models.Model):
    elect_div = models.CharField(max_length=30)
    state = models.CharField(max_length=4)
    numccds = models.IntegerField()
    actual = models.IntegerField()
    projected = models.IntegerField()
    total_population = models.IntegerField()
    australians_over_18 = models.IntegerField()
    area_sqkm = models.FloatField()
    sortname = models.CharField(max_length=30)
    the_geom = models.MultiPolygonField(srid=4326)


# Auto-generated `LayerMapping` dictionary for national model
federal_electorate_2016_mapping = {
    'elect_div': 'Elect_div',
    'state': 'State',
    'numccds': 'Numccds',
    'actual': 'Actual',
    'projected': 'Projected',
    'total_population': 'Total_Popu',
    'australians_over_18': 'Australian',
    'area_sqkm': 'Area_SqKm',
    'sortname': 'Sortname',
    'the_geom': 'POLYGON',
}
