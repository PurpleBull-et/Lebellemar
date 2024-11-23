from django.urls import path, include
from .views import *
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', index, name='index'),
    path('hospedaje/', hospedaje, name='hospedaje'),
    path('solicitud/', solicitud, name='solicitud'),
    #registro
    path('registro/', registro, name='registro'),
    path('accounts/login/', login, name='login'),
    path('accounts/logout/', logoutView, name='logout'),
    # reseteo contraseña
    path('accounts/', include('django.contrib.auth.urls')),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    #habitaciones
    
    path('habitacion_detalle/<habitacion_id>/', habitacion_detalle, name='habitacion_detalle'),
    path('get_reservas_habitacion/<habitacion_id>/', get_reservas_habitacion, name='get_reservas_habitacion'),
    path('list_room/', list_room, name='list_room'),
    path('add_room/', add_room, name='add_room'),
    path('mod_room/<habitacion_id>/', mod_room, name='mod_room'),
    path('erase_room/<habitacion_id>/', erase_room, name='erase_room'),
    path('add_image_to_room/', add_image_to_room, name='add_image_to_room'),
    #usuarios
    path('add_user/', add_user, name='add_user'),
    path('list_user/', list_user, name='list_user'),
    path('erase_user/<user_id>/', erase_user, name='erase_user'),
    path('mod_user/<user_id>/', mod_user, name='mod_user'),
    #perfil de usuarios
    path('perfil/', perfil, name='perfil'),
    path('mod_perfil/', mod_perfil, name='mod_perfil'),
    #gest. de solicitud
    path('list_soli/', list_soli, name='list_soli'),
    path('mod_soli/<solicitud_id>/', mod_soli, name='mod_soli'),
    #solicitud usuario
    path('my_soli/', my_soli, name='my_soli'),
    path('my_soli_det/<solicitud_id>/', my_soli_det, name='my_soli_det'),
    path('my_room/', my_room, name='my_room'),
    path('my_room_det/<reserva_id>/', my_room_det, name='my_room_det'),
    path('cancelar_reserva/<reserva_id>/', cancelar_reserva, name='cancelar_reserva'),
    path('confirmar_entrega/<int:reserva_id>/', confirmar_entrega, name='confirmar_entrega'),
    path('opinion_form/<int:reserva_id>/', opinion_form, name='opinion_form'),
    path('habitacion_detalle/<int:habitacion_id>/', habitacion_detalle, name='habitacion_detalle'),
    path('pago/iniciar/<int:reserva_id>/', iniciar_pago, name='iniciar_pago'),
    path('pago/completado/', pago_completado, name='pago_completado'),
    # reportes 
    path('reporte/', mostrar_reporte, name='reporte'),
    path('reporte/pdf/', generar_reporte, name='generar_pdf_reporte'),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)