from __future__ import unicode_literals
from django.db import models
import re, time
import bcrypt

#regex object stores regex validations and error messages
#some regexs are duplicates so that field-names can be preserved,
#fields like email and login_email have idetical regex but errors need to be displayed in different places
regex = {
    'first_name' : (re.compile(r'^[a-zA-Z]{2,}$'), "Name must be at least two letter long with no numbers"),
    'last_name' : (re.compile(r'^[a-zA-Z]{2,}$'), "Name must be at least two letter long with no numbers"),
    'email' : (re.compile(r'^[a-zA-Z0-9\.\+_-]+@[a-zA-Z0-9\._-]+\.[a-zA-Z]*$'), "Please enter a valid email"),
    'login_email' : (re.compile(r'^[a-zA-Z0-9\.\+_-]+@[a-zA-Z0-9\._-]+\.[a-zA-Z]*$'), "Please enter a valid email"),
    'birthday' : (re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$'), "Please enter a valid date"),
    'password' : (re.compile(r'(?=.*[A-Z])(?=.*[0-9])[a-zA-Z0-9]{8,}'), "Please enter a valid password"),
    'login_password' : (re.compile(r'(?=.*[A-Z])(?=.*[0-9])[a-zA-Z0-9]{8,}'), "Please enter a valid password"),
}

class UserManager(models.Manager):
    #Checks for empty fields and Uses regex object to validate format.
    #first value in tuple is true or false- registration is valid
    #second value returns an error notes object if form has errors, or a user info object if form is valid
    def validateFields(self, form_data):
        print "Starting login_reg.models.py UserManager validateFields method"
        valid = True
        error_notes = {}
        #Check for empty fields
        for key, value in form_data.items():
            print "Checking for value in {} field".format(key)
            if len(value) == 0:
                print "//////////////////// Form Error- {} field is empty".format(key)
                valid = False
                error_notes[key] = "This field cannot be empty"

        #Check for valid field formats- if regex exists for field- validate
        for key, value in form_data.items():
            #Check to see if regex exists for field
            if key in regex:
                print "Checking format of {} field".format(key)
                if not regex[key][0].search(value):
                    print "//////////////////// Form Error- {} field is invalid format".format(key)
                    valid = False
                    #If invalid, and no error note has been set for this field- pull error matching error message from regex dictionary
                    #The error notes will contain the most basic note for each field.
                    if not key in error_notes:
                        error_notes[key] = regex[key][1]

        if 'birthday' in form_data:
            #Check that user birthday at least 14 years before current date
            if not User.objects.checkAge(form_data['birthday']):
                valid = False
                if not 'birthday' in error_notes:
                    error_notes['birthday'] = "You must be at least 14 years old to register an account"

        return (valid, error_notes)

    def checkAge(self, birthday):
        print "Starting login_reg.models.py UserManager checkAge method"
        #Check that user birthday at least 14 years before current date
        #age-restriction is calculated by getting seconds since epoch, subtrating seconds per year * minimum age in years and formatting to string-time
        age_restriction = time.strftime("%Y-%m-%d", time.localtime(time.time() - (31561600 * 14)))
        birthday = str(birthday)
        print "age_restriction", age_restriction
        print "birthday", birthday
        print "birthday <= age_restriction is:", birthday <= age_restriction
        if birthday <= age_restriction:
            return True
        else:
            return False

    def register(self, form_data):
        print "Starting login_reg.models.py UserManager register method"
        #Uses validateFields method to check for basic field validations- if successful,
        #checks to make sure new email is not already in DB and creates new user.
        response = User.objects.validateFields(form_data)
        valid = True
        error_notes = response[1]
        #Check if basic validation returned false
        if not response[0]:
            return (False, error_notes)
        #check that confirm-password matches password
        if form_data['password'] != form_data['c_password']:
            valid = False
            error_notes['c_password'] = "confirm-password does not match password"
        #Check to make sure email does not exist in DB- save this for last because it requires DB call
        try:
            email_check = User.objects.get(email=form_data['email'])
            print "Email already exists in DB"
            valid = False
            error_notes['email'] = "The email you entered is already registered to a different account. Please use a different email or login below"
        except User.DoesNotExist:
            print "Email is not duplicate"

        if valid == False:
            print "Form has errors"
            return (False, error_notes)

        #Create user object in DB
        print "//////////////////////////////////Form is Vald- Creating new User"
        password = bcrypt.hashpw(form_data['password'].encode(encoding="utf-8", errors="strict"), bcrypt.gensalt())
        new_user = User.objects.create(first_name=form_data['first_name'], last_name=form_data['last_name'], email=form_data['email'], birthday=form_data['birthday'], password=password)
        new_user.save()
        print new_user.id
        return (True, new_user.id)

    def login(self, form_data):
        print "Starting login_reg.models.py UserManager login method"
        #Uses validateFields method to check for basic field validations- if successful,
        #checks to make sure email is in DB and that password matches password in DB.
        response = User.objects.validateFields(form_data)
        valid = True
        error_notes = response[1]
        #Check if basic validation returned false
        if not response[0]:
            return (False, error_notes)
        #check that an account exists for the email
        try:
            user = User.objects.get(email=form_data['login_email'])
            print "Email found in DB"

        except User.DoesNotExist:
            valid = False
            error_notes['login_email'] = "The email you entered is not registered to an account. Please use a different email or register a new account"

        #Check that the password matches the password in the DB
        password = form_data['login_password'].encode(encoding="utf-8", errors="strict")
        hashed_password = user.password.encode(encoding="utf-8", errors="strict")
        if bcrypt.hashpw(password, hashed_password) == hashed_password:
            print "Login Successful!"
            return (True, user.id)
        else:
            print "Password does not match record"
            error_notes['login_password'] = "The password you entered doe not match our records"
            return (False, error_notes)

    def update(self, form_data, login_id):
        print "Starting login_reg.models.py UserManager update method"
        #Uses validateFields method to check for basic field validations- if successful,
        #checks to make sure new email is not already registered to a different account
        #Updates User info if form is valid
        response = User.objects.validateFields(form_data)
        valid = True
        error_notes = response[1]
        #Check if basic validation returned false
        if not response[0]:
            return (False, error_notes)

        #Check to make sure email does not belong to a different account in the DB- save this for last because it requires DB call
        try:
            email_check = User.objects.get(email=form_data['email'])
            if email_check.id != login_id:
                print "Email is already registered to another account"
                valid = False
                error_notes['email'] = "The email you entered is already registered to a different account"
        except User.DoesNotExist:
            print "Email is not duplicate or belongs to user"

        if valid == False:
            print "Form has errors"
            return (False, error_notes)

        print "//////////////////////////////////Form is Vald- Updating User"
        user = User.objects.get(id=login_id)
        user.first_name = form_data['first_name']
        user.last_name = form_data['last_name']
        user.email = form_data['email']
        user.birthday = form_data['birthday']
        user.save()
        return (True, True)

class User(models.Model):
    first_name = models.CharField(max_length=55)
    last_name = models.CharField(max_length=55)
    email = models.CharField(max_length=55)
    birthday = models.DateField()
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = UserManager()
