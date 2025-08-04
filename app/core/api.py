from ninja import Router, Schema
from ninja.errors import HttpError
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime
from typing import Optional
from .models import EmailLog
from app.bookings.models import Booking
from app.clients.models import Client
from .services import EmailService

router = Router()

# Schemas para la API
class SendEmailRequest(Schema):
    reserva_id: int

class SendWelcomeEmailRequest(Schema):
    client_id: int

class SendEmailResponse(Schema):
    success: bool
    message: str
    email_log_id: Optional[int] = None
    recipient_email: Optional[str] = None
    subject: Optional[str] = None

@router.post("/manda_email_cliente/", response=SendEmailResponse, tags=["Emails"])
def send_email_to_client(request, payload: SendEmailRequest):
    """
    Envía un email de confirmación al cliente de una reserva específica.
    
    Args:
        payload: Datos de la reserva
        
    Returns:
        Estado del envío del email
    """
    result = EmailService.send_booking_confirmation(payload.reserva_id)
    
    if result["success"]:
        return result
    else:
        raise HttpError(500, result["message"])

@router.post("/manda_email_bienvenida/", response=SendEmailResponse, tags=["Emails"])
def send_welcome_email(request, payload: SendWelcomeEmailRequest):
    """
    Envía un email de bienvenida a un nuevo cliente.
    
    Args:
        payload: Datos del cliente
        
    Returns:
        Estado del envío del email
    """
    result = EmailService.send_welcome_email(payload.client_id)
    
    if result["success"]:
        return result
    else:
        raise HttpError(500, result["message"])

@router.get("/emails/", tags=["Emails"])
def get_email_logs(request):
    """
    Obtiene el historial de emails enviados
    """
    from django.core.paginator import Paginator
    
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    
    emails = EmailLog.objects.all().order_by('-created_at')
    paginator = Paginator(emails, per_page)
    
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)
    
    return {
        "emails": [
            {
                "id": email.id,
                "recipient_email": email.recipient_email,
                "recipient_name": email.recipient_name,
                "subject": email.subject,
                "status": email.status,
                "sent_at": email.sent_at,
                "created_at": email.created_at,
                "error_message": email.error_message
            }
            for email in page_obj
        ],
        "total_pages": paginator.num_pages,
        "current_page": page_obj.number,
        "total_count": paginator.count
    } 