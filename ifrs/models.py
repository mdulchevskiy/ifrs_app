from django.db import models


class UploadInfo(models.Model):
    table_name = models.CharField(max_length=255, default=None)
    table_size = models.CharField(max_length=255, default=None)
    upload_date = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=255, default=None)
    file_type = models.CharField(max_length=255, default=None)
    file_date = models.DateField()
    uploading_time = models.TimeField()

    def __str__(self):
        return f'{self.pk}: {self.table_name}'


class IFRSData(models.Model):
    date = models.DateField()
    ccf_over = models.FloatField(null=True)
    lgd_auto = models.FloatField(null=True)
    lgd_nedv = models.FloatField(null=True)
    lgd_potr = models.FloatField(null=True)
    lgd_delay = models.FloatField(null=True)
    lgd_over = models.FloatField(null=True)
    pd_auto_0 = models.FloatField(null=True)
    pd_auto_1_30 = models.FloatField(null=True)
    pd_auto_31_60 = models.FloatField(null=True)
    pd_auto_61_90 = models.FloatField(null=True)
    pd_auto_91 = models.FloatField(null=True)
    pd_nedv_0 = models.FloatField(null=True)
    pd_nedv_1_30 = models.FloatField(null=True)
    pd_nedv_31_60 = models.FloatField(null=True)
    pd_nedv_61_90 = models.FloatField(null=True)
    pd_nedv_91 = models.FloatField(null=True)
    pd_potr_0 = models.FloatField(null=True)
    pd_potr_1_30 = models.FloatField(null=True)
    pd_potr_31_60 = models.FloatField(null=True)
    pd_potr_61_90 = models.FloatField(null=True)
    pd_potr_91 = models.FloatField(null=True)
    pd_delay_0 = models.FloatField(null=True)
    pd_delay_1_30 = models.FloatField(null=True)
    pd_delay_31_60 = models.FloatField(null=True)
    pd_delay_61_90 = models.FloatField(null=True)
    pd_delay_91 = models.FloatField(null=True)
    pd_over_0 = models.FloatField(null=True)
    pd_over_1_30 = models.FloatField(null=True)
    pd_over_31_60 = models.FloatField(null=True)
    pd_over_61_90 = models.FloatField(null=True)
    pd_over_91 = models.FloatField(null=True)

    def __str__(self):
        return f'{self.pk}: {self.date}'
