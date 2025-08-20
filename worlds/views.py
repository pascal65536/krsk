from django.db.models import Q
from django.utils import timezone
from worlds.models import Parallel, Place
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
import uuid
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404




def worlds_detail(request, pk):
    photo = get_object_or_404(Parallel, pk=pk, deleted__isnull=True)

    if photo.group:
        group_photos = list(Parallel.objects.filter(group=photo.group, deleted__isnull=True).order_by('-changed'))
        # Формируем очередь: выбранное фото - первое, потом остальные
        group_photos_sorted = [photo] + [p for p in group_photos if p.pk != photo.pk]
    else:
        group_photos_sorted = [photo]

    place_title = photo.place.title if photo.place else 'Не указано'
    group_count = len(group_photos_sorted)

    for p in group_photos_sorted:
        if p.tags:
            p.tags_lst = [t.strip().lower() for t in p.tags.split(',')]

    return render(request, 'worlds/worlds_detail.html', {
        'photo': photo,
        'group_photos': group_photos_sorted,
        'place_title': place_title,
        'group_count': group_count,
    })





# def worlds_detail1(request, pk):
#     # Получаем объект или 404
#     photo = get_object_or_404(Parallel, pk=pk, deleted__isnull=True)
#
#     if photo.group:
#         group_photos = Parallel.objects.filter(group=photo.group, deleted__isnull=True).order_by('-changed')
#     else:
#         group_photos = Parallel.objects.filter(pk=photo.pk)
#
#     count = group_photos.count()
#     place_title = 'Не указано'
#     if photo.place:
#         place_title = photo.place.title
#
#     for p in group_photos:
#         if p.tags:
#             p.tags_lst = [t.strip().lower() for t in p.tags.split(',')]
#
#     return render(request, 'worlds/worlds_detail.html', {
#         'group_photos': group_photos,
#         'photo': photo,
#         'group_count': count,
#         'place_title': place_title,
#     })


def worlds_list(request):
    place = request.GET.get("place")
    search = request.GET.get("search")
    tag = request.GET.get("tag")
    page_number = request.GET.get("page", 1)  # Получаем номер страницы из GET, по умолчанию 1

    parallel_dct = dict()
    for parallel in Parallel.objects.filter(deleted__isnull=True):
        parallel_dct.setdefault(parallel.group, list())
        parallel_dct[parallel.group].append(parallel.pk)
    count_dct = dict()
    for k, v in parallel_dct.items():
        for vv in v:
            count_dct[vv] = len(v) if k else 0

    parallel_qs = Parallel.objects.filter(deleted__isnull=True).order_by('-changed')
    if tag:
        parallel_qs = parallel_qs.filter(tags__icontains=tag)
    if search:
        parallel_qs = parallel_qs.filter(
            Q(title__icontains=search) | Q(tags__icontains=search) | Q(descriptions__icontains=search)
        )
    if place:
        if place == 'Не указано':
            parallel_qs = parallel_qs.filter(place__isnull=True)
        else:
            place_obj = Place.objects.get(title=place)
            parallel_qs = parallel_qs.filter(place=place_obj)

    parallel_dct = dict()
    for parallel in parallel_qs:
        parallel_dct.setdefault(parallel.group, list())
        parallel_dct[parallel.group].append(parallel.pk)

    parallel_lst = list()
    for k, v in parallel_dct.items():
        if k is None:
            parallel_lst.extend(v)
        else:
            parallel_lst.append(v[0])

    worlds_qs = Parallel.objects.filter(pk__in=parallel_lst).order_by('-changed')

    # Создаём пагинатор и получаем страницу с нужным номером
    paginator = Paginator(worlds_qs, 24)  # 24 записи на страницу
    try:
        worlds_page = paginator.page(page_number)
    except PageNotAnInteger:
        worlds_page = paginator.page(1)
    except EmptyPage:
        worlds_page = paginator.page(paginator.num_pages)

    place_dct = dict(Place.objects.all().values_list('id', 'title'))

    message = 'Параллельные миры'
    for worlds in worlds_page:
        worlds.group_count = count_dct.get(worlds.pk, 0)
        worlds.place_title = 'Не указано'
        if worlds.place:
            worlds.place_title = place_dct.get(worlds.place.id, 'Не найдено')
        if worlds.tags:
            worlds.tags_lst = [z.strip().lower() for z in worlds.tags.split(',')]

    page_lst = paginator.page_range  # Диапазон страниц для пагинации (1, 2, 3 ...)

    return render(
        request,
        "worlds/worlds_list.html",
        {
            "worlds_qs": worlds_page,
            "page_lst": page_lst,
            "message": message,
            "place": place,
            "request": request,
        },
    )




@require_http_methods(["POST"])
def worlds_group(request):
    selected_ids = request.POST.getlist('group_items')
    group_lst = list(Parallel.objects.filter(id__in=selected_ids, group__isnull=False).values_list('group', flat=True))
    parallels_idx = list(Parallel.objects.filter(Q(id__in=selected_ids) | Q(group__in=group_lst)).values_list('id', flat=True))

    place = None
    tags = None
    title = None
    for p, tg, tt in Parallel.objects.filter(id__in=parallels_idx).values_list('place', 'tags', 'title'):
        if p and not place:
            place = p
        if tg and not tags:
            tags = tg
        if tt and not title:
            title = tt

    if len(parallels_idx) > 1:
        new_group_uuid = str(uuid.uuid4())
        Parallel.objects.filter(id__in=parallels_idx).update(group=new_group_uuid)
        Parallel.objects.filter(id__in=parallels_idx).update(changed=timezone.now())
        if place:
            place_obj = Place.objects.get(id=place)
            Parallel.objects.filter(id__in=parallels_idx).update(place=place_obj)
        if title:
            Parallel.objects.filter(id__in=parallels_idx).update(title=title)
        if tags:
            Parallel.objects.filter(id__in=parallels_idx).update(tags=tags)
    return redirect('worlds_list')
