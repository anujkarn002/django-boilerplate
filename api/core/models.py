from django.db import models


class BaseModel(models.Model):
    '''
    Base model for all models
    '''
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE,
                                   null=True, blank=True, related_name='%(class)s_created_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class FileUploads(BaseModel):
    '''
    FileUploads Model for storing files related to activities, events, etc
    '''
    class Meta:
        ordering = ['-created_at']

    url = models.URLField()
    FILE_TYPE_CHOICES = (
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Document'),
        ('other', 'Other'),
    )
    file_type = models.CharField(
        max_length=10, choices=FILE_TYPE_CHOICES, default='image')
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.file_type
