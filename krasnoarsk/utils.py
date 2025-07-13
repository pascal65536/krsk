import os
import datetime
import string
import textwrap

import requests
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from django.db.models.fields.files import ImageFieldFile


def cyr2lat(cyrillic):
    if not cyrillic:
        return cyrillic
    cyr2lat_dct = {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "yo",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "h",
        "ц": "c",
        "ч": "ch",
        "ш": "sh",
        "щ": "shch",
        "ъ": "y",
        "ы": "y",
        "ь": "i",
        "э": "e",
        "ю": "yu",
        "я": "ya",
        "!": "_",
        "'": "_",
        " ": "_",
        ",": "_",
        "+": "_",
        ".": "_",
        ":": "_",
        "-": "_",
        "%": "_",
        "&": "_",
        "*": "_",
        "?": "_",
        "@": "_",
        "$": "_",
        "^": "_",
        "(": "_",
        ")": "_",
        "{": "_",
        "}": "_",
        "[": "_",
        "]": "_",
        "/": "_",
        "«": "_",
        "»": "_",
        '"': "_",
    }
    char_lst = list()
    eng = f"{string.ascii_lowercase}{string.digits}"
    for i in cyrillic.lower():
        if i.lower() in eng:
            char_lst.append(i.lower())
            continue
        char_lst.append(cyr2lat_dct.get(i, "-"))
    return "".join(char_lst).strip("_")


def opengraph(post_obj):
    """
    Создадим opengraph для Рубрики и Статьи
    cd ~/git/krsk/ && pipenv shell && python3 manage.py runserver
    """
    from article.models import Post
    from photo.models import Photo
    from article.models import Category

    photo_obj_path = None
    photo_obj = None
    this_cat = [
        isinstance(post_obj, Category),
        isinstance(post_obj.image, ImageFieldFile),
    ]
    if all(this_cat):
        photo_obj = post_obj.image
        photo_obj_path = os.path.join(settings.MEDIA_ROOT, post_obj.image.name)

    this_post = [
        isinstance(post_obj, Post),
        isinstance(post_obj.image, Photo),
        # isinstance(post_obj.image.picture, ImageFieldFile),
    ]
    if all(this_post):
        photo_obj = post_obj.image.picture
        picture_name = post_obj.image.picture.name
        photo_obj_path = os.path.join(settings.MEDIA_ROOT, picture_name)

    font_size = 36
    pic_width = 1024
    pic_height = 512
    max_color = (255, 255, 255)

    fill_image = Image.new("RGB", (pic_width, pic_height), max_color)
    if photo_obj and photo_obj_path and os.path.exists(photo_obj_path):
        input_im = Image.open(str(photo_obj_path))
        if input_im.mode != "RGBA":
            input_im = input_im.convert("RGBA")

        # Найдём цвет для градиента
        unique_colors = dict()
        for i in range(input_im.size[0]):
            for j in range(input_im.size[1]):
                pixel = input_im.getpixel((i, j))
                unique_colors.setdefault(pixel, 0)
                unique_colors[pixel] += 1
        max_color = (0, 0, 0)
        max_color_count = 0
        for k, v in unique_colors.items():
            if v > max_color_count and len(set(list(k)[0:3])) > 1:
                max_color_count = v
                max_color = k

        # Это картинка для соцсетей
        (w, h) = input_im.size
        if w / h < pic_width / pic_height:
            percent = pic_width / w
        else:
            percent = pic_height / h
        width = int(w * percent)
        height = int(h * percent)
        input_im = input_im.resize((width, height), Image.Resampling.LANCZOS)
        yc = int((height - pic_height) / 2)
        xc = 0
        input_im = input_im.crop((xc, yc, xc + pic_width, yc + pic_height))

        alpha_gradient = Image.new("L", (pic_width, 1), color=0)
        for x in range(pic_width):
            a = int((1 * 255.0) * (1.0 - 0.7 * float(x) / pic_width))
            if a > 0:
                alpha_gradient.putpixel((x, 0), a)
            else:
                alpha_gradient.putpixel((x, 0), 0)

        alpha = alpha_gradient.resize(input_im.size)

        # create black image, apply gradient
        black_im = Image.new("RGBA", (pic_width, pic_height), color=max_color)
        black_im.putalpha(alpha)

        # make composite with original image
        fill_image = Image.alpha_composite(input_im, black_im)

    if min(max_color) > 127:
        font_color = (0, 0, 0)
    else:
        font_color = (255, 255, 255)

    text = post_obj.title
    unicode_text = "\n".join(textwrap.wrap(text, width=30))
    draw = ImageDraw.Draw(fill_image)
    font_path = os.path.join(settings.STATIC_ROOT, "fonts", "Oswald-Medium.ttf")
    unicode_font = ImageFont.truetype(font_path, font_size)

    textbox = draw.textbbox(text=unicode_text, xy=(0, 0), font=unicode_font)
    text_width, text_height = textbox[2], textbox[3]

    text_top = (pic_height - text_height) // 2
    text_left = (pic_width - text_width) // 2
    draw.text((text_left, text_top), unicode_text, font=unicode_font, fill=font_color)

    # Создадим путь и имя файла
    short = f"{post_obj.pk:04d}"
    directory = os.path.join(settings.MEDIA_ROOT, "opengraph", short[:2], short[2:4])
    directory_item = os.path.join("media", "opengraph", short[:2], short[2:4])
    if not os.path.exists(directory):
        os.makedirs(directory)
    ext = "png"
    filename = f"{short}.{ext}"
    fill_image.save(f"{directory}/{filename}", format="PNG", dpi=[72, 72])
    return f"{directory_item}/{filename}"


def check_plagiarism(text):
    url = "https://content-watch.ru/public/api/"
    data = {"action": "CHECK_TEXT", "key": settings.API_KEY, "test": 0, "text": text}
    req = requests.post(url, data=data)
    req.encoding = "utf-8"
    return req.json()
