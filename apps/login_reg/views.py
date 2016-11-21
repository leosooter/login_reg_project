from django.shortcuts import render, redirect
from django.contrib import messages
from models import User

def index(request):
    print "/////////////////////////// Starting login_reg.views.py index route"


    return render(request, 'login_reg/index.html')

def register(request):
    print "/////////////////////////// Starting login_reg.views.py register route"
    if request.method == 'POST':
        form = request.POST
        form_data = {
            'first_name' : form['first_name'],
            'last_name' : form['last_name'],
            'email' : form['email'],
            'birthday' : form['birthday'],
            'password' : form['password'],
            'c_password' : form['c_password'],
        }
        response = User.objects.register(form_data)
        #response[0] is True or False- Registration was successful
        #response[1] is object containing new user-id on success- object containing error-notes on failure
        print response[0], response[1]
        if response[0]:
            print "Registration was successful"
            request.session['login_id'] = response[1]
            return redirect('/success')

        else:
            print "Registration has errors"
            #Load error_notes returned from registration method into messages
            error_notes = response[1]
            for key, note in error_notes.items():
                messages.error(request, note, extra_tags=key)

            #Preserve any values that do not have error messages and pass them back to the registration form
            for key, value in form_data.items():
                if key not in error_notes:
                    messages.info(request, value, extra_tags=key + "_value")

            return redirect('/')

    else:
        #If the route recieves a non-POST request- assume something shady is going on- log the user out
        #this might be a little harsh if there are legitimate ways a user might accidentally send a GET request to /register
        print "Invalid request method"
        return redirect('/logout')

def login(request):
    print "/////////////////////////// Starting login_reg.views.py login route"
    if request.method == 'POST':
        form = request.POST
        form_data = {
            'login_email' : form['login_email'],
            'login_password' : form['login_password'],
        }
        response = User.objects.login(form_data)
        #response[0] is True or False- Registration was successful
        #response[1] is object containing user information on success- object containing error notes on failure
        print response[0], response[1]
        if response[0]:
            print "Login was successful"
            request.session['login_id'] = response[1]
            return redirect('/success')

        else:
            print "Login has errors"
            #Load error_notes returned from registration method into messages
            error_notes = response[1]
            for key, note in error_notes.items():
                messages.error(request, note, extra_tags=key)

            return redirect('/')
    else:
        print "Invalid request method"
        return redirect('/logout')

def success(request):
    print "/////////////////////////// Starting login_reg.views.py success route"
    # Check to make sure user is logged in
    try:
        request.session['login_id']
    except KeyError:
        print "User is not logged in"
        return redirect('/')

    users = User.objects.all()
    context = {
        'users' : users,
    }
    return render(request, 'login_reg/success.html', context)

def account(request):
    print "/////////////////////////// Starting login_reg.views.py account route"
    # Check to make sure user is logged in
    try:
        request.session['login_id']
    except KeyError:
        print "User is not logged in"
        return redirect('/')

    try:
        login_user = User.objects.get(id=request.session['login_id'])
    #This should never run, but it will prevent the server from breaking if the user is
    #somehow logged in with a bad id
    except User.DoesNotExist:
        print "User matching id not found in records"
        return redirect('/logout')

    request.session['user_info'] = {
        'first_name' : login_user.first_name,
        'last_name' : login_user.last_name,
        'email' : login_user.email,
        'birthday' : login_user.birthday.isoformat(),
    }

    return render(request, 'login_reg/account.html')

def update(request):
        print "/////////////////////////// Starting login_reg.views.py update route"
        if request.method == 'POST':
            form = request.POST
            form_data = {
                'first_name' : form['first_name'],
                'last_name' : form['last_name'],
                'email' : form['email'],
                'birthday' : form['birthday'],
            }
            response = User.objects.update(form_data, request.session['login_id'])
            #response[0] is True or False- Registration was successful
            #response[1] is True on success- object containing error-notes on failure
            print response[0], response[1]
            if response[0]:
                print "Update was successful"
                return redirect('/success')

            else:
                print "Update has errors"
                #Load error_notes returned from registration method into messages
                error_notes = response[1]
                for key, note in error_notes.items():
                    messages.error(request, note, extra_tags=key)

                return redirect('/account')

        else:
            #If the route recieves a non-POST request- assume something shady is going on- log the user out
            #this might be a little harsh if there are legitimate ways a user might accidentally send a GET request to /register
            print "Invalid request method"
            return redirect('/logout')

def delete(request, delete_id):
    print "/////////////////////////// Starting login_reg.views.py delete route"
    try:
        user = User.objects.get(id=delete_id)
        if user.id == request.session['login_id']:
            user.delete()
            return redirect('/logout')
        else:
            user.delete()

    except User.DoesNotExist:
        print "Cannot delete User- id does not match any records"

    return redirect('/success')

def logout(request):
    print "/////////////////////////// Starting login_reg.views.py logout route"
    try:
        request.session.clear()
    except KeyError:
        print "User already logged out"

    return redirect('/')
