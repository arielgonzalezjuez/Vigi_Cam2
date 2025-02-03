from django.shortcuts import render, redirect, get_object_or_404
from .models import Persona, RegistroAcceso, Camara, Video
from .forms import PersonaForm, CamaraForm, ClienteRegistrarForm, ClienteActualizarForm
from django.http import HttpResponse, StreamingHttpResponse
import numpy as np
from django.core.files.base import ContentFile
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
import cv2
from datetime import datetime
from django.conf import settings
from django.utils import timezone
import os
from django.conf import settings
from django.views.decorators import gzip

def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def cctv(request):
    return render(request, 'cctv.html')

def company(request):
    return render(request, 'company.html')

def testimonial(request):
    return render(request, 'testimonial.html')

def cameras(request):
    return render(request, 'cameras.html')

def inicio_sesion(request):
    if request.method == 'GET':
        return render(request, 'login.html', {'form':AuthenticationForm})
    else:
        cliente = authenticate(request,username=request.POST['username'], password=request.POST['password'])
        if cliente is None:
            return render(request, 'login.html', {'form':AuthenticationForm, 'error':'Usuario o contraseña incorrectos'})
        else:
            login(request,cliente)
            return redirect('index')
        
@login_required
def cerrarSession(request):
    logout(request) 
    return redirect('index')

# Vista para manejar la lista de personas y el registro de cámaras
@login_required
def lista_personas(request):
    personas = Persona.objects.all()
    return render(request, 'lista_persona.html', {'personas': personas})

@login_required
def registrar_persona(request):
    title = 'Registrar Persona'
    if request.method == 'POST':
        form = PersonaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('lista_personas')
    else:
        form = PersonaForm()
    return render(request, 'registrar_persona.html', {'form': form, 'title': title})

@login_required
def editar_persona(request, id_persona):
    title = 'Editar Persona'
    persona = get_object_or_404(Persona, pk=id_persona)
    if request.method == 'POST':
        form = PersonaForm(request.POST, request.FILES, instance=persona)
        if form.is_valid():
            form.save()
            return redirect('lista_personas')
    else:
        form = PersonaForm(instance=persona)
    return render(request, 'registrar_persona.html', {'form': form, 'persona': persona, 'title': title})

@login_required
def eliminar_persona(request, id_persona):
    persona = get_object_or_404(Persona, pk=id_persona)
    persona.delete()
    return redirect('lista_personas')

# Función para iniciar la captura y el reconocimiento facial desde una cámara ONVIF
@login_required
def registrar_camara(request):
    if request.method == 'POST':
        formC = CamaraForm(request.POST)
        if formC.is_valid():
            formC.save()
            return redirect('reconocimiento_facial')
    else:
        formC = CamaraForm()
    return render(request, 'registrar_camara.html', {'formC': formC})

@login_required
def reconocimiento_facial(request):
     registros = RegistroAcceso.objects.all().order_by('-fecha_hora')
     cameras = Camara.objects.all()
     return render(request, 'reconocimiento.html', {'camaras': cameras,'registros': registros})

@login_required
def eliminarregistros(request):
     RegistroAcceso.objects.all().delete()
     return redirect('reconocimiento_facial')

# @login_required
# def vervideoscapturdos(request):
#      viedos_folder = os.path.join(settings.MEDIA_ROOT, 'videos_capturados')
    
#      videos = [f for f in os.listdir(viedos_folder) if f.endswith(('.mp4','.avi','.mov'))]
    
#      viedos_urls = [os.path.join(settings.MEDIA_URL, 'videos_capturados',video) for video in videos]
     
#      return render(request,'vervideos.html',{'videos':viedos_urls})



# mi_app/views.py

import os
from django.conf import settings
from django.shortcuts import render

# def video_list(request):
#     videos_dir = os.path.join(settings.MEDIA_ROOT, 'videos_capturados')
#     videos = [f for f in os.listdir(videos_dir) if f.endswith('.mp4')]
#     videos_urls = [f"{settings.MEDIA_URL}videos_capturados/{video}" for video in videos]
#     return render(request, 'video_list.html', {'videos_urls': videos_urls})

def video_list(request):
    # Obtener todos los videos de la base de datos
    videos = Video.objects.all()
    return render(request, 'video_list.html', {'videos': videos})

from django.shortcuts import get_object_or_404, redirect
from .models import Video
import os

def eliminar_video(request, video_id):
    # Obtener el video de la base de datos
    video = get_object_or_404(Video, id=video_id)

    # Eliminar el archivo del sistema
    archivo_video = os.path.join(settings.MEDIA_ROOT, video.file.name)
    if os.path.exists(archivo_video):
        os.remove(archivo_video)

    # Eliminar el registro en la base de datos
    video.delete()

    return redirect('vervideos')

import cv2
import os
from django.http import StreamingHttpResponse
from django.shortcuts import render
from django.conf import settings
import time
from .models import Persona, RegistroAcceso, Video
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

# Ruta del clasificador Haar
face_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(face_cascade_path)

# Cargar imágenes de referencia conocidas y calcular histogramas
referencias_rostros = []
nombres_rostros = []

# Cargar los rostros desde la base de datos
personas = Persona.objects.all()

# Función para guardar la imagen del rostro capturado
def save_face_image(face_img):
    filename = f"captura_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
    folder = os.path.join('imagenes_capturadas')
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)
    cv2.imwrite(filepath, face_img)
    return filepath

for persona in personas:
    if persona.imagen:  # Verificar que exista imagen cargada
        ruta_imagen = os.path.join(settings.MEDIA_ROOT, str(persona.imagen))
        img = cv2.imread(ruta_imagen)
        if img is not None:
            gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            rostros = face_cascade.detectMultiScale(gris, scaleFactor=1.1, minNeighbors=5)
            if len(rostros) > 0:
                (x, y, w, h) = rostros[0]
                rostro_conocido = gris[y:y + h, x:x + w]
                histograma_rostro = cv2.calcHist([rostro_conocido], [0], None, [256], [0, 256])
                referencias_rostros.append(histograma_rostro)
                nombres_rostros.append(persona.nombre)

# Captura de video
cap = cv2.VideoCapture(0)

# Generador de frames para el streaming
def gen():
    # Crear el archivo de video donde se guardarán los frames capturados
    nombre_video = f"video_{str(int(time.time()))}.mp4"
    ruta_video = os.path.join(settings.MEDIA_ROOT, 'videos_capturados', nombre_video)
    os.makedirs(os.path.dirname(ruta_video), exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    out = cv2.VideoWriter(ruta_video, fourcc, 20.0, (frame_width, frame_height))

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rostros_detectados = face_cascade.detectMultiScale(gris, scaleFactor=1.1, minNeighbors=5)

            for (x, y, w, h) in rostros_detectados:
                rostro_actual = gris[y:y + h, x:x + w]
                histograma_actual = cv2.calcHist([rostro_actual], [0], None, [256], [0, 256])

                nombre = "Desconocido"
                color_rectangulo = (0, 0, 255)  # Rojo para desconocido

                # Comparación mediante histogramas
                for idx, histograma_conocido in enumerate(referencias_rostros):
                    similitud = cv2.compareHist(histograma_conocido, histograma_actual, cv2.HISTCMP_CORREL)

                    if similitud > 0.7:  # Ajustar umbral si es necesario
                        nombre = nombres_rostros[idx]
                        color_rectangulo = (0, 255, 0)  # Verde para conocido
                    #     imagen_nombre = f"rostro_conocido_{str(int(time.time()))}.jpg"
                    #     imagen_path = os.path.join(settings.MEDIA_ROOT, 'imagenes_capturadas', imagen_nombre)

                    # # Guardar la imagen en el sistema de archivos
                    #     default_storage.save(imagen_path, ContentFile(img_bytes.tobytes()))

                    # # Crear la instancia de RegistroAcceso con la imagen guardada
                    #     imagen_guardada = f'imagenes_capturadas/{imagen_nombre}' 
                        # Guardar registro en la base de datos
                        persona = Persona.objects.get(nombre=nombre)
                        RegistroAcceso.objects.create(persona=persona)
                        break

                # Si es desconocido, capturar la imagen del rostro y guardarla
                if nombre == "Desconocido":
                    rostro_desconocido = frame[y:y+h, x:x+w]
                    _, img_bytes = cv2.imencode('.jpg', rostro_desconocido)  # Convertir el rostro a JPEG

                    # Crear un nombre único para la imagen capturada
                    imagen_nombre = f"rostro_desconocido_{str(int(time.time()))}.jpg"
                    imagen_path = os.path.join(settings.MEDIA_ROOT, 'imagenes_capturadas', imagen_nombre)

                    # Guardar la imagen en el sistema de archivos
                    default_storage.save(imagen_path, ContentFile(img_bytes.tobytes()))

                    # Crear la instancia de RegistroAcceso con la imagen guardada
                    imagen_guardada = f'imagenes_capturadas/{imagen_nombre}'  # Ruta relativa para la imagen
                    # Asegúrate de usar el archivo correctamente asociado al campo ImageField
                    RegistroAcceso.objects.create(imagen_capturada=imagen_guardada)

                # Dibujar rectángulo y nombre
                cv2.rectangle(frame, (x, y), (x + w, y + h), color_rectangulo, 2)
                cv2.putText(frame, nombre, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color_rectangulo, 2)

            # Codificar el frame como JPEG para el streaming
            ret, jpeg = cv2.imencode('.jpg', frame)
            if not ret:
                break

            # Guardar el frame en el archivo de video
            out.write(frame)

            # Convertir el frame en un formato adecuado para HTTP
            frame = jpeg.tobytes()

            # Usamos un generador para enviar los frames
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
    except GeneratorExit:
        # El cliente cerró la conexión, por lo que detenemos el generador
        print("El cliente cerró la conexión. Deteniendo el streaming.")
    finally:
        # Una vez terminado el streaming, cerrar el archivo de video
        out.release()
        cap.release()

        # Guardar el video en la base de datos
        video = Video.objects.create(title=nombre_video, file=f'videos_capturados/{nombre_video}')
        video.save()

# Vista para el streaming
def video_feed(request):
    return StreamingHttpResponse(gen(), content_type='multipart/x-mixed-replace; boundary=frame')



# import cv2
# import os
# from django.http import StreamingHttpResponse
# from django.shortcuts import render
# from django.conf import settings
# import time
# from .models import Persona, RegistroAcceso, Video  # Asegúrate de importar tus modelos

# # Ruta del clasificador Haar
# face_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
# face_cascade = cv2.CascadeClassifier(face_cascade_path)

# # Cargar imágenes de referencia conocidas y calcular histogramas
# referencias_rostros = []
# nombres_rostros = []

# # Cargar los rostros desde la base de datos
# personas = Persona.objects.all()

# for persona in personas:
#     if persona.imagen:  # Verificar que exista imagen cargada
#         ruta_imagen = os.path.join(settings.MEDIA_ROOT, str(persona.imagen))
#         img = cv2.imread(ruta_imagen)
#         if img is not None:
#             gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#             rostros = face_cascade.detectMultiScale(gris, scaleFactor=1.1, minNeighbors=5)
#             if len(rostros) > 0:
#                 (x, y, w, h) = rostros[0]
#                 rostro_conocido = gris[y:y + h, x:x + w]
#                 histograma_rostro = cv2.calcHist([rostro_conocido], [0], None, [256], [0, 256])
#                 referencias_rostros.append(histograma_rostro)
#                 nombres_rostros.append(persona.nombre)

# # Captura de video
# cap = cv2.VideoCapture(0)

# # Generador de frames para el streaming
# def gen():
#     # Crear el archivo de video donde se guardarán los frames capturados
#     nombre_video = f"video_{str(int(time.time()))}.avi"
#     ruta_video = os.path.join(settings.MEDIA_ROOT, 'videos_capturados', nombre_video)
#     os.makedirs(os.path.dirname(ruta_video), exist_ok=True)

#     fourcc = cv2.VideoWriter_fourcc(*'XVID')
#     frame_width = int(cap.get(3))
#     frame_height = int(cap.get(4))
#     out = cv2.VideoWriter(ruta_video, fourcc, 20.0, (frame_width, frame_height))

#     try:
#         while True:
#             ret, frame = cap.read()
#             if not ret:
#                 break

#             gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#             rostros_detectados = face_cascade.detectMultiScale(gris, scaleFactor=1.1, minNeighbors=5)

#             for (x, y, w, h) in rostros_detectados:
#                 rostro_actual = gris[y:y + h, x:x + w]
#                 histograma_actual = cv2.calcHist([rostro_actual], [0], None, [256], [0, 256])

#                 nombre = "Desconocido"
#                 color_rectangulo = (0, 0, 255)  # Rojo para desconocido

#                 # Comparación mediante histogramas
#                 for idx, histograma_conocido in enumerate(referencias_rostros):
#                     similitud = cv2.compareHist(histograma_conocido, histograma_actual, cv2.HISTCMP_CORREL)

#                     if similitud > 0.7:  # Ajustar este umbral si es necesario
#                         nombre = nombres_rostros[idx]
#                         color_rectangulo = (0, 255, 0)  # Verde para conocido

#                         # Guardar registro en la base de datos
#                         try:
#                             persona = Persona.objects.get(nombre=nombre)
#                             RegistroAcceso.objects.create(persona=persona)
#                             print(f"Guardando acceso para: {nombre}")  # Depuración
#                         except Persona.DoesNotExist:
#                             print(f"Persona {nombre} no encontrada.")
#                         except Exception as e:
#                             print(f"Error al guardar el registro: {e}")
#                         break

#                 # Dibujar rectángulo y nombre
#                 cv2.rectangle(frame, (x, y), (x + w, y + h), color_rectangulo, 2)
#                 cv2.putText(frame, nombre, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color_rectangulo, 2)

#             # Codificar el frame como JPEG para el streaming
#             ret, jpeg = cv2.imencode('.jpg', frame)
#             if not ret:
#                 break

#             # Guardar el frame en el archivo de video
#             out.write(frame)

#             # Convertir el frame en un formato adecuado para HTTP
#             frame = jpeg.tobytes()

#             # Usamos un generador para enviar los frames
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
#     except GeneratorExit:
#         # El cliente cerró la conexión, por lo que detenemos el generador
#         print("El cliente cerró la conexión. Deteniendo el streaming.")
#     finally:
#         # Una vez terminado el streaming, cerrar el archivo de video
#         out.release()
#         cap.release()

#         # Guardar el video en la base de datos
#         try:
#             video = Video.objects.create(title=nombre_video, file=f'videos_capturados/{nombre_video}')
#             video.save()
#             print(f"Video guardado en la base de datos: {nombre_video}")
#         except Exception as e:
#             print(f"Error al guardar el video: {e}")

# # Vista para el streaming
# def video_feed(request):
#     return StreamingHttpResponse(gen(), content_type='multipart/x-mixed-replace; boundary=frame')




# Vista para mostrar el video en el navegador


# import cv2
# import os
# from datetime import datetime

# # Cargar el clasificador Haar para detección de rostros
# face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Función para guardar la imagen del rostro capturado
# def save_face_image(face_img):
#     filename = f"captura_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
#     folder = os.path.join('imagenes_capturadas')
#     os.makedirs(folder, exist_ok=True)
#     filepath = os.path.join(folder, filename)
#     cv2.imwrite(filepath, face_img)
#     return filepath

# class VideoCamera:
#     def __init__(self):
#         # Cámara local por defecto
#         self.video = cv2.VideoCapture(0)

#     def __del__(self):
#         if self.video.isOpened():
#             self.video.release()

#     def get_frame(self):
#         ret, frame = self.video.read()
#         if not ret:
#             return None

#         # Convertir a escala de grises para la detección
#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
#         # Detectar rostros en el frame
#         faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

#         for (x, y, w, h) in faces:
#             # Dibujar el rectángulo alrededor del rostro detectado
#             cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
#             # Guardar la imagen del rostro detectado
#             face_img = frame[y:y+h, x:x+w]
#             save_face_image(face_img)

#         # Codificar el frame en formato JPEG
#         ret, jpeg = cv2.imencode('.jpg', frame)
#         return jpeg.tobytes()

# def gen(camera):
#     """
#     Generador de frames para el streaming.
#     """
#     while True:
#         frame = camera.get_frame()
#         if frame is None:
#             continue
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

# from django.http import StreamingHttpResponse

# def capturaVideo(request):
#     """
#     Vista que devuelve el streaming del video procesado.
#     """
#     # Crear una instancia de la cámara
#     video_camera = VideoCamera()
    
#     # Retornar el streaming del video
#     return StreamingHttpResponse(gen(video_camera), content_type="multipart/x-mixed-replace; boundary=frame")


# Cargar el clasificador Haar para detección de rostros

# def capturaVideo(request):
#     """
#     Vista que devuelve el streaming del video procesado.
#     """
#     if request.method == "POST":
#         # Obtener el ID de la cámara seleccionada del formulario
#         camara_id = request.POST.get('camara')
#         camara = Camara.objects.get(id=camara_id)

#         # Crear una instancia de la cámara utilizando la IP y el puerto
#         video_camera = VideoCamera(camara)
        
#         Retornar el streaming del video
#         return StreamingHttpResponse(gen(video_camera), content_type="multipart/x-mixed-replace; boundary=frame")

#     else:
#         camaras = Camara.objects.all()
#         return render(request, 'reconocimiento.html', {'camaras': camaras})


# # Función para guardar la imagen del rostro capturado
# def save_face_image(face_img):
#     filename = f"captura_{datetime.now().strftime("%Y-%m-%d %H:%M")}.jpg"
#     folder = os.path.join(settings.MEDIA_ROOT, 'imagenes_capturadas')
#     os.makedirs(folder, exist_ok=True)
#     filepath = os.path.join(folder, filename)
#     cv2.imwrite(filepath, face_img)
#     # Se retorna la ruta relativa para asignar al ImageField
#     return os.path.join('imagenes_capturadas', filename)

# # Cargar el clasificador Haar para detección de rostros
# face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# class VideoCamera:
#     def __init__(self):
#         # Abrir la cámara (0 para la cámara por defecto)
#         self.video = cv2.VideoCapture(0)
#         # Configuración para grabar el video
#         fourcc = cv2.VideoWriter_fourcc(*'XVID')
#         videos_folder = os.path.join(settings.MEDIA_ROOT, 'videos_capturados')
#         os.makedirs(videos_folder, exist_ok=True)
#         video_filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
#         self.video_path = os.path.join(videos_folder, video_filename)
#         # Se asume una resolución 640x480 y 20 FPS (ajustable según la cámara)
#         self.out = cv2.VideoWriter(self.video_path, fourcc, 20.0, (640, 480))
    
#     def __del__(self):
#         if self.video.isOpened():
#             self.video.release()
#         self.out.release()

#     def comparar_histogramas(self, img1, img2):
#         """
#         Compara dos imágenes en escala de grises mediante sus histogramas.
#         Retorna un valor de correlación (mientras mayor, mayor similitud).
#         """
#         hist_img1 = cv2.calcHist([img1], [0], None, [256], [0, 256])
#         hist_img2 = cv2.calcHist([img2], [0], None, [256], [0, 256])
#         cv2.normalize(hist_img1, hist_img1)
#         cv2.normalize(hist_img2, hist_img2)
#         correlacion = cv2.compareHist(hist_img1, hist_img2, cv2.HISTCMP_CORREL)
#         return correlacion

#     def reconocer_persona(self, face_roi):
#         """
#         Compara el rostro detectado (face_roi) con la imagen de cada Persona registrada.
#         Se recorre cada Persona y se toma aquella con mayor similitud (usando un umbral).
#         Retorna una tupla: (persona, score) donde 'persona' es el objeto Persona reconocido o None.
#         """
#         umbral = 0.5  # Valor empírico; ajusta según tus pruebas
#         mejor_score = -1
#         persona_reconocida = None
#         for persona in Persona.objects.all():
#             persona_img_path = persona.imagen.path
#             persona_img = cv2.imread(persona_img_path, cv2.IMREAD_GRAYSCALE)
#             if persona_img is None:
#                 continue
#             # Redimensionar la imagen de la persona para que coincida con el tamaño de face_roi
#             try:
#                 persona_img = cv2.resize(persona_img, (face_roi.shape[1], face_roi.shape[0]))
#             except Exception as e:
#                 continue
#             score = self.comparar_histogramas(face_roi, persona_img)
#             if score > umbral and score > mejor_score:
#                 mejor_score = score
#                 persona_reconocida = persona
#         return persona_reconocida, mejor_score

#     def get_frame(self):
#         ret, frame = self.video.read()
#         if not ret:
#             return None

#         # Escribir el frame en el video de salida
#         self.out.write(frame)
#         # Convertir a escala de grises para la detección y comparación
#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         # Detectar rostros en el frame
#         faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
#         for (x, y, w, h) in faces:
#             face_roi = gray[y:y+h, x:x+w]
#             persona, score = self.reconocer_persona(face_roi)
#             if persona:
#                 label = persona.nombre
#                 color = (0, 255, 0)  # Verde para reconocido
#             else:
#                 label = "Desconocido"
#                 color = (0, 0, 255)  # Rojo para desconocido

#             # Dibujar el rectángulo y la etiqueta en el frame
#             cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
#             cv2.putText(frame, label, (x, y-10),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
#             # Guardar la imagen del rostro detectado y registrar el acceso
#             ruta_capturada = save_face_image(frame[y:y+h, x:x+w])
#             RegistroAcceso.objects.create(
#                 persona=persona,  # Si no se reconoce, persona es None
#                 imagen_capturada=ruta_capturada
#             )
#         # Codificar el frame en formato JPEG
#         ret, jpeg = cv2.imencode('.jpg', frame)
#         return jpeg.tobytes()

# def gen(camera):
#     """
#     Generador de frames para el streaming.
#     """
#     while True:
#         frame = camera.get_frame()
#         if frame is None:
#             continue
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

# @gzip.gzip_page
# def capturaVideo(request):
#     """
#     Vista que devuelve el streaming del video procesado.
#     """
#     return StreamingHttpResponse(gen(VideoCamera()),
#                                  content_type="multipart/x-mixed-replace; boundary=frame")

# @login_required
# def capturaVideo(request):
#     return StreamingHttpResponse(gen_frames(request), content_type='multipart/x-mixed-replace; boundary=frame')
# def gen_frames(request):
#     # Cargar el clasificador de rostros de OpenCV
#     face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

#     # Iniciar la captura de video desde la cámara
#     camera = cv2.VideoCapture(0)

#     while True:
#         success, frame = camera.read()
#         if not success:
#             break
#         else:
#             gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

#             # Detectar rostros en el frame
#             faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

#             # Recorrer los rostros detectados
#             for (x, y, w, h) in faces:
#                 rostro = gray[y:y+h, x:x+w]
#                 reconocido = False

#                 # Comparar el rostro detectado con las imágenes en la base de datos
#                 for persona in Persona.objects.all():
#                     persona_img_path = os.path.join(settings.MEDIA_ROOT, persona.imagen.name)
#                     persona_img = cv2.imread(persona_img_path, cv2.IMREAD_GRAYSCALE)

#                     # Redimensionar la imagen de la persona para que coincida con el tamaño del rostro detectado
#                     persona_img_resized = cv2.resize(persona_img, (w, h))

#                     # Comparar los rostros (esto es un ejemplo básico, puedes usar técnicas más avanzadas)
#                     diferencia = cv2.absdiff(persona_img_resized, rostro)
#                     if diferencia.mean() < 30:  # Umbral de similitud
#                         reconocido = True
#                         cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
#                         cv2.putText(frame, persona.nombre, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
#                         break

#                 if not reconocido:
#                     cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
#                     cv2.putText(frame, 'Desconocido', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

#             # Convertir el frame a formato JPEG
#             ret, buffer = cv2.imencode('.jpg', frame)
#             frame = buffer.tobytes()

#             # Enviar el frame como parte de la respuesta
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
# def gen_frames(request):
#     # Inicializar la cámara
#     captura = cv2.VideoCapture(0)
#     # Clasificador de rostros
#     face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

#     # Cargar las imágenes de las personas y sus nombres
#     personas = Persona.objects.all()

#     # Entrenamiento del modelo de reconocimiento facial
#     recognizer = cv2.face.LBPHFaceRecognizer_create()
#     etiquetas = []
#     rostros = []
#     nombres = {}

#     for idx, persona in enumerate(personas):
#         imagen = cv2.imread(persona.imagen.path)
#         gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
#         rostros_detectados = face_cascade.detectMultiScale(gris, 1.1, 4)
        
#         for (x, y, w, h) in rostros_detectados:
#             rostro_recortado = gris[y:y+h, x:x+w]
#             rostros.append(rostro_recortado)
#             etiquetas.append(idx)
#             nombres[idx] = persona.nombre

#     # Entrenar el modelo
#     recognizer.train(rostros, np.array(etiquetas))

#     # Bucle de captura y transmisión en tiempo real
#     while True:
#         ret, frame = captura.read()
#         if not ret:
#             break

#         gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         rostros = face_cascade.detectMultiScale(gris, scaleFactor=1.1, minNeighbors=5)

#         for (x, y, w, h) in rostros:
#             rostro_recortado = gris[y:y+h, x:x+w]
#             id_prediccion, confianza = recognizer.predict(rostro_recortado)
#             nombre = "Desconocido"
#             color_rectangulo = (0, 0, 255)  # Rojo para desconocidos

#             if confianza < 100:
#                 nombre = nombres.get(id_prediccion, "Desconocido")
#                 color_rectangulo = (0, 255, 0)  # Verde para conocidos

#             # Obtener la fecha y hora actual (con zona horaria si es necesario)
#             hora_actual = timezone.now().replace(second=0)

#             # Si es una persona desconocida
#             if nombre == "Desconocido":
#                 # Registrar el rostro desconocido
#                 imagen_capturada = "ruta_de_imagen_placeholder_o_real.jpg"
#                 registro = RegistroAcceso(persona=None, imagen_capturada=imagen_capturada, fecha_hora=hora_actual)
#                 registro.save()
#             else:
#                 # Si es una persona conocida, registrar con el nombre y fecha
#                 persona_identificada = personas[id_prediccion]
                
#                 # Verificar que no exista un registro para la misma persona a la misma hora
#                 if not RegistroAcceso.objects.filter(persona=persona_identificada, fecha_hora=hora_actual).exists():
#                     # Crear el registro de acceso
#                     imagen_capturada = "ruta_de_imagen_placeholder_o_real.jpg"  # Aquí puedes capturar una imagen real
#                     registro = RegistroAcceso(persona=persona_identificada, imagen_capturada=imagen_capturada, fecha_hora=hora_actual)
#                     registro.save()

#             # Dibujar rectángulo y nombre en el frame
#             cv2.rectangle(frame, (x, y), (x+w, y+h), color_rectangulo, 2)
#             cv2.putText(frame, nombre, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color_rectangulo, 2)

#         # Convertir el frame a JPEG para transmisión
#         ret, buffer = cv2.imencode('.jpg', frame)
#         frame = buffer.tobytes()

#         # Enviar el frame al cliente
#         yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

#     # Liberar la cámara
#     captura.release()
#     cv2.destroyAllWindows()

# def gen_frames(request):
#     # Inicializar la cámara
#     captura = cv2.VideoCapture(0)
#     # Clasificador de rostros
#     face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

#     # Cargar las imágenes de las personas y sus nombres
#     personas = Persona.objects.all()

#     # Entrenamiento del modelo de reconocimiento facial
#     recognizer = cv2.face.LBPHFaceRecognizer_create()
#     etiquetas = []
#     rostros = []
#     nombres = {}

#     for idx, persona in enumerate(personas):
#         imagen = cv2.imread(persona.imagen.path)
#         gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
#         rostros_detectados = face_cascade.detectMultiScale(gris, 1.1, 4)
        
#         for (x, y, w, h) in rostros_detectados:
#             rostro_recortado = gris[y:y+h, x:x+w]
#             rostros.append(rostro_recortado)
#             etiquetas.append(idx)
#             nombres[idx] = persona.nombre

#     # Entrenar el modelo
#     recognizer.train(rostros, np.array(etiquetas))

#     # Bucle de captura y transmisión en tiempo real
#     while True:
#         ret, frame = captura.read()
#         if not ret:
#             break

#         gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         rostros = face_cascade.detectMultiScale(gris, scaleFactor=1.1, minNeighbors=5)

#         for (x, y, w, h) in rostros:
#             rostro_recortado = gris[y:y+h, x:x+w]
#             id_prediccion, confianza = recognizer.predict(rostro_recortado)
#             nombre = "Desconocido"
#             color_rectangulo = (0, 0, 255)  # Rojo para desconocidos

#             if confianza < 100:
#                 nombre = nombres.get(id_prediccion, "Desconocido")
#                 color_rectangulo = (0, 255, 0)  # Verde para conocidos

#                 # Crear un nuevo registro de acceso
#                 imagen_capturada = "ruta_de_imagen_placeholder_o_real.jpg"
#                 persona_identificada = personas[id_prediccion]
                
#                 # Guardar el registro
#                 registro = RegistroAcceso(persona=persona_identificada, imagen_capturada=imagen_capturada)
#                 registro.save()

#             # Dibujar rectángulo y nombre en el frame
#             cv2.rectangle(frame, (x, y), (x+w, y+h), color_rectangulo, 2)
#             cv2.putText(frame, nombre, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color_rectangulo, 2)

#         # Convertir el frame a JPEG para transmisión
#         ret, buffer = cv2.imencode('.jpg', frame)
#         frame = buffer.tobytes()

#         # Enviar el frame al cliente
#         yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

#     # Liberar la cámara
#     captura.release()