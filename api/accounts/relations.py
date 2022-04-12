from rest_framework.serializers import RelatedField

from .models import Skill, Interest


class SkillRelatedField(RelatedField):
    queryset = Skill.objects.all()

    def to_representation(self, value):
        return value.name

    def to_internal_value(self, data):
        skill, created = Skill.objects.get_or_create(name=data)
        return skill


class InterestRelatedField(RelatedField):
    queryset = Interest.objects.all()

    def to_representation(self, value):
        return value.name

    def to_internal_value(self, data):
        interest, created = Interest.objects.get_or_create(name=data)
        return interest
