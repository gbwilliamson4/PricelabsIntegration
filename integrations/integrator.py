import datetime
import requests
from requests.auth import HTTPBasicAuth
import json


def integrate(testing, moto_key, moto_secret, season_request, rates_request, pricelabs_api_key, pricelabs_id,
         accomodation_id):

    basic = HTTPBasicAuth(moto_key, moto_secret)

    # List of all dates we need to keep track of.
    list_dates = create_list_of_dates()

    if not testing:
        # Lets see real quick if we have any seasons.
        existing_seasons = get_data(season_request,
                                    basic)  # One thing to note, is this will come back as empty if the ones in there are only drafts and not published.
        existing_rates = get_data(rates_request, basic)
        rates_id = existing_rates[0]['id']

        current_dates = [i['end_date'] for i in existing_seasons]
        to_add = [date for date in list_dates if date not in current_dates]
        to_delete = [date for date in current_dates if date not in list_dates]
        print('to_add: ', to_add)
        print('to_delete: ', to_delete)

        for i in to_add:
            pass
            create_season(i, season_request, basic)

        for date in to_delete:
            season_id = delete_season(season_request, date, existing_seasons,
                                      basic)  # I should make this return the season id so we can pass it through to delete the rate.

        # After any seasons are added or deleted, we need to refresh the existing lists with updated data.
        existing_seasons = get_data(season_request,
                                    basic)
        existing_rates = get_data(rates_request, basic)
        rates_id = existing_rates[0]['id']
        motopress_data = motopress_rates_data(existing_seasons,
                                              existing_rates)  # Returns a dictionary with end date as key, season_id as value.
        pricelabls_data = get_pricelabs_data(pricelabs_api_key,
                                             pricelabs_id)  # will return a dict with date as key and price as value
        moto_data_to_add = compare_prices(motopress_data, pricelabls_data, rates_request, basic)
        create_rate(moto_data_to_add, rates_request, basic, accomodation_id, rates_id)

    else:
        pass
        # *** For Testing ***
        existing_seasons = get_data(season_request,
                                    basic)  # I made a copy of this one and renamed it to have find_duplicates at the end.

        existing_rates = get_data(rates_request, basic)
        rates_id = existing_rates[0]['id']


        motopress_data = motopress_rates_data(existing_seasons,
                                              existing_rates)  # Returns a dictionary with end date as key, season_id as value.

        pricelabls_data = get_pricelabs_data(pricelabs_api_key,
                                             pricelabs_id)  # will return a dict with date as key and price as value

        moto_data_to_add = compare_prices(motopress_data, pricelabls_data, rates_request, basic)
        create_rate(moto_data_to_add, rates_request, basic, accomodation_id, rates_id)


        # *** End testing ***


def delete_season(url, date, existing_seasons, basic):
    '''deletes seasons in motopress for past days. This keeps everything clean in motopress and avoids
    having a bunch of not needed information.'''
    for season_date in existing_seasons:
        if season_date['end_date'] == date:
            # print(season_date['end_date'])
            season_id = season_date['id']
            full_url = url + str(season_id)
            response = requests.delete(full_url, auth=basic)
            # print(response.json())
            # print('season id of what will be deleted: ', season_id)
            return season_id


def delete_rate(url, season_id, existing_rates, basic):
    '''Sends a delete request to motopress to delete any not needed rates. Takes the season id as a paramater
    and uses that to figure out which rate is associated with that date. Once it has that, a delete
    request is sent.'''
    for rate in existing_rates:
        if rate['season_prices'][0]['season_id'] == season_id:
            # print('info from within delete_rate', rate['title'])
            rate_id = rate['id']
            full_url = url + str(rate_id)
            print(full_url)
            response = requests.delete(full_url, auth=basic)
            # response = requests.get(full_url, basic)
            print(response.json())


def compare_prices(motopress, pricelabs, rates_request,
                   basic):  # We pass in the request and auth because we will update from here.
    '''Takes in the motopress rates data, pricelabs rates data, and the rates url as paramaters. It compares the
    motopress and pricelabs rates. If they are different, it sends a post request to motopress to update the rate.'''
    # print('motopress', motopress)

    rate_data_to_add = []
    priority = 0
    # print(motopress)
    for data, season_id in motopress.items():
        date = data
        # print('date from compare_prices', data)
        # print('id from compare_prices', season_id)

        if date in pricelabs:
            pricelabs_rate = pricelabs[date]  # output is the rate shown in pricelabs

            entry = {
                "priority": priority,
                "season_id": season_id,
                "base_price": pricelabs_rate,
                "variations": [
                    {
                        "adults": 11,
                        "children": 0,
                        "price": pricelabs_rate + 25
                    },
                    {
                        "adults": 12,
                        "children": 0,
                        "price": pricelabs_rate + 50
                    },
                    {
                        "adults": 13,
                        "children": 0,
                        "price": pricelabs_rate + 75
                    }
                ]
            }
            rate_data_to_add.append(entry)
            priority = priority + 1
    return rate_data_to_add



def motopress_rates_data(existing_seasons, existing_rates):
    '''Uses the existing seasons and existing rates data to compile a dictionary that is used later to compare
    the motopress existing rates to what pricelabs has. It returns a dictionary with the key as the date and the
    value is the season id.'''

    # print('existing seasons: ', existing_seasons)

    moto_dict = {}

    for season in existing_seasons:
        # get the id, then we will need to find the rate that has that id.
        season_id = season['id']
        end_date = season['end_date']
        # print(season_id, end_date)

        moto_dict[end_date] = season_id

    # print(moto_dict)
    return moto_dict


def create_list_of_dates():
    '''Creats a list of dates thats used as a base to know if any dates need to be added to motopress or removed.'''
    list_dates = []
    for i in range(-1, 366):
    # for i in range(-1, 13):
        date_i = datetime.datetime.today() + datetime.timedelta(days=i)
        date_string = date_i.strftime('%Y-%m-%d')
        list_dates.append(date_string)
    return list_dates


def get_data(url, basic):
    '''This is the base function to get data from motopress. its used to get both season data and rates data.
    A bug I found is that the base url will only bring in 10 entries, so an extension to the url is added with a
    loop that will take it through 4 pages showing 100 records per page.'''

    data = []

    for i in range(1, 16):
        # extension = f'?context=view&page={i}&per_page=1'
        extension = f'?page={i}&per_page={25}'
        full_url = url + extension
        response = requests.get(full_url, auth=basic)
        data.extend(response.json())
        # jprint(response.json())

    for i in range(1, 9):
        # extension = f'?context=view&page={i}&per_page=1'
        extension = f'?page={i}&per_page={50}'
        full_url = url + extension
        response = requests.get(full_url, auth=basic)
        data.extend(response.json())
        # jprint(response.json())

    for i in range(1, 6):
        # extension = f'?context=view&page={i}&per_page=1'
        extension = f'?page={i}&per_page={75}'
        full_url = url + extension
        response = requests.get(full_url, auth=basic)
        data.extend(response.json())
        # jprint(response.json())

    for i in range(1, 6):
        # extension = f'?context=view&page={i}&per_page=1'
        extension = f'?page={i}&per_page={100}'
        full_url = url + extension
        response = requests.get(full_url, auth=basic)
        data.extend(response.json())
        # jprint(response.json())

    removed_duplicates = []
    [removed_duplicates.append(x) for x in data if x not in removed_duplicates]
    removed_duplicates_count = len(removed_duplicates)
    print('len of get_data:', removed_duplicates_count)
    # jprint(removed_duplicates)
    return removed_duplicates


def jprint(obj):
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)


def create_season(season_date, url, basic):
    text = {
        "title": f"season {season_date} main post request",
        "description": f"season {season_date}",
        "start_date": f"{season_date}",
        "end_date": f"{season_date}",
        "days": [
            "sunday",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday"
        ],
        "dates": [
            f"{season_date}",
        ]
    }

    # print('text dictionary ', text)

    response = requests.post(url, json=text, auth=basic)
    print('status code', response)
    print('response: ', response.json())
    return response


def create_rate(season_info, url, basic, accomodation_id, rates_id):
    # print(season_stuff_to_add)
    # print('season_prices:', season_prices)

    text = {
        "id": 4186,
        "status": "active",
        "title": "Bearadise Booking Rate",
        "description": "Single rate - main post request",
        "accommodation_type_id": accomodation_id,
        "season_prices": season_info
    }

    # print(text)
    # print('season_info', season_info)
    url = url + str(rates_id) + '/'
    response = requests.post(url, json=text, auth=basic)
    print(response.status_code)
    # print(response.text)
    return response


def get_pricelabs_data(api_key, id):
    # API key and id are hard coded
    url = "https://api.pricelabs.co/v1/listing_prices"

    payload = json.dumps({
        "listings": [
            {
                "id": f"{id}",
                "pms": "airbnb"
            }
        ]
    })
    headers = {
        'X-API-Key': f'{api_key}',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    full_response = json.loads(response.text)

    data = full_response[0]['data']
    print(data)

    # !!! For production. This will get a dictionary with dates as key and prices as values. !!!
    dict_data = {i['date']: i['price'] for i in data}
    # print('dict_data: ', dict_data)

    return dict_data

#
#
#     main(False, moto_key, moto_secret, season_request, rates_request, pricelabs_api_key, pricelabs_id)
