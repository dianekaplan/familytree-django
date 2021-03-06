from django.core.management.base import BaseCommand, CommandError
from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement
from gedcom.parser import Parser
from ...models import Person, Family
from pathlib import Path
from django.utils import timezone

class Command(BaseCommand):
    help = 'Imports records from GEDCOM file'
    missing_args_message = 'Please specify GEDCOM file'
    gedcom_person_records = 0;
    gedcom_family_records = 0;
    person_added_count = 0;
    family_added_count = 0;
    person_skipped_count = 0;
    child_family_dict = {}

    def add_arguments(self, parser):
        parser.add_argument('file name', type=Path, help='Name of GEDCOM file to import from')

    def handle(self, *args, **kwargs):
        filename = kwargs['file name']

        # validate that the user gave file with extension ged
        if filename.suffix!= '.ged':
            raise CommandError('Please specify GEDCOM file, ex: myGedcom.ged')

        # Check that the file is there
        path = Path("familytree/management/commands/gedcom_files/") # @@TODO: update to take the whole path (so it doesn't need to be saved in a particular folder)
        path_plus_file = path.joinpath(filename)

        if (path_plus_file.is_file()):
            gedcom_parser = Parser()
            gedcom_parser.parse_file(path_plus_file)
            root_child_elements = gedcom_parser.get_root_child_elements()

            for element in root_child_elements:
                # find/add people records
                if isinstance(element, IndividualElement):
                    self.handle_person(element)

                # find/add family records (person records exist already, so we can look up parent references)
                # also save intermediate dictionary: CHIL INDI - family INDI
                if isinstance(element, FamilyElement):
                    self.handle_family(element)

            #now that we've saved all the people and families, populate orig_family on people records
            self.add_orig_family_values(self.child_family_dict)

        else:
            raise CommandError('That gedcom file does not exist in the expected directory')

        # gather run results
        run_results = 'gedcom_person_records: ' + str(self.gedcom_person_records) +  '\n'
        run_results += 'gedcom_family_records: ' + str(self.gedcom_family_records) +  '\n'
        run_results += 'person_added_count: ' + str(self.person_added_count) +  '\n'
        run_results += 'person_skipped_count: ' + str(self.person_skipped_count) +  '\n'
        run_results += 'family_added_count: ' + str(self.family_added_count) +  '\n'

        # Display and log them
        self.stdout.write(self.style.SUCCESS('You passed filename: ') + str(filename))
        self.stdout.write(run_results )
        f = open('ImportInfo.txt', 'w')
        f.write(run_results)
        f.closed

    def handle_person(self, element):
        self.gedcom_person_records += 1
        (gedcom_first_middle, last) = element.get_name()
        gedcom_uuid = ''
        skip_record = False

        if "INDI" in str(element):
            gedcom_indi = str(element).replace(" INDI", "").replace("0 ", "").replace("\r\n", "")
        # get the fields available from our parser
        (birthdate, birthplace, sources) = element.get_birth_data()
        sex = element.get_gender()
        occupation = element.get_occupation()
        (deathdate, deathplace, sources) = element.get_death_data()
        display_name = gedcom_first_middle + " " + last

        # check the children for our custom UUID field (applicable for subsequent imports)
        element_children = element.get_child_elements()
        for child in element_children:
            # print(element.to_gedcom_string(recursive=True))
            if "ALIA" in str(child):
                gedcom_uuid = str(child).replace("1 ALIA ", "").replace("\r\n", "")

                try:
                    matching_record = Person.objects.get(gedcom_uuid=gedcom_uuid)
                    if matching_record != "":
                        skip_record = self.check_matching_record(matching_record, element)
                except:
                    print(gedcom_first_middle + " " + last + " gedcom record with ALIA tag had no matching value in our data")

        if not skip_record:
            # make the person record
            (obj, created_bool) = Person.objects.get_or_create(gedcom_indi=gedcom_indi, gedcom_uuid=gedcom_uuid,
                                                           first=gedcom_first_middle, last=last,
                                                           display_name=display_name, birthdate_note=birthdate,
                                                           birthplace=birthplace, sex=sex, work=occupation,
                                                           deathdate_note=deathdate, resting_place=deathplace,
                                                               show_on_landing_page=True,
                                                           created_at = timezone.now(), updated_at = timezone.now(), reviewed=False)
            if created_bool:
                self.person_added_count += 1
        else:
            self.person_skipped_count += 1

    def handle_family(self, element):
        gedcom_indi = str(element).replace(" FAM", "").replace("0 ", "").replace("\r\n", "")
        self.gedcom_family_records += 1
        no_kids_bool = True
        wife = ""
        husband = ""
        element_children = element.get_child_elements()
        marriage_date = ""
        husband_indi= ""
        wife_indi = ""

        for child in element_children:  # @TODO: look back at gedcom_parser.get_family_members approach: there you see FAMS but not wife vs husband
            # print(element.to_gedcom_string(recursive=True))
            if "MARR" in str(child):
                marriage_info = child.get_child_elements()
                for item in marriage_info:
                    if "PLAC" in str(item):
                        marriage_place = str(item).replace("2 PLAC ", "")
                    if "DATE" in str(item):
                        marriage_date = str(item).replace("2 DATE ", "")
            if "WIFE" in str(child):
                wife_indi = str(child).replace("1 WIFE ", "").replace("\r\n", "")
                try:
                    this_person = Person.objects.get(gedcom_indi=wife_indi) #this person does not exist for our family @F118@
                    wife = this_person
                except:
                    print("For family " + gedcom_indi + ", couldn't find person matching wife_indi " + wife_indi)
            if "HUSB" in str(child):
                husband_indi = str(child).replace("1 HUSB ", "").replace("\r\n", "")
                try:
                    this_person = Person.objects.get(gedcom_indi=husband_indi)
                    husband = this_person
                except:
                    print("For family " + gedcom_indi + ", couldn't find person matching husband_indi " + husband_indi)
            if "CHIL" in str(child):
                no_kids_bool = False
                child_indi = str(child).replace("1 CHIL ", "").replace("\r\n",
                                                                       "")  # @FIXME: originally did += for text field, but if this works we won't need to use that text field
                if child_indi not in self.child_family_dict:
                    self.child_family_dict[child_indi] = gedcom_indi  # add dictionary entry for the child

        display_name = (wife.display_name + " & " if wife != "" else "(unknown name) & ")
        display_name += (husband.display_name if husband != "" else "(unknown name)")

        (obj, created_bool) = Family.objects.get_or_create(gedcom_indi=gedcom_indi, display_name=display_name,
                                                           wife_indi=wife_indi, husband_indi=husband_indi,
                                                           marriage_date_note=marriage_date, no_kids_bool=no_kids_bool,
                                                           created_at = timezone.now(), updated_at = timezone.now(), reviewed=False)

        # then link the parents that are known
        if wife != "":
            obj.wife = wife
            obj.save()
        if husband != "":
            obj.husband = husband
            obj.save()

        if created_bool:
            self.family_added_count += 1

    def add_orig_family_values(self, child_family_dict):
        # loop through dictionary
        for entry in self.child_family_dict:
            try:
                this_person = Person.objects.get(gedcom_indi=entry)
                orig_family = Family.objects.get(gedcom_indi=self.child_family_dict.get(entry))
                this_person.origin_family = orig_family
                this_person.save()
            except:
                print("We have a family person whose record didn't get saved with gedcom_indi: " + entry)

    def check_matching_record(self, matching_record, element):
        print("This record with ALIA tag exists already: " + matching_record.first + " " +  matching_record.last)
        # @TODO: come back and look into whether there are fields we'd want to update (ex: add birthdate, etc)
        # If gedcom entry has values for fields we have blank, can fill them in

        # matching_record.reviewed = False
        # matching_record.save()
        skip_record = True
        return skip_record