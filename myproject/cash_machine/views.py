import pdfkit
import qrcode
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Item


class CashMachineView(APIView):
    def post(self, request):
        item_ids = request.data.get("items", [])

        try:
            Item.objects.filter(id__in=item_ids)
            selected_items = {}
            total_price = 0

            for item_id in item_ids:
                if item_id in selected_items:
                    selected_items[item_id]["quantity"] += 1
                else:
                    selected_items[item_id] = {
                        "item": Item.objects.get(id=item_id),
                        "quantity": 1,
                    }

            check_items = []
            for item_id, data in selected_items.items():
                item = data["item"]
                quantity = data["quantity"]
                check_item = {
                    "title": item.title,
                    "quantity": quantity,
                    "price": item.price,
                    "total_price": item.price * quantity,
                }
                total_price += check_item["total_price"]
                check_items.append(check_item)

            UTC_time = timezone.now()
            current_time = timezone.localtime(UTC_time).strftime("%d.%m.%Y %H:%M")

            context = {
                "items": check_items,
                "total_price": total_price,
                "current_date": current_time,
            }

            html_content = render_to_string("check_template.html", context)

            options = {
                "page-size": "A4",
                "encoding": "UTF-8",
            }
            pdf_file = pdfkit.from_string(html_content, False, options=options)

            pdf_name = f"check{UTC_time.strftime('%Y%m%d%H%M%S')}.pdf"
            path = f"{settings.MEDIA_ROOT}/{pdf_name}"
            with open(path, "wb") as f:
                f.write(pdf_file)

            file_url = request.build_absolute_uri(settings.MEDIA_URL + pdf_name)
            # print(file_url)

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(file_url)
            qr.make(fit=True)

            qr_img = qr.make_image(fill_color="black", back_color="white")

            qr_name = f"qr_code_{UTC_time.strftime('%Y%m%d%H%M%S')}.png"
            qr_path = f"{settings.MEDIA_ROOT}/{qr_name}"
            qr_img.save(qr_path)

            with open(qr_path, "rb") as qr_file:
                response = HttpResponse(qr_file.read(), content_type="image/png")
                response["Content-Disposition"] = f'attachment; filename="{qr_name}"'
            return response

        except Item.DoesNotExist:
            return Response(
                {"error": "One or more items not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
