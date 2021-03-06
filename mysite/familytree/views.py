from datetime import datetime

from django.shortcuts import render, get_object_or_404, get_list_or_404
from .models import Person, Family, Image, ImagePerson, Note , Branch, Profile
from django.contrib.auth import logout

today = datetime.now() # used to get birthday_people and anniversary_couples

show_by_branch = True  # default this to False, but set to true if you've set families
branch1_name = Branch.objects.filter(id=1)
branch2_name = Branch.objects.filter(id=2)
branch3_name = Branch.objects.filter(id=3)
branch4_name = Branch.objects.filter(id=4)


def index(request):  #dashboard page
    user = request.user
    this_person = get_user_person(request.user).first()

    profile = Profile.objects.filter(user=user)
    accessible_branches = get_valid_branches(request)

    try:
        birthday_people = Person.objects.filter(birthdate__month=today.month).order_by('birthdate__day')
    except Person.DoesNotExist:
        birthday_people = None

    try:
        anniversary_couples = Family.objects.filter(marriage_date__month=today.month).order_by('marriage_date__day')
    except Family.DoesNotExist:
        anniversary_couples = None

    try:
        latest_pics = Image.objects.all().order_by('-id')[:10]
    except Image.DoesNotExist:
        latest_pics = None

    context = {'user': user, 'birthday_people': birthday_people,  'anniversary_couples': anniversary_couples,
               'latest_pics': latest_pics, 'user_person': this_person, 'profile': profile,
               'accessible_branches': accessible_branches
               }

    return render(request, 'familytree/dashboard.html', context )


def family_index(request):
    this_person = get_user_person(request.user).first()
    family_list = Family.objects.order_by('display_name')
    accessible_branches = get_valid_branches(request)

# @@TODO: update so we can use branch1_name variables instead (tried but it's not working yet)

    branch1_families = Family.objects.filter(branches__display_name__contains="Keem")
    branch2_families = Family.objects.filter(branches__display_name__contains="Husband")
    branch3_families = Family.objects.filter(branches__display_name__contains="Kemler")
    branch4_families = Family.objects.filter(branches__display_name__contains="Kobrin")

    context = { 'family_list': family_list,
                'branch1_families': branch1_families, 'branch2_families': branch2_families,
                'branch3_families': branch3_families, 'branch4_families': branch4_families, 'branch1_name': branch1_name,
                'branch2_name': branch2_name, 'branch3_name': branch3_name, 'branch4_name': branch4_name,
                'show_by_branch': show_by_branch, 'accessible_branches': accessible_branches, 'user_person': this_person}

    return render(request, 'familytree/family_index.html', context)


def person_index(request):
    accessible_branches = get_valid_branches(request)
    this_person = get_user_person(request.user).first()

    # to start we'll assume up to 4 branches, gets ids 1-4, entering names manually
    # @@TODO: update so we can use branch1_name variables instead (tried but it's not working yet)
    branch1_people = Person.objects.filter(branches__display_name__contains="Keem")
    branch2_people = Person.objects.filter(branches__display_name__contains="Husband")
    branch3_people = Person.objects.filter(branches__display_name__contains="Kemler")
    branch4_people = Person.objects.filter(branches__display_name__contains="Kobrin")

    person_list = Person.objects.order_by('display_name') # add this to limit list displayed: [:125]
    context = { 'person_list': person_list,
                'branch1_people': branch1_people, 'branch2_people': branch2_people,
                'branch3_people': branch3_people, 'branch4_people': branch4_people, 'branch1_name': branch1_name,
                'branch2_name': branch2_name, 'branch3_name': branch3_name, 'branch4_name': branch4_name,
                'show_by_branch': show_by_branch, 'accessible_branches':accessible_branches,
                'request_user': request.user,
                'user_person': this_person
                }
    return render(request, 'familytree/person_index.html', context)


def person_detail(request, person_id):
    user_person = get_user_person(request.user).first()
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

    try:
        notes = Note.objects.filter(person_id=person_id)
    except ImagePerson.DoesNotExist:
        notes = None

    try:
        featured_images = Image.objects.filter(person_id=person_id) & Image.objects.filter(featured=1)
    except Image.DoesNotExist:
        featured_images = None

    return render(request, 'familytree/person_detail.html', {'person': person, 'families_made': families_made,
                                                             'images': images, 'group_images': group_images, 'notes': notes,
                                                             'featured_images': featured_images, 'user_person': user_person})


def family_detail(request, family_id):
    family = get_object_or_404(Family, pk=family_id)
    user_person = get_user_person(request.user).first()

    try:
        kids = Person.objects.filter(origin_family=family_id)
    except Person.DoesNotExist:
        kids = None

    try:
        notes = Note.objects.filter(family_id=family_id)
    except ImagePerson.DoesNotExist:
        notes = None

    try:
        featured_images = Image.objects.filter(family_id=family_id) & Image.objects.filter(featured=1)
    except Image.DoesNotExist:
        featured_images = None

    try:
        images = Image.objects.filter(family_id=family_id)
    except Image.DoesNotExist:
        images = None

    return render(request, 'familytree/family_detail.html', {'family': family, 'kids': kids, 'notes': notes,
                                                             'featured_images': featured_images, 'icons': images,
                                                             'user_person': user_person})


def image_detail(request, image_id):
    user_person = get_user_person(request.user).first()
    image = get_object_or_404(Image, pk=image_id)

    this_image_person, this_image_family, image_people = Image.image_subjects(image)

    return render(request, 'familytree/image_detail.html', {'image': image, 'image_person': this_image_person,
                                                            'image_family': this_image_family,
                                                            'image_people' : image_people, 'user_person': user_person
                                                            })


def image_index(request):
    user_person = get_user_person(request.user).first()
    accessible_branches = get_valid_branches(request)

    # @@TODO: update so we can use branch1_name variables instead (tried but it's not working yet)
    branch1_images = Image.objects.filter(branches__display_name__contains="Keem").order_by('year')
    branch2_images = Image.objects.filter(branches__display_name__contains="Husband").order_by('year')
    branch3_images = Image.objects.filter(branches__display_name__contains="Kemler").order_by('year')
    branch4_images = Image.objects.filter(branches__display_name__contains="Kobrin").order_by('year')

    image_list = Image.objects.none()

    if branch1_name.first in accessible_branches:
        image_list = image_list.union(branch1_images)
    if branch2_name.first in accessible_branches:
        image_list = image_list.union(branch2_images)
    if branch3_name.first in accessible_branches:
        image_list = image_list.union(branch3_images)
    if branch4_name.first in accessible_branches:
        image_list = image_list.union(branch4_images)

    image_list = image_list.union( Image.objects.order_by('year')) # add this to limit list displayed: [:125]
    context = { 'image_list': image_list, 'accessible_branches': accessible_branches, 'branch2_name': branch2_name,
                'user_person': user_person}
    return render(request, 'familytree/image_index.html', context)

def landing(request):
    landing_page_people = Person.objects.filter(show_on_landing_page=True)

    context = { 'landing_page_people': landing_page_people}
    return render(request, 'familytree/landing.html', context)


def get_valid_branches(request):
    user = request.user
    profile = Profile.objects.filter(user=user)
    accessible_branches = Branch.objects.filter(profile__in=profile)
    return accessible_branches

def get_user_person(user):
    try:
        this_user_person = Person.objects.filter(profile__user_id=user)
    except Profile.DoesNotExist:
        this_user_person = None
    return this_user_person

def logout(request):
    logout(request)
    return render(request, 'familytree/landing.html')