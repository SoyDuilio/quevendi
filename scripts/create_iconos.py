# Script rápido para crear iconos
from PIL import Image, ImageDraw, ImageFont

def create_icon(size):
    img = Image.new('RGB', (size, size), color='#0EA5E9')
    draw = ImageDraw.Draw(img)
    
    # Dibujar "QV"
    font_size = size // 2
    text = "QV"
    
    # Calcular posición central
    bbox = draw.textbbox((0, 0), text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    position = ((size - text_width) // 2, (size - text_height) // 2)
    draw.text(position, text, fill='white')
    
    img.save(f'static/icon-{size}.png')

create_icon(192)
create_icon(512)