from django.http import JsonResponse
from django.views.decorators.http import require_GET
from apps.mesas.models import Mesa


@require_GET
def get_mesa_qr(request, mesa_id):
    """
    Endpoint API que devuelve el QR base64 de una mesa.
    Uso: GET /api/mesas/{mesa_id}/qr/
    Respuesta: { "qr_base64": "data:image/png;base64,iVBORw0KG..." }
    """
    try:
        mesa = Mesa.objects.get(pk=mesa_id)
        base_url = request.build_absolute_uri('/').rstrip('/')
        qr_base64 = mesa.generate_qr_base64(base_url=base_url)
        return JsonResponse({
            'id': mesa.id,
            'numero_mesa': mesa.numero_mesa,
            'qr_base64': f'data:image/png;base64,{qr_base64}',
            'qr_url': mesa.get_qr_url(),
        })
    except Mesa.DoesNotExist:
        return JsonResponse({'error': 'Mesa no encontrada'}, status=404)
