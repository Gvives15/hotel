from ninja import Router, Schema
from ninja.errors import HttpError
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
from typing import Optional
from .models import EmailLog
from app.bookings.models import Booking
from app.clients.models import Client
from .services import EmailService
from app.administration.models import Hotel, SUB_TRIAL, SUB_ACTIVE
from django.utils import timezone
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.db.models import Count, Sum, Q
from decimal import Decimal

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

@router.get("/superadmin/kpis", tags=["Superadmin"])
def superadmin_kpis(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated or not request.user.is_superuser:
        raise HttpError(403, "Forbidden")
    today = timezone.now().date()
    total_rooms = 0
    try:
        from app.rooms.models import Room
        total_rooms = Room.objects.count()
    except Exception:
        total_rooms = 0
    occupied_rooms = Booking.objects.filter(
        status="confirmed",
        check_in_date__lte=today,
        check_out_date__gte=today,
    ).values("room").distinct().count()
    occupancy_rate = float(occupied_rooms / total_rooms) if total_rooms > 0 else 0.0
    active_bookings = Booking.objects.filter(
        status="confirmed",
        check_in_date__lte=today,
        check_out_date__gte=today,
    ).count()
    agg = Booking.objects.filter(
        status="confirmed",
        check_in_date=today,
    ).aggregate(total=Sum("total_price"))
    estimated_revenue_today = agg.get("total") or Decimal("0")
    active_hotels = Hotel.objects.filter(
        subscription_status__in=[SUB_TRIAL, SUB_ACTIVE],
        is_blocked=False,
    ).count()
    return {
        "date": today,
        "occupancy_rate": round(occupancy_rate, 4),
        "active_bookings": active_bookings,
        "estimated_revenue_today": str(estimated_revenue_today),
        "active_hotels": active_hotels,
    }

@router.get("/superadmin/chart", tags=["Superadmin"])
def superadmin_chart(request, metric: str = "bookings", interval: str = "week", start_date: Optional[str] = None, end_date: Optional[str] = None):
    if not getattr(request, "user", None) or not request.user.is_authenticated or not request.user.is_superuser:
        raise HttpError(403, "Forbidden")
    today = timezone.now().date()
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except Exception:
            end = today
    else:
        end = today
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        except Exception:
            start = end - timedelta(days=84)
    else:
        start = end - timedelta(days=84)
    qs = Booking.objects.filter(check_in_date__gte=start, check_in_date__lte=end)
    if interval == "month":
        grp = TruncMonth("check_in_date")
    elif interval == "day":
        grp = TruncDate("check_in_date")
    else:
        grp = TruncWeek("check_in_date")
    if metric == "revenue":
        data = (
            qs.filter(status="confirmed")
            .annotate(p=grp)
            .values("p")
            .annotate(value=Sum("total_price"))
            .order_by("p")
        )
    else:
        data = (
            qs.annotate(p=grp)
            .values("p")
            .annotate(value=Count("id"))
            .order_by("p")
        )
    return {"series": [{"period": d["p"], "value": d["value"]} for d in data]}

@router.get("/superadmin/hotels", tags=["Superadmin"])
def superadmin_hotels(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated or not request.user.is_superuser:
        raise HttpError(403, "Forbidden")
    today = timezone.now().date()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)
    hotels = Hotel.objects.all().order_by("name")
    results = []
    for h in hotels:
        week_count = Booking.objects.filter(
            hotel=h,
            check_in_date__gte=start_week,
            check_in_date__lte=end_week,
        ).count()
        bookings_today = Booking.objects.filter(
            hotel=h,
            status="confirmed",
            check_in_date__lte=today,
            check_out_date__gte=today,
        ).count()
        results.append({
            "id": h.id,
            "name": h.name,
            "slug": h.slug,
            "plan_name": h.plan_name,
            "subscription_status": h.subscription_status,
            "is_blocked": h.is_blocked,
            "bookings_this_week": week_count,
            "bookings_today": bookings_today,
        })
    return {"hotels": results}