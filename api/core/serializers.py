from rest_framework import serializers

from .models import FileUploads


class FileUploadsSerializer(serializers.ModelSerializer):

    class Meta:
        model = FileUploads
        fields = ('url', 'file_type', 'id', 'description')
        read_only_fields = ('id',)

