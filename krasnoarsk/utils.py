import os
import json
import string
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont
from django.db.models.fields.files import ImageFieldFile
from django.conf import settings


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

    # Создадим путь и имя файла
    short = f"{post_obj.pk:04d}"
    directory = os.path.join(settings.MEDIA_ROOT, "opengraph", short[:2], short[2:4])
    directory_item = os.path.join("media", "opengraph", short[:2], short[2:4])
    if not os.path.exists(directory):
        os.makedirs(directory)
    ext = "jpeg"
    filename = f"{short}.{ext}"
    if os.path.exists(f"{directory_item}/{filename}"):
        return f"{directory_item}/{filename}"

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

    fill_image.save(f"{directory}/{filename}", format="PNG", dpi=[72, 72])
    return f"{directory_item}/{filename}"


def create_opengraph_image_for_obj(obj):
    """
    Генерирует изображение OpenGraph (1024x512) для объекта с атрибутом `title` и полем картинки.
    Возвращает относительный URL к сгенерированному файлу.
    """
    # Определяем путь и имя файла
    short = f"{obj.pk:04d}"
    directory = os.path.join(settings.MEDIA_ROOT, "opengraph", short[:2], short[2:4])
    directory_item = os.path.join("media", "opengraph", short[:2], short[2:4])
    if not os.path.exists(directory):
        os.makedirs(directory)
    ext = "png"
    filename = f"{short}.{ext}"
    full_path = os.path.join(directory, filename)
    relative_path = f"/{directory_item}/{filename}"

    # Если файл уже существует, возвращаем путь
    if os.path.exists(full_path):
        return relative_path

    # Параметры изображения
    pic_width = 1024
    pic_height = 512

    # Создаём белый фон
    fill_image = Image.new("RGBA", (pic_width, pic_height), (255, 255, 255, 255))

    # База для вставки фонового изображения, если есть
    photo_obj_path = None
    photo_obj_field = None

    # Определяем поле картинки в объекте, можно расширять по типам
    if hasattr(obj, 'picture') and obj.picture:
        photo_obj_field = obj.picture
    elif hasattr(obj, 'image') and obj.image:
        photo_obj_field = obj.image

    if photo_obj_field:
        photo_obj_path = os.path.join(settings.MEDIA_ROOT, photo_obj_field.name)

    if photo_obj_path and os.path.exists(photo_obj_path):
        input_im = Image.open(photo_obj_path).convert("RGBA")

        # Подгоняем размер изображения в нужный формат с сохранением пропорций
        w, h = input_im.size
        scale = max(pic_width / w, pic_height / h)
        new_w, new_h = int(w * scale), int(h * scale)
        input_im = input_im.resize((new_w, new_h), Image.LANCZOS)

        # Кропаем по центру
        left = (new_w - pic_width) // 2
        top = (new_h - pic_height) // 2
        input_im = input_im.crop((left, top, left + pic_width, top + pic_height))

        # Добавляем градиентный слой для текста (черный прозрачный фон по горизонтали)
        alpha_gradient = Image.new("L", (pic_width, 1), color=0)
        for x in range(pic_width):
            a = int(255 * (1 - 0.7 * x / pic_width))
            alpha_gradient.putpixel((x, 0), max(a, 0))
        alpha = alpha_gradient.resize(input_im.size)
        black_im = Image.new("RGBA", (pic_width, pic_height), color=(0, 0, 0, 180))
        black_im.putalpha(alpha)

        fill_image = Image.alpha_composite(input_im, black_im)

    # Выбираем цвет текста в зависимости от яркости фона
    stat = fill_image.convert("L").getextrema()
    font_color = (255, 255, 255) if stat[0] < 128 else (0, 0, 0)

    # Отрисовываем текст заголовка
    draw = ImageDraw.Draw(fill_image)
    font_path = os.path.join(settings.STATIC_ROOT, "fonts", "Oswald-Medium.ttf")
    font_size = 36
    font = ImageFont.truetype(font_path, font_size)

    text = getattr(obj, 'title', '')
    wrapped_text = "\n".join(textwrap.wrap(text, width=30))

    # import ipdb; ipdb.sset_trace()

    bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
    text_width = bbox[2]
    text_height = bbox[3]
    text_x = (pic_width - text_width) // 2
    text_y = (pic_height - text_height) // 2

    draw.multiline_text((text_x, text_y), wrapped_text, font=font, fill=font_color, align='center')

    # Сохраняем результат
    fill_image.convert("RGB").save(full_path, format="PNG", dpi=(72, 72))

    return relative_path



def check_plagiarism(text):
    url = "https://content-watch.ru/public/api/"
    post_data = {
        "key": settings.API_KEY,
        "text": text,
        "test": 0,
        "action": "CHECK_TEXT",
        "format": "json"
    }
    response = requests.post(url, data=post_data, timeout=30, verify=False)
    response.raise_for_status()
    return response.json()    


def load_json(folder_name_lst, file_name, default={}):
    """
    Функция загружает данные из JSON-файла. Если указанный каталог
    не существует, она создает его. Если файл не существует,
    функция создает пустой JSON-файл. Затем она загружает
    и возвращает содержимое файла в виде словаря.
    """
    if isinstance(folder_name_lst, str):
        folder_name = folder_name_lst
    elif isinstance(folder_name_lst, list):
        folder_name = os.path.join(*folder_name_lst)
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    filename = os.path.join(folder_name, file_name)
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=True)
    with open(filename, encoding="utf-8") as f:
        load_dct = json.load(f)
    return load_dct


def save_json(folder_name_lst, file_name, save_dct):
    """
    Функция сохраняет словарь в формате JSON в указанный файл.
    Если указанный каталог не существует, она создает его.
    Затем она записывает переданный словарь в файл с заданным именем.
    """
    if isinstance(folder_name_lst, str):
        folder_name = folder_name_lst
    elif isinstance(folder_name_lst, list):
        folder_name = os.path.join(*folder_name_lst)
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    filename = os.path.join(folder_name, file_name)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(save_dct, f, ensure_ascii=False, indent=4)


def get_page_items(data_lst, current_page, per_page=24, length=2):
    '''
    data_lst - Отрезает часть списка для создания страницы
    current_page - номер страницы
    per_page - Количество данных на странице
    length - Сколько нужно сделать кнопок
    '''
    num_lst = list()
    maxx = 0
    minn = len(data_lst)
    for i in range(0, len(data_lst), per_page):
        curr = 1 + (i // per_page)
        if maxx < curr:
            maxx = curr
        if minn > curr:
            minn = curr
        if curr - length <= current_page <= curr + length:
            num_lst.append(curr)
    num_lst.append(maxx)
    num_lst.insert(0, minn)
    data_page = data_lst[per_page * (current_page - 1): per_page * current_page]
    return data_page, sorted(set(num_lst))


def clear_text(text, is_russian=True):
    if is_russian:
        alphabet = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    else:
        alphabet = "abcdefghijklmnopqrstuvwxyzабвгдеёжзийклмнопрстуфхцчшщъыьэюя"

    text_new = str()
    for t in text.lower():
        if t in alphabet:
            text_new += t
        else:
            text_new += ' '
    return text_new
