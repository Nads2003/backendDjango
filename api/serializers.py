from rest_framework import serializers
from .models import Compte, Etudiant, Professeur, Mention, Niveau, Cours, Notification
from django.contrib.auth.hashers import make_password
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CompteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compte
        fields = ['id', 'username', 'email', 'password', 'role','photo']
        extra_kwargs = {'password': {'write_only': True},
                        'photo':{'required':False,'allow_null':True}
                        }

    def create(self, validated_data):
        validated_data['password']=make_password(validated_data['password'])
        return super().create(validated_data)
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['username'] = user.username
        token['email'] = user.email
        return token

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        user = Compte.objects.filter(email=email).first()
        if user and user.check_password(password):
            attrs["username"] = user.username
            data = super().validate(attrs)
            # ✅ Ajoute les infos dans la réponse envoyée à React
            data['role'] = user.role
            data['username'] = user.username
            data['email'] = user.email
            return data
        raise serializers.ValidationError("Email ou mot de passe incorrect.")

from rest_framework import serializers
from .models import Mention, Niveau, Professeur, Cours

class MentionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mention
        fields = ['id', 'nom']


class NiveauSerializer(serializers.ModelSerializer):
    mention = MentionSerializer(read_only=True)

    class Meta:
        model = Niveau
        fields = ['id', 'nom', 'mention']


class ProfesseurSerializer(serializers.ModelSerializer):
    compte = CompteSerializer()  # affichera "Prénom Nom"

    class Meta:
        model = Professeur
        fields = ['id', 'compte', 'specialite']


class CoursSerializer(serializers.ModelSerializer):
    mention = MentionSerializer(read_only=True)
    niveau = NiveauSerializer(read_only=True)
    professeur = ProfesseurSerializer(read_only=True)

    mention_id = serializers.PrimaryKeyRelatedField(
        queryset=Mention.objects.all(), source='mention', write_only=True
    )
    niveau_id = serializers.PrimaryKeyRelatedField(
        queryset=Niveau.objects.all(), source='niveau', write_only=True
    )

    class Meta:
        model = Cours
        fields = [
            'id', 'titre', 'description',
            'mention', 'niveau', 'professeur',
            'mention_id', 'niveau_id',
            'date_debut', 'date_fin', 'fichier'
        ]

from rest_framework import serializers
from .models import Favori

class FavoriSerializer(serializers.ModelSerializer):
    cours = CoursSerializer()  # inclure les infos détaillées du cours
    class Meta:
        model = Favori
        fields = ['id', 'etudiant', 'cours', 'date_ajout']
