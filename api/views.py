from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Cours, Compte
from .serializers import CoursSerializer, CompteSerializer, MyTokenObtainPairSerializer
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Cours
from .serializers import CoursSerializer
from django.http import FileResponse, Http404
from django.conf import settings
import os

from rest_framework import generics, permissions
from .models import Mention, Niveau, Professeur, Cours
from .serializers import MentionSerializer, NiveauSerializer, ProfesseurSerializer, CoursSerializer

# 🔹 Création de compte
class CreerCompter(generics.CreateAPIView):
    queryset = Compte.objects.all()
    serializer_class = CompteSerializer

# 🔹 Login JWT
class CompteTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

# 🔹 Liste des cours
class MesCoursView(generics.ListAPIView):
    serializer_class = CoursSerializer
   # permission_classes = [permissions.IsAuthenticated]


# 🔹 Liste Mentions
class MentionListView(generics.ListAPIView):
    queryset = Mention.objects.all()
    serializer_class = MentionSerializer
   # permission_classes = [permissions.IsAuthenticated]
# 🔹 Liste Niveaux
class NiveauListView(generics.ListAPIView):
    queryset = Niveau.objects.select_related('mention').all()
    serializer_class = NiveauSerializer
    # permission_classes = [permissions.IsAuthenticated]

# 🔹 Liste Professeurs
class ProfesseurListView(generics.ListAPIView):
    queryset = Professeur.objects.select_related('compte').all()
    serializer_class = ProfesseurSerializer
     #permission_classes = [permissions.IsAuthenticated]
class CoursListCreateView(generics.ListCreateAPIView):
    serializer_class = CoursSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        # ✅ Si l'utilisateur est un professeur connecté
        if hasattr(user, 'professeur'):
            return Cours.objects.filter(professeur=user.professeur).select_related('mention', 'niveau', 'professeur')
        if hasattr(user, 'etudiant'):
            etu = user.etudiant
            return Cours.objects.filter(mention=etu.mention,niveau=etu.niveau).select_related('mention', 'niveau', 'professeur')
        return Cours.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'professeur'):
            serializer.save(professeur=user.professeur)
        else:
            raise PermissionDenied("Seuls les professeurs peuvent créer un cours.")

def media_pdf_view(request, pk):
    try:
        cours = Cours.objects.get(pk=pk)
        if not cours.fichier:
            raise Http404("Aucun fichier trouvé.")
        filepath = cours.fichier.path
        filename = os.path.basename(filepath)
        response = FileResponse(open(filepath, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'  # ✅ affichage direct
        return response
    except Cours.DoesNotExist:
        raise Http404("Cours introuvable.")

from rest_framework import generics, permissions
from .models import Favori
from .serializers import FavoriSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

# Ajouter un cours aux favoris
class FavoriCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        if not hasattr(user, 'etudiant'):
            return Response({"detail": "Seuls les étudiants peuvent ajouter des favoris."}, status=status.HTTP_403_FORBIDDEN)
        
        cours_id = request.data.get('cours')
        if not cours_id:
            return Response({"detail": "L'ID du cours est requis."}, status=status.HTTP_400_BAD_REQUEST)
        
        from .models import Cours
        try:
            cours = Cours.objects.get(pk=cours_id)
        except Cours.DoesNotExist:
            return Response({"detail": "Cours introuvable."}, status=status.HTTP_404_NOT_FOUND)
        
        favori, created = Favori.objects.get_or_create(etudiant=user.etudiant, cours=cours)
        if not created:
            return Response({"detail": "Le cours est déjà en favori."}, status=status.HTTP_200_OK)
        
        serializer = FavoriSerializer(favori)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FavoriDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, cours_id, *args, **kwargs):
        user = request.user

        if not hasattr(user, 'etudiant'):
            return Response({"detail": "Seuls les étudiants peuvent retirer des favoris."},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            favori = Favori.objects.get(etudiant=user.etudiant, cours_id=cours_id)
            favori.delete()
            return Response({"detail": "Favori supprimé."}, status=status.HTTP_200_OK)

        except Favori.DoesNotExist:
            return Response({"detail": "Ce cours n'est pas dans vos favoris."},
                            status=status.HTTP_404_NOT_FOUND)

# Lister les favoris d'un étudiant
class FavoriListView(generics.ListAPIView):
    serializer_class = FavoriSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'etudiant'):
            return Favori.objects.filter(etudiant=user.etudiant).select_related('cours')
        return Favori.objects.none()
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Cours
import json
import re
from groq import Groq
client = Groq(api_key=settings.GROQ_API_KEY)
class GenerateQuizIAFree(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cours_id = request.data.get("cours_id")
        try:
            cours = Cours.objects.get(id=cours_id)
        except Cours.DoesNotExist:
            return Response({"error": "Cours introuvable"}, status=404)

        texte_base = f"{cours.titre}\n\n{cours.description or ''}"

        prompt = f"""
Tu es un expert en création de quiz pédagogiques.
Crée un quiz basé sur le texte suivant :

{texte_base}

✅ Requis :
- Minimum 3 questions, maximum 5.
- Questions de type QCM, vrai/faux ou texte à trous.
- Format JSON strict :

{{
  "qcm": [{{ "question": "...", "options": ["A","B","C","D"], "answer": "..." }}],
  "vrai_faux": [{{ "statement": "...", "answer": true }}],
  "textes_trous": [{{ "phrase": "...", "answer": "..." }}]
}}

Réponds uniquement en JSON, **sans aucun texte supplémentaire**.
"""

        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )

            raw_content = getattr(response.choices[0].message, "content", "").strip()
            print("Contenu brut IA :", raw_content)  # 🔹 pour debug

            # Extraire JSON du texte brut
            match = re.search(r'(\{.*\})', raw_content, re.DOTALL)
            if not match:
                raise ValueError("Pas de JSON détecté dans la réponse IA")

            quiz_json = match.group(1)
            quiz = json.loads(quiz_json)

        except (json.JSONDecodeError, ValueError) as e:
            return Response({
                "error": "IA n'a pas généré de JSON valide",
                "raw": raw_content
            }, status=500)
        except Exception as e:
            return Response({"error": f"Erreur IA : {str(e)}"}, status=500)

        # Vérifier le nombre de questions
        total_questions = len(quiz.get("qcm", [])) + len(quiz.get("vrai_faux", [])) + len(quiz.get("textes_trous", []))
        if total_questions < 3:
            return Response({
                "error": "IA n'a pas généré assez de questions (minimum 3).",
                "quiz": quiz
            }, status=500)

        return Response({"quiz": quiz, "warning": False}, status=200)











from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from openai import OpenAI
from .models import MessageAI, ConversationSession
import uuid

# -----------------------
# 🔵 CHAT AI VIEW
# -----------------------
class ChatAIView(APIView):
    def post(self, request):
        user = request.user
        if not hasattr(user, "etudiant"):
            return Response({"error": "Utilisateur non autorisé"}, status=403)

        etudiant = user.etudiant
        user_message = request.data.get("message")
        session_id = request.data.get("session_id")

        # ⚡ Créer nouvelle session si aucune ID n'est envoyée
        if not session_id:
            session_id = str(uuid.uuid4())
            session = ConversationSession.objects.create(
                session_id=session_id,
                owner=etudiant
            )
        else:
            session, _ = ConversationSession.objects.get_or_create(
                session_id=session_id,
                owner=etudiant
            )

        # ⚡ Mettre un titre automatique si c'est le premier message
        if session.title == "Nouvelle discussion":
            session.title = user_message[:40]
            session.save()

        # ⚡ Sauvegarde du message utilisateur
        MessageAI.objects.create(
            session=session,
            sender="user",
            content=user_message
        )

        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            # Récupérer l'historique
            history = MessageAI.objects.filter(session=session).order_by("timestamp")
            messages = [
                {"role": "user" if m.sender == "user" else "assistant", "content": m.content}
                for m in history
            ]

            # Appel modèle OpenAI
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "Tu es un assistant utile."}, *messages]
            )
            bot_reply = response.choices[0].message.content

            # Sauvegarde réponse IA
            MessageAI.objects.create(
                session=session,
                sender="assistant",
                content=bot_reply
            )

            return Response({
                "reply": bot_reply,
                "session_id": session.session_id,
                "title": session.title,
            })

        except Exception as e:
            print("❌ ERREUR OPENAI :", e)
            return Response({"error": str(e)}, status=500)


# -----------------------
# 🔵 LISTE SESSIONS (historique)
# -----------------------
class ChatSessionsView(APIView):
    def get(self, request):
        user = request.user
        if not hasattr(user, "etudiant"):
            return Response({"error": "Utilisateur non autorisé"}, status=403)

        etudiant = user.etudiant
        sessions = ConversationSession.objects.filter(owner=etudiant).order_by("-created_at")
        data = [
            {
                "session_id": s.session_id,
                "title": s.title,
                "messages": s.messages.count()
            }
            for s in sessions
        ]
        return Response(data)


# -----------------------
# 🔵 LISTE DES MESSAGES d’une session
# -----------------------
class ChatMessagesView(APIView):
    def get(self, request, session_id):
        user = request.user
        if not hasattr(user, "etudiant"):
            return Response({"error": "Utilisateur non autorisé"}, status=403)

        etudiant = user.etudiant
        try:
            session = ConversationSession.objects.get(session_id=session_id, owner=etudiant)
        except ConversationSession.DoesNotExist:
            return Response({"error": "Session introuvable"}, status=404)

        messages = session.messages.order_by("timestamp")
        return Response([
            {
                "id": m.id,
                "sender": m.sender,
                "content": m.content,
            }
            for m in messages
        ])
# views.py
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ConversationSession

class ChatSessionDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, session_id, *args, **kwargs):
        user = request.user
        if not hasattr(user, "etudiant"):
            return Response({"error": "Utilisateur non autorisé"}, status=403)

        try:
            session = ConversationSession.objects.get(session_id=session_id, owner=user.etudiant)
            session.delete()
            return Response({"detail": "Session supprimée."}, status=status.HTTP_200_OK)
        except ConversationSession.DoesNotExist:
            return Response({"error": "Session introuvable."}, status=status.HTTP_404_NOT_FOUND)
