from django.db import models
from django.contrib.auth.models import AbstractUser

# ------------------ Compte ------------------
class Compte(AbstractUser):
    email=models.EmailField(unique=True)
    ROLE_CHOICES = (
        ('etudiant', 'Etudiant'),
        ('professeur', 'Professeur'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    photo =models.ImageField(upload_to='profils/',blank=True,null=True)
    USERNAME_FIELD="email"
    REQUIRED_FIELDS=["username"]
    def __str__(self):
        return f"{self.username} ({self.role})"

# ------------------ Mention ------------------
class Mention(models.Model):
    nom = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nom

# ------------------ Niveau ------------------
class Niveau(models.Model):
    nom = models.CharField(max_length=100)
    mention = models.ForeignKey(Mention, on_delete=models.CASCADE, related_name='niveaux')

    class Meta:
        unique_together = ('nom', 'mention')

    def __str__(self):
        return f"{self.nom} ({self.mention.nom})"

# ------------------ Etudiant ------------------
class Etudiant(models.Model):
    compte = models.OneToOneField(Compte, on_delete=models.CASCADE, related_name='etudiant')
    niveau = models.ForeignKey(Niveau, on_delete=models.SET_NULL, null=True)
    mention = models.ForeignKey(Mention, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.compte.first_name} {self.compte.last_name}"

# ------------------ Professeur ------------------
class Professeur(models.Model):
    compte = models.OneToOneField(Compte, on_delete=models.CASCADE, related_name='professeur')
    specialite = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.compte.first_name} {self.compte.last_name}"

# ------------------ Cours ------------------
class Cours(models.Model):
    titre = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    professeur = models.ForeignKey(Professeur, on_delete=models.CASCADE, related_name='cours')
    mention = models.ForeignKey(Mention, on_delete=models.CASCADE, related_name='cours')
    niveau = models.ForeignKey(Niveau, on_delete=models.CASCADE, related_name='cours')
    etudiants = models.ManyToManyField(Etudiant, related_name='cours', blank=True)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    fichier = models.FileField(upload_to="cours_pdfs/", blank=True, null=True)

    def __str__(self):
        return f"{self.titre} - {self.mention.nom} - {self.niveau.nom}"

# ------------------ Notification ------------------
class Notification(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='notifications')
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    lu = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification pour {self.etudiant.compte.username} - {self.cours.titre}"
# ------------------ Favori ------------------
class Favori(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='favoris')
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name='favoris')
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('etudiant', 'cours')  # empêche les doublons

    def __str__(self):
        return f"{self.etudiant.compte.username} - {self.cours.titre}"
    
class ConversationSession(models.Model):
    session_id = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255, blank=True, default="Nouvelle discussion")
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name="sessions")


class MessageAI(models.Model):
    session = models.ForeignKey(ConversationSession, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=10)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.session.session_id} - {self.sender}: {self.content[:30]}"
