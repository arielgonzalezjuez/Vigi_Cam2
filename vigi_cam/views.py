from django.shortcuts import render, redirect, get_object_or_404
from .models import Persona, RegistroAcceso, Camara, Video
from .forms import PersonaForm, CamaraForm, ClienteRegistrarForm, ClienteActualizarForm
from django.http import HttpResponse, StreamingHttpResponse,HttpResponseNotFound
import numpy as np
from django.core.files.base import ContentFile
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
import cv2
from datetime import datetime
from django.conf import settings
import os
from django.conf import settings
from django.core.files.storage import default_storage
import time

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

def video_list(request):
    # Obtener todos los videos de la base de datos
    videos = Video.objects.all()
    return render(request, 'video_list.html', {'videos': videos})

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
    folder = os.path.join(settings.MEDIA_ROOT, 'imagenes_capturadas')
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
    fecha_hora = datetime.now().strftime("%Y%m%d_%H%M")  # Formato: AAAAMMDD_HHMMSS
    nombre_video = f"video_{fecha_hora}.mp4"  # Usamos .mp4 para compatibilidad
    ruta_video = os.path.join(settings.MEDIA_ROOT, 'videos_capturados', nombre_video)

    # Asegurarse de que el directorio exista
    os.makedirs(os.path.dirname(ruta_video), exist_ok=True)

    # Configurar el codec y el objeto VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'avc1')  # Codec H.264
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
                        rostro_conocido = frame[y:y+h, x:x+w]
                        _, img_bytes = cv2.imencode('.jpg', rostro_conocido)  # Convertir el rostro a JPEG

                        # Crear un nombre único para la imagen capturada
                        imagen_nombre = f"rostro_conocido_{str(int(time.time()))}.jpg"
                        imagen_path = os.path.join(settings.MEDIA_ROOT, 'imagenes_capturadas', imagen_nombre)

                        # Guardar la imagen en el sistema de archivos
                        default_storage.save(imagen_path, ContentFile(img_bytes.tobytes()))

                        # Crear la instancia de RegistroAcceso con la imagen guardada
                        imagen_guardada = f'imagenes_capturadas/{imagen_nombre}'
                        color_rectangulo = (0, 255, 0)  # Verde para conocido
                        persona = Persona.objects.get(nombre=nombre)
                        RegistroAcceso.objects.create(persona=persona,imagen_capturada=imagen_guardada)
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

# Vista para servir archivos de video directamente
def video_download(request, video_path):
    file_path = os.path.join(settings.MEDIA_ROOT, 'videos_capturados', video_path)
    if not os.path.exists(file_path):
        return HttpResponseNotFound("Video no encontrado.")

    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='video/mp4')
        response['Content-Disposition'] = f'inline; filename="{video_path}"'
        return response
