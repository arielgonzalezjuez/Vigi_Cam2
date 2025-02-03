from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('cctv/', views.cctv, name='cctv'),
    path('company/', views.company, name='company'),
    path('testimonial/', views.testimonial, name='testimonial'),
    path('cameras/', views.cameras, name='cameras'),
    path('login/', views.inicio_sesion, name='login'),
    path('cerrar-session/',views.cerrarSession, name='cerrarSession'),
    path('lista_personas/', views.lista_personas, name='lista_personas'),
    path('registrar/', views.registrar_persona, name='registrar_persona'),
    path('editar/<int:id_persona>/', views.editar_persona, name='editar_persona'),
    path('eliminar/<int:id_persona>/', views.eliminar_persona, name='eliminar_persona'),
    path('registrarCamara/', views.registrar_camara, name='registrar_camara'),
    path('reconocimiento/', views.reconocimiento_facial, name='reconocimiento_facial'),
    path('capturavideo/', views.video_feed, name='capturavideo'),
    path('eliminarregistro/', views.eliminarregistros, name='eliminarregistro'),
    path('vervideos/', views.video_list, name='vervideos'),
    path('video/eliminar/<int:video_id>/', views.eliminar_video, name='eliminar_video'),
]