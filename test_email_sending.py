import os
import django
from django.core.mail import send_mail
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xcsm_project.settings')
django.setup()

def test_emails():
    print("📧 Test d'envoi d'emails en cours...")
    
    recipients = [
        'pafedilane@gmail.com', 
        'nzungangf@gmail.com', 
        'jordanowona@icloud.com'
    ]
    
    subject = "Test de Notification XCSM v2.0"
    message = """
    Bonjour,
    
    Ceci est un email de test envoyé depuis le backend XCSM (Extraction et Consultation Sémantique de Documents).
    
    Si vous recevez ce message, cela confirme que le module de notification SMTP est correctement configuré et opérationnel.
    
    Cordialement,
    L'équipe XCSM (Bot Antigravity)
    """
    
    sender = settings.DEFAULT_FROM_EMAIL
    
    print(f"Expéditeur : {sender}")
    print(f"Destinataires : {', '.join(recipients)}")
    
    try:
        # Envoi groupé (ou individuel pour ne pas dévoiler les autres adresses si on voulait, mais ici send_mail met tout le monde en TO ou BCC selon l'usage, ici recipient_list est en TO)
        # Pour un test propre, on peut boucler ou envoyer en une fois. send_mail envoie à la liste.
        count = send_mail(
            subject,
            message,
            sender,
            recipients,
            fail_silently=False,
        )
        print(f"✅ Succès ! {count} email(s) envoyé(s).")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi : {str(e)}")
        print("Vérifiez vos paramètres SMTP dans le fichier .env (EMAIL_HOST_USER, EMAIL_HOST_PASSWORD instable ou blocage Google).")

if __name__ == "__main__":
    test_emails()
