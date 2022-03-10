from django.shortcuts import render
from django.http import HttpResponse
import json
import requests
from datetime import date, timedelta
TODAY = date.today()
# Create your views here.


def hello(request):
    return HttpResponse('Hello, user!')


def view_data(request):
    has_data, connected, consistent = False, False, False
    day = TODAY
    top_three = []
    units_available, units_occupied, quarantined, nonclose = 0, 0, 0, 0
    countday = 0  # will not retrieve > 7 days in the past
    # error handling: connection issues
    try:
        centers = request_occupancy(day.strftime("%d/%m/%Y"))
        confines = request_nonconfined(day.strftime("%d/%m/%Y"))
        connected = True
    except requests.exceptions.RequestException as e:
        print(e)

    if connected:
        # retrieve latest data if current day is unavailable
        while not (centers and confines) and countday <= 7:
            day -= timedelta(1)
            countday += 1
            centers = request_occupancy(day.strftime("%d/%m/%Y"))
            confines = request_nonconfined(day.strftime("%d/%m/%Y"))
    # retrieve relevant information if both sources have data
    if centers and confines:
        has_data = True

        for center in centers:
            units_occupied += center['Current unit in use']
            units_available += center['Ready to be used (unit)']
            quarantined += center['Current person in use']

        centers.sort(reverse=True, key=lambda x: x['Ready to be used (unit)'])

        for i in range(3):
            top_three.append(
                {"name": centers[i]['Quarantine centres'], "units": centers[i]['Ready to be used (unit)']})

        nonclose, close = confines[0]['Current number of non-close contacts'], confines[0]['Current number of close contacts of confirmed cases']
        # check data consistency
        if close + nonclose == quarantined:
            consistent = True
    # fill in context for browser display
    context = {
        "connected": connected,
        "has_data": has_data,
        "data": {
            "date": day,
            "units_available": units_available,
            "units_in_use": units_occupied,
            "persons_quarantined": quarantined,
            "non_close_contacts": nonclose,
            "count_consistent": consistent,
        },
        "centres": top_three,
    }
    return render(request, 'dashboard3.html', context=context)


def request_occupancy(date):
    data = {
        "resource": "http://www.chp.gov.hk/files/misc/occupancy_of_quarantine_centres_eng.csv",
        "section": 1,
        "format": "json",
        "filters": [
                    [1, "eq", [date]],
        ]
    }
    params = {"q": json.dumps(data)}
    r = requests.get('https://api.data.gov.hk/v2/filter', params=params)
    centers = r.json()
    return centers


def request_nonconfined(date):
    data = {
        "resource": "http://www.chp.gov.hk/files/misc/no_of_confines_by_types_in_quarantine_centres_eng.csv",
        "section": 1,
        "format": "json",
        "filters": [
                    [1, "eq", [date]],
        ]
    }
    params = {"q": json.dumps(data)}
    r = requests.get('https://api.data.gov.hk/v2/filter', params=params)
    confines = r.json()
    return confines
