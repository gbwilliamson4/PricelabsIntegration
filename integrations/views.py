from django.http import HttpResponse
from django.shortcuts import render, redirect
# from psycopg2 import IntegrityError
from sqlite3 import IntegrityError
from django.contrib.auth.decorators import login_required

from .forms import *
from .models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .integrator import integrate


def index(request):
    # If user is authenticated, navigate to properties page. else, go to login.
    if request.user.is_authenticated:
        print('user is authenticated.')
        if request.user.is_staff:
            print('user is staff')
        return redirect('properties')

    else:
        print('not authenticated.')
        return redirect('login-user')


def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to a success page.
            messages.success(request, "Login Successful.")
            return redirect('index')
        else:
            messages.error(request, 'Invalid username/password combination.')
            return redirect('login-user')
    else:
        # messages.error(request, 'Problem! Sooo many problems!')
        return render(request, 'integrations/login.html', {})


def signup_user(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(request, user)
            messages.success(request, "Login Successful.")
            return redirect('index')

    else:
        form = SignUpForm()

    context = {'form': form}
    return render(request, 'integrations/signup.html', context)


def logout_user(request):
    logout(request)
    # messages.success(request, 'You have been successfully logged out. Please come again soon.')
    return render(request, 'integrations/logout.html', {})


@login_required
def properties(request):
    if request.user.is_staff:
        all_properties = Property.objects.all()
    else:
        all_properties = Property.objects.filter(user=request.user)
    context = {'all_properties': all_properties}
    return render(request, 'integrations/properties.html', context)


@login_required
def property_detail(request, prop_pk):
    prop = Property.objects.get(pk=prop_pk)

    if prop.user != request.user and not request.user.is_staff:
        return redirect('properties')
    else:
        property_info = Property_Info.objects.get(property=prop)
        prop_history = History.objects.filter(property_name=prop).order_by('-run_date')

        # print(property_info)
        context = {'property_info': property_info, 'prop_history': prop_history}
        return render(request, 'integrations/property-detail.html', context)


@login_required
def run_integrator(request, prop_pk, info_pk):
    info = Property_Info.objects.get(pk=info_pk)
    # print(info)

    print('this is running from within the run_integrator function')

    prop = Property.objects.get(pk=prop_pk)

    if prop.user != request.user and not request.user.is_staff:
        return redirect('properties')
    else:
        print('property is', prop)
        prop_info = Property_Info.objects.get(property=prop)
        pricelabs_key = prop_info.pricelabs_key
        pricelabs_id = prop_info.pricelabs_id
        motopress_key = prop_info.motopress_key
        motopress_secret = prop_info.motopress_secret
        motopress_season_request = prop_info.motopress_season_request
        motopress_rates_request = prop_info.motopress_rates_request
        accomodation_id = prop_info.accomodation_id

        response = integrate(False, motopress_key, motopress_secret, motopress_season_request, motopress_rates_request,
                  pricelabs_key, pricelabs_id, accomodation_id)
        history = History(property_name=prop)
        if response.status_code == 200:
            history.notes = 'Success'
        else:
            history.notes = 'Fail'

        history.save()
        return redirect('property-detail', prop_pk)
    # return redirect('property-detail', args=[1])
