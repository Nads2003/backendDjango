from django.urls import path
from .views import CreerCompter,ChatAIView,ChatSessionsView, FavoriDeleteView,ChatSessionDeleteView,ChatMessagesView,CompteTokenObtainPairView,MesCoursView,GenerateQuizIAFree,MentionListView, NiveauListView, ProfesseurListView, CoursListCreateView,media_pdf_view,FavoriCreateView, FavoriListView
from django.conf import settings
from django.conf.urls.static import static
urlpatterns=[
   path("ai/chat/", ChatAIView.as_view(), name="ai-chat"),
    path("ai/sessions/", ChatSessionsView.as_view()),
    path("ai/messages/<str:session_id>/", ChatMessagesView.as_view()),
  path("ai/sessions/<str:session_id>/delete/", ChatSessionDeleteView.as_view(), name="chat-session-delete"),
    path('creercompte/',CreerCompter.as_view(),name='creer'),
    path('login/',CompteTokenObtainPairView.as_view(),name='login'),
    path('mes-cours/', MesCoursView.as_view(), name='mes-cours'),
    path('mentions/', MentionListView.as_view(), name='mentions-list'),
    path('niveaux/', NiveauListView.as_view(), name='niveaux-list'),
    path('professeurs/', ProfesseurListView.as_view(), name='professeurs-list'),
    path('cours/', CoursListCreateView.as_view(), name='cours-list-create'),
    path('pdf/<int:pk>/', media_pdf_view, name='media-pdf'),
    path('favoris/', FavoriListView.as_view(), name='favoris-list'),
    path('favori/<int:cours_id>/', FavoriDeleteView.as_view(), name="favori-delete"),
    path('favori/', FavoriCreateView.as_view(), name='favori-create'),
 path("generate-quiz-ia-free/", GenerateQuizIAFree.as_view(), name="generate-quiz-ia-free"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)