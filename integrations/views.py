from django.http import HttpResponse
from django.shortcuts import render, redirect

from .forms import *
from .models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .integrator import integrate
from .sync_calendars import SyncCalendars

import logging

logger = logging.getLogger(__name__)


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
            logger.info(f"User has logged in. {request}")
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

    property_info = Property_Info.objects.get(property=prop)
    prop_history = History.objects.filter(property_name=prop).order_by('-run_date')[:30]
    sync_calendar_info = CalendarSyncInfo.objects.get(property=prop)

    logger.info(f"Navigating to property_detail. {property_info}")
    context = {'property_info': property_info, 'prop_history': prop_history, 'sync_calendar_info': sync_calendar_info}
    return render(request, 'integrations/property-detail.html', context)


@login_required
def run_integrator(request, prop_pk, info_pk):
    info = Property_Info.objects.get(pk=info_pk)

    prop = Property.objects.get(pk=prop_pk)
    property_name = prop.property_name

    logger.info(f"Running integrator for property: {property_name} ID: {prop_pk}. This is from within the run_integrator function.")

    if prop.user != request.user and not request.user.is_staff:
        return redirect('properties')
    else:
        prop_info = Property_Info.objects.get(property=prop)
        pricelabs_key = prop_info.pricelabs_key
        pricelabs_id = prop_info.pricelabs_id
        motopress_key = prop_info.motopress_key
        motopress_secret = prop_info.motopress_secret
        motopress_season_request = prop_info.motopress_season_request
        motopress_rates_request = prop_info.motopress_rates_request
        accomodation_id = prop_info.accomodation_id

        response = integrate(False, motopress_key, motopress_secret, motopress_season_request, motopress_rates_request,
                             pricelabs_key, pricelabs_id, accomodation_id, property_name)
        history = History(property_name=prop)
        if response.status_code == 200:
            history.notes = 'Success'
        else:
            history.notes = 'Fail'

        history.save()
        return redirect('property-detail', prop_pk)


def run_bearadise(request):
    prop = Property.objects.get(pk=1)

    prop_info = Property_Info.objects.get(property=prop)
    pricelabs_key = prop_info.pricelabs_key
    pricelabs_id = prop_info.pricelabs_id
    motopress_key = prop_info.motopress_key
    motopress_secret = prop_info.motopress_secret
    motopress_season_request = prop_info.motopress_season_request
    motopress_rates_request = prop_info.motopress_rates_request
    accomodation_id = prop_info.accomodation_id

    # print("pricelabs_key", pricelabs_key)
    # print("pricelabs_id", pricelabs_id)
    # print("motopress_key", motopress_key)
    # print("motopress_secret", motopress_secret)
    # print("motopress_season_request", motopress_season_request)
    # print("motopress_rates_request", motopress_rates_request)
    # print("accomodation_id", accomodation_id)

    print("running integrator from run_bearadise endpoint.")

    # Below this is copied directly from the run_integrator function above. I know it doesn't meet DRY standards.
    response = integrate(False, motopress_key, motopress_secret, motopress_season_request, motopress_rates_request,
                         pricelabs_key, pricelabs_id, accomodation_id, prop.property_name, )
    history = History(property_name=prop)
    if response.status_code == 200:
        history.notes = 'Success'
    else:
        history.notes = 'Fail'

    history.save()
    # ** end of copy **

    context = {}
    return render(request, 'integrations/run-bearadise.html', context)


# Loops though each Property. If it has a CalendarSyncInfo, then it will run the calendar sync.
# If not, it will skip. Returns 200 status code on completion.
def sync_calendars(request):
    logger.info(f"running sync_calendars.")
    for prop in Property.objects.all():
        logger.info(f"Current property is: {prop.property_name}. Will attempt to sync calendars.")

        try:
            calendar_sync_info = CalendarSyncInfo.objects.get(property=prop)

            calendar_sync = SyncCalendars(calendar_sync_info.wp_login, calendar_sync_info.sync_url,
                                          calendar_sync_info.username, calendar_sync_info.password)
            response = calendar_sync.send_sync_request()

        except CalendarSyncInfo.DoesNotExist:
            logger.info(f'{prop.property_name} does not have a CalendarSyncInfo.')
            continue

    return HttpResponse(status=200)


def sync_pricelabs_data(request, prop_pk):
    logger.info(f"Running sync_pricelabs_data for the following primary key: {prop_pk}")

    prop = Property.objects.get(pk=prop_pk)

    prop_info = Property_Info.objects.get(property=prop)
    pricelabs_key = prop_info.pricelabs_key
    pricelabs_id = prop_info.pricelabs_id
    motopress_key = prop_info.motopress_key
    motopress_secret = prop_info.motopress_secret
    motopress_season_request = prop_info.motopress_season_request
    motopress_rates_request = prop_info.motopress_rates_request
    accomodation_id = prop_info.accomodation_id

    logger.info(f"running integrator from sync_pricelabs_data endpoint for {prop.property_name}.")

    # Below this is copied directly from the run_integrator function above. I know it doesn't meet DRY standards.
    response = integrate(False, motopress_key, motopress_secret, motopress_season_request, motopress_rates_request,
                         pricelabs_key, pricelabs_id, accomodation_id, prop.property_name, )
    history = History(property_name=prop)
    if response.status_code == 200:
        history.notes = 'Success'
    else:
        history.notes = 'Fail'

    history.save()
    # ** end of copy **

    context = {"prop_pk": prop_pk}
    return render(request, 'integrations/sync-pricelabs-data.html', context)
