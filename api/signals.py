from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Cours, Notification, Etudiant

@receiver(post_save, sender=Cours)
def create_notifications_for_students(sender, instance, created, **kwargs):
    if created:
        etudiants = Etudiant.objects.filter(mention=instance.mention, niveau=instance.niveau)
        for etu in etudiants:
            Notification.objects.create(
                etudiant=etu,
                cours=instance,
                message=f"Nouveau cours ajouté : {instance.titre} par {instance.professeur.compte.username}"
            )
