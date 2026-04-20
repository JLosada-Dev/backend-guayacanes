from django.db.models.signals import post_save
from django.dispatch import receiver, Signal

# Signal personalizada que veeduría emite al crear una denuncia
# auditoria escucha esta signal — nunca importa directamente de veeduria
complaint_created = Signal()


from .models import Complaint


@receiver(post_save, sender=Complaint)
def on_complaint_saved(sender, instance, created, **kwargs):
    """
    Emite complaint_created solo en creación, no en updates.
    Auditoría escucha esta signal en receivers.py.
    """
    if created:
        complaint_created.send(
            sender=Complaint,
            complaint_id=instance.id,
            service_slug=instance.service_slug,
            location=instance.location,
            created_at=instance.created_at,
            location_source=instance.location_source,
            commune_id=instance.commune_id,
        )
