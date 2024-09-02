import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
from st_social_media_links import SocialMediaIcons

# Cargar el logo SVG desde un archivo
with open("data/logo.svg", "r") as svg_file:
    svg_logo = svg_file.read()

# Incrustar el logo SVG usando HTML
st.markdown(f'<div style="text-align:center">{svg_logo}</div>', unsafe_allow_html=True)
st.subheader("Descubre contra qué Pokémon pelearía tu perro")

# Función para recortar y redimensionar la imagen
def recortar_y_redimensionar(imagen, tamaño=(255, 255)):
    # Convertir la imagen a RGBA
    imagen = imagen.convert("RGBA")
    ancho, alto = imagen.size
    
    # Calcular el tamaño del recorte central
    nuevo_tamaño = min(ancho, alto)
    izquierda = (ancho - nuevo_tamaño) / 2
    superior = (alto - nuevo_tamaño) / 2
    derecha = (ancho + nuevo_tamaño) / 2
    inferior = (alto + nuevo_tamaño) / 2

    # Recortar la imagen al centro
    imagen_recortada = imagen.crop((izquierda, superior, derecha, inferior))

    # Redimensionar la imagen recortada
    imagen_redimensionada = imagen_recortada.resize(tamaño, Image.LANCZOS)
    return imagen_redimensionada

# Subir imagen
uploaded_image = st.file_uploader("Sube una imagen de tu perro", type=["jpg", "jpeg", "png"])

# Mostrar la imagen del perro si ha sido cargada
if uploaded_image is not None:
    st.image(uploaded_image, caption="Imagen de tu perro")

# Input para el nombre y peso del perro
nombre_perro = st.text_input("Introduce el nombre de tu perro", "Tobi")
peso_perro = st.number_input("Introduce el peso de tu perro en kg", min_value=1.0, step=0.1)

# Botón para buscar contrincante Pokémon (desactivado hasta que se suba una imagen)
if st.button("Buscar contrincante Pokémon", disabled=uploaded_image is None):
    if peso_perro > 0:
        # Convertir el peso del perro a hectogramos
        peso_hectogramos = int(peso_perro * 10)

        # Limitar la búsqueda a los primeros 50 Pokémon para mejorar la velocidad
        response = requests.get("https://pokeapi.co/api/v2/pokemon?limit=50")
        pokemon_data = response.json()

        # Variable para guardar el Pokémon con el peso más cercano
        pokemon_mas_cercano = None
        diferencia_peso = float('inf')

        # Iterar sobre cada Pokémon para encontrar el más cercano en peso
        for pokemon in pokemon_data['results']:
            # Obtener la información detallada del Pokémon
            pokemon_info = requests.get(pokemon['url']).json()
            peso_pokemon = pokemon_info['weight']

            # Calcular la diferencia de peso
            diferencia_actual = abs(peso_hectogramos - peso_pokemon)

            if diferencia_actual < diferencia_peso:
                diferencia_peso = diferencia_actual
                pokemon_mas_cercano = pokemon_info

        # Mostrar los resultados
        if pokemon_mas_cercano:
            st.write(f"¡El contrincante perfecto es **{pokemon_mas_cercano['name'].capitalize()}**!")
            
            # Cargar la plantilla y fuentes
            plantilla = Image.open("data/plantilla.png").convert("RGBA")
            try:
                font_path = "fonts/pokemon_classic.ttf"
                font_nombre = ImageFont.truetype(font_path, 45)
                font_peso = ImageFont.truetype(font_path, 30)
            except IOError:
                font_nombre = ImageFont.load_default()
                font_peso = ImageFont.load_default()

            # Crear un objeto para dibujar sobre la imagen
            draw = ImageDraw.Draw(plantilla)

            # Cargar y procesar la imagen del perro y Pokémon
            imagen_perro = Image.open(uploaded_image)
            imagen_perro = recortar_y_redimensionar(imagen_perro)

            pokemon_image_url = pokemon_mas_cercano['sprites']['front_default']
            imagen_pokemon = Image.open(requests.get(pokemon_image_url, stream=True).raw).convert("RGBA").resize((255, 255))

            # Posiciones hardcodeadas para los elementos
            posiciones = {
                "nombre_perro": (300, 490),
                "peso_perro": (230, 565),
                "imagen_perro": (167, 226),
                "nombre_pokemon": (990, 490),
                "peso_pokemon": (925, 565),
                "imagen_pokemon": (855, 232),
            }

            # Calcular ancho de los nombres para centrar
            bbox_nombre_perro = draw.textbbox((0, 0), nombre_perro, font=font_nombre)
            bbox_nombre_pokemon = draw.textbbox((0, 0), pokemon_mas_cercano['name'].capitalize(), font=font_nombre)

            ancho_nombre_perro = bbox_nombre_perro[2] - bbox_nombre_perro[0]
            ancho_nombre_pokemon = bbox_nombre_pokemon[2] - bbox_nombre_pokemon[0]

            # Calcular la nueva posición X para centrar los nombres
            posicion_centrada_perro = (posiciones["nombre_perro"][0] - ancho_nombre_perro // 2, posiciones["nombre_perro"][1])
            posicion_centrada_pokemon = (posiciones["nombre_pokemon"][0] - ancho_nombre_pokemon // 2, posiciones["nombre_pokemon"][1])

            # Formatear el peso del perro para que tenga máximo un decimal
            peso_perro_formateado = f"{peso_perro:.1f} kg"
            peso_pokemon_formateado = f"{pokemon_mas_cercano['weight'] / 10:.1f} kg"

            # Dibujar los textos (nombre y peso) en la plantilla con tamaños de fuente diferentes y centrados
            draw.text(posicion_centrada_perro, nombre_perro, font=font_nombre, fill="white")
            draw.text(posiciones["peso_perro"], peso_perro_formateado, font=font_peso, fill="white")
            draw.text(posicion_centrada_pokemon, pokemon_mas_cercano['name'].capitalize(), font=font_nombre, fill="white")
            draw.text(posiciones["peso_pokemon"], peso_pokemon_formateado, font=font_peso, fill="white")

            # Pegar las imágenes sobre la plantilla en las posiciones correspondientes
            plantilla.paste(imagen_perro, posiciones["imagen_perro"], imagen_perro)
            plantilla.paste(imagen_pokemon, posiciones["imagen_pokemon"], imagen_pokemon)

            # Convertir la imagen final a RGB
            plantilla_final = plantilla.convert("RGB")

            # Mostrar la imagen resultante
            st.image(plantilla_final)

            # Crear un archivo para la imagen final
            buffer = io.BytesIO()
            plantilla_final.save(buffer, format="PNG")
            buffer.seek(0)

            # Botón para descargar la imagen
            st.download_button(
                label="Descargar imagen",
                data=buffer,
                file_name="resultado_pokemon_vs_perro.png",
                mime="image/png"
            )

            # Crear enlaces de redes sociales con st-social-media-links
            social_media_links = [
                "https://x.com/intent/tweet?text=¡Mira%20el%20resultado%20del%20enfrentamiento%20entre%20mi%20perro%20y%20un%20Pokémon!%20%23PerroVsPokemon&url=https://pokemonvsperro.streamlit.app",
                "https://www.tiktok.com/@izanhacecosas",
                "https://youtube.com/@quarto.es",
                "https://www.instagram.com/izanhacecosas/"
            ]

            social_media_icons = SocialMediaIcons(social_media_links)
            social_media_icons.render()

    else:
        st.error("Por favor, introduce un peso válido.")
