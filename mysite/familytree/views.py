from django.http import HttpResponse, Http404
from django.template import loader
from django.shortcuts import render, get_object_or_404, get_list_or_404

from .models import Person, Family, Image, ImagePerson

def index(request):
    return HttpResponse("Here is the familytree index.")

def family_index(request):
    family_list = Family.objects.order_by('display_name')
    context = { 'family_list': family_list}
    return render(request, 'familytree/family_index.html', context)

def person_index(request):
    person_list = Person.objects.order_by('display_name') # add this to limit list displayed: [:125]
    context = { 'person_list': person_list}
    return render(request, 'familytree/person_index.html', context)

def person_detail(request, person_id):
    person = get_object_or_404(Person, pk=person_id)

    try:
        wife_of = Family.objects.filter(wife=person_id)
        husband_of = Family.objects.filter(husband=person_id)
        families_made = wife_of | husband_of
    except Family.DoesNotExist:
        families_made = None

    try:
        images = Image.objects.filter(person_id=person_id)
    except Image.DoesNotExist:
        images = None

    try:
        group_images = ImagePerson.objects.filter(person_id=person_id)
    except ImagePerson.DoesNotExist:
        group_images = None

    return render(request, 'familytree/person_detail.html', {'person': person, 'families_made': families_made,
                                                             'images': images, 'group_images': group_images})

def family_detail(request, family_id):
    family = get_object_or_404(Family, pk=family_id)

    try:
        kids = Person.objects.filter(origin_family=family_id)
    except Person.DoesNotExist:
        kids = None

    return render(request, 'familytree/family_detail.html', {'family': family, 'kids': kids})