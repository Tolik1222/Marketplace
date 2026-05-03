from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SupportMessageForm, SupportTicketCreateForm
from .models import SupportMessage, SupportTicket


def _can_access_ticket(user, ticket):
    return user.is_staff or ticket.user_id == user.id


@login_required
def ticket_list(request):
    tickets = SupportTicket.objects.all() if request.user.is_staff else SupportTicket.objects.filter(user=request.user)
    status_filter = request.GET.get("status", "all")
    if status_filter in {SupportTicket.STATUS_OPEN, SupportTicket.STATUS_ANSWERED, SupportTicket.STATUS_CLOSED}:
        tickets = tickets.filter(status=status_filter)

    return render(
        request,
        "support/ticket_list.html",
        {"tickets": tickets, "status_filter": status_filter},
    )


@login_required
def ticket_create(request):
    if request.method == "POST":
        form = SupportTicketCreateForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            SupportMessage.objects.create(
                ticket=ticket,
                author=request.user,
                message=form.cleaned_data["message"],
                is_staff_reply=False,
            )
            messages.success(request, "Тікет створено. Підтримка скоро відповість.")
            return redirect("support:ticket_detail", ticket_id=ticket.id)
    else:
        form = SupportTicketCreateForm()

    return render(request, "support/ticket_create.html", {"form": form})


@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    if not _can_access_ticket(request.user, ticket):
        return HttpResponseForbidden("Немає доступу до цього тікета.")

    if request.method == "POST":
        form = SupportMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.ticket = ticket
            msg.author = request.user
            msg.is_staff_reply = request.user.is_staff
            msg.save()

            if request.user.is_staff:
                ticket.status = SupportTicket.STATUS_ANSWERED
            elif ticket.status == SupportTicket.STATUS_CLOSED:
                ticket.status = SupportTicket.STATUS_OPEN
            ticket.save(update_fields=["status", "updated_at"])

            return redirect("support:ticket_detail", ticket_id=ticket.id)
    else:
        form = SupportMessageForm()

    return render(
        request,
        "support/ticket_detail.html",
        {"ticket": ticket, "form": form},
    )


@login_required
@user_passes_test(lambda u: u.is_staff)
def ticket_update_status(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    status = request.POST.get("status")
    valid_statuses = {
        SupportTicket.STATUS_OPEN,
        SupportTicket.STATUS_ANSWERED,
        SupportTicket.STATUS_CLOSED,
    }
    if status in valid_statuses:
        ticket.status = status
        ticket.save(update_fields=["status", "updated_at"])
    return redirect("support:ticket_detail", ticket_id=ticket.id)


@login_required
def ticket_messages_api(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    if not _can_access_ticket(request.user, ticket):
        return HttpResponseForbidden("Немає доступу до цього тікета.")

    payload = {
        "messages": [
            {
                "author": "Підтримка" if msg.is_staff_reply else msg.author.username,
                "is_staff_reply": msg.is_staff_reply,
                "message": msg.message,
                "created_at": msg.created_at.strftime("%d.%m.%Y %H:%M"),
            }
            for msg in ticket.messages.select_related("author").all()
        ]
    }
    return JsonResponse(payload)
