from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import CashMachineView

urlpatterns = [
    path("cash_machine", CashMachineView.as_view()),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
