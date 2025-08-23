from django.db.models import Q, Count
from django.utils import timezone
from krasnoarsk.utils import get_page_items, clear_text
from worlds.models import Parallel, Place
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, get_object_or_404, redirect
import uuid


def worlds_detail(request, pk):
    photo = get_object_or_404(Parallel, pk=pk, deleted__isnull=True)

    if photo.group:
        group_photos = list(Parallel.objects.filter(group=photo.group, deleted__isnull=True).order_by('-changed'))
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


def worlds_list(request):
    place = request.GET.get("place")
    search = request.GET.get("search")
    title = request.GET.get("title")
    tag = request.GET.get("tag")
    page_number = int(request.GET.get("page", 1))

    title_count = Parallel.objects.filter(deleted__isnull=True).order_by('title').values('title').annotate(count=Count('title'))
    title_dct = dict()
    for title_count_dct in title_count:
        new_title = list()
        for nt in clear_text(title_count_dct['title'], is_russian=False).split():
            if len(nt) < 3:
                continue
            if nt == 'мир':
                continue
            new_title.append(nt)
        if len(new_title) == 0:
            new_title.append('мир')
        for nt in new_title:
            title_dct.setdefault(nt[0], list())
            title_dct[nt[0]].append(title_count_dct)
    title_dct = dict(sorted(title_dct.items()))

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
    if title:
        title = '' if title == 'Пусто' else title
        parallel_qs = parallel_qs.filter(title=title)
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

    worlds_page, num_lst = get_page_items(worlds_qs, page_number, per_page=8, length=2)

    place_dct = dict(Place.objects.order_by('title').values_list('id', 'title'))

    message = 'Параллельные миры'
    for worlds in worlds_page:
        worlds.group_count = count_dct.get(worlds.pk, 0)
        worlds.place_title = 'Не указано'
        if worlds.place:
            worlds.place_title = place_dct.get(worlds.place.id, 'Не найдено')
        if worlds.tags:
            worlds.tags_lst = [z.strip().lower() for z in worlds.tags.split(',')]

    return render(
        request,
        "worlds/worlds_list.html",
        {
            "worlds_qs": worlds_page,
            "page_lst": num_lst,
            "message": message,
            "place": place,
            "current_page": page_number,
            "title_count": title_count,
            "place_dct": place_dct,
            "title_dct": title_dct,
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
