import requests
from datetime import datetime, timedelta
from dotenv import find_dotenv, load_dotenv
import os

def tripPossible(start_date, end_date, now_date):
    if (now_date + timedelta(days=16)).date() >= end_date or now_date.date() < start_date:
        return False
    else:
        return True

def categorization_clothings(items):
    category_dictionary = dict()
    for item in items:
        cat = items[item]['category']
        if cat not in category_dictionary:
            category_dictionary[cat] = {item : items[item]}
        else:
            category_dictionary[cat][item] = items[item]
    return category_dictionary


class WardrobeTrip:
    root_url = "https://api.openweathermap.org/data/2.5/forecast/daily?"
    api_key = os.getenv("WEATHER_API_KEY")

    def __init__(self, id, destination, start_date, end_date, occasion_days, latitude, longitude, wardrobe):
        self.id = id
        self.destination = destination
        self.start_date = start_date
        self.end_date = end_date
        self.sport_days, self.formal_days, self.casual_days = int(occasion_days.split('%')[2]), int(occasion_days.split('%')[1]), int(occasion_days.split('%')[0])
        self.latitude = latitude
        self.longitude = longitude
        self.length = (self.end_date - self.start_date).days + 2
        self.request = (requests.get(f"{WardrobeTrip.root_url}lat={self.latitude}&lon={self.longitude}&cnt={16}&appid={WardrobeTrip.api_key}")).json()
        self.result_list = [self.request['list'][i] for i in range((self.start_date - (datetime.now()).date()).days, self.length + 1)]
        self.weather_conditions = self.get_weather_conditions()
        self.temperature_avg_extrema = self.get_temperature_avg_extrema()
        self.temperature_avg = self.get_temperature_avg()
        self.climate = self.classify_climate()
        self.user_wardrobe = wardrobe

    def get_weather_conditions(self):
        conditions = set()
        for day in self.result_list:
            if day['weather'][0]['main'] not in conditions:
                conditions.add(day['weather'][0]['main'])
        return conditions

    def get_temperature_avg_extrema(self):
        minima = 0
        maxima = 0
        for day in self.result_list:
            minima += day['temp']['min'] - 273.15
            maxima += day['temp']['max'] - 273.15
        l = [maxima/len(self.result_list), minima/len(self.result_list)]
        return tuple(l)

    def get_temperature_avg(self):
        temperature_days = []
        for day in self.result_list:
            temperature_days.append(day['temp']['day'] - 273.15)
        return temperature_days

    def classify_climate(self):
        temperature_extrema = self.get_temperature_avg_extrema()
        temperature = (temperature_extrema[0] + temperature_extrema[1]) / 2
        if temperature > 19:
            return "warm"
        elif temperature < 11:
            return "cold"
        else:
            return "moderate"

def createWardrobe(trip):
    used_casual_shirts = []
    used_casual_underwear = []
    used_casual_socks = []
    used_casual_shoes = []

    used_sport_shirts = []
    used_sport_underwear = []
    used_sport_socks = []
    used_sport_shoes = []

    used_suits = []
    used_formal_socks = []
    used_formal_shoes = []
    used_formal_shirts = []

    used_jackets = []

    used_casual_bottoms = []
    used_casual_sweater = []
    used_sport_bottoms = []
    used_sport_sweater = []
    climate = trip.climate
    weather = trip.weather_conditions
    total_days = trip.length
    casual_days = trip.casual_days
    formal_days = trip.formal_days
    sport_days = trip.sport_days

    def get_item_by_occasion(category, occasion):
        return [item for item in trip.user_wardrobe[category] if trip.user_wardrobe[category][item]['occasion'] == occasion]


    def check_and_fill_items(other_items, category, casual_items, required_count, used_items):
        available_items = [item for item in casual_items if item not in used_items]
        available_count = len(available_items)
        if len(other_items) + available_count >= required_count:
            other_items.extend(available_items[:required_count-len(other_items)])
            return True
        else:
            return False

    casual_socks = get_item_by_occasion("socks", "casual")
    casual_shirts = get_item_by_occasion("shirt", "casual")
    casual_underwear = get_item_by_occasion("underwear", "casual")
    casual_shoes = get_item_by_occasion("shoes", "casual")

    if casual_shoes:
        used_casual_shoes=[casual_shoes[0]]
    else:
        return None

    used_casual_shirts = casual_shirts[:casual_days]
    if len(used_casual_shirts) < casual_days:
        return None
    used_casual_underwear = casual_underwear[:(casual_days + formal_days if casual_days + formal_days < total_days else total_days)]
    if len(used_casual_underwear) < casual_days:
        return None
    used_casual_socks = casual_socks[:casual_days]
    if len(used_casual_socks) < casual_days:
        return None

    if sport_days>0:
        sport_shirts = get_item_by_occasion("shirt", "sport")
        sport_underwear = get_item_by_occasion("underwear", "sport")
        sport_socks = get_item_by_occasion("socks", "sport")
        sport_shoes = get_item_by_occasion("shoes", "sport")

        used_sport_shirts = sport_shirts[:sport_days]
        if len(used_sport_shirts) < sport_days:
            if not check_and_fill_items(used_sport_shirts, "shirt", casual_shirts, sport_days, used_casual_shirts):
                return None

        used_sport_underwear = sport_underwear[:sport_days]
        print(sport_underwear)
        if len(used_sport_underwear) < sport_days:
            if not check_and_fill_items(used_sport_underwear, "underwear", casual_underwear, sport_days, used_casual_underwear):
                return None

        used_sport_socks = sport_socks[:sport_days]
        if len(used_sport_socks) < sport_days:
            if not check_and_fill_items(used_sport_socks, "socks", casual_socks, sport_days, used_casual_socks):
                return None

        used_sport_shoes = []
        for shoes in sport_shoes:
            if trip.user_wardrobe['shoes'][shoes]['weather'].capitalize() in trip.weather_conditions:
                used_sport_shoes.append(shoes)
                break
        if not used_sport_shoes:
            used_sport_shoes.append(sport_shoes[0])

    if formal_days>0:
        used_suits = []
        if 1 <= formal_days <= 5:
            formal_suits = [item for item in trip.user_wardrobe['suit']]
            formal_suits.sort(key=lambda x: trip.user_wardrobe["suit"][x]['preference'], reverse=True)
            used_suits.append(formal_suits[1])
        elif 6 <= formal_days <= 11:
            formal_suits = [item for item in trip.user_wardrobe["suit"]]
            formal_suits.sort(key=lambda x: trip.user_wardrobe["suit"][x]['preference'], reverse=True)
            used_suits.append(formal_suits[2])
        else:
            formal_suits = [item for item in trip.user_wardrobe["suit"]]
            formal_suits.sort(key=lambda x: trip.user_wardrobe["suit"][x]['preference'], reverse=True)
            used_suits.append(formal_suits[3])
        formal_shirts = [item for item in trip.user_wardrobe["shirt"] if trip.user_wardrobe["shirt"][item]["occasion"] == "formal"]
        used_formal_shirts = formal_shirts[:formal_days]

        socks_formal = get_item_by_occasion("socks", "formal")
        if len(socks_formal) < formal_days:
            return None
        used_formal_socks = socks_formal[:formal_days]
        shoes_formal = get_item_by_occasion("shoes", "formal")
        if not shoes_formal:
            return None
        used_formal_shoes = []
        for shoes in shoes_formal:
            if trip.user_wardrobe["shoes"][shoes]['weather'].capitalize() in trip.weather_conditions:
                used_formal_shoes.append(shoes)
                break
        if not used_formal_shoes:
            used_formal_shoes.append(shoes_formal[0])

    if climate == "warm":
        casual_shorts = [item for item in trip.user_wardrobe["bottoms"] if trip.user_wardrobe["bottoms"][item]["length"] == "shorts" and trip.user_wardrobe["bottoms"][item]["occasion"] == "casual"]
        casual_bottoms = [item for item in trip.user_wardrobe["bottoms"] if trip.user_wardrobe["bottoms"][item]["length"] == "regular" and trip.user_wardrobe["bottoms"][item]["occasion"] == "casual"]
        sport_shorts = [item for item in trip.user_wardrobe["bottoms"] if trip.user_wardrobe["bottoms"][item]["length"] == "shorts" and trip.user_wardrobe["bottoms"][item]["occasion"] == "sport"]
        sport_bottoms = [item for item in trip.user_wardrobe["bottoms"] if trip.user_wardrobe["bottoms"][item]["length"] == "regular" and trip.user_wardrobe["bottoms"][item]["occasion"] == "sport"]
        casual_sweater_w = [item for item in trip.user_wardrobe["sweater"] if trip.user_wardrobe["sweater"][item]["climate"] == "warm" and item["occasion"] == "casual"]
        casual_sweater_m = [item for item in trip.user_wardrobe["sweater"] if trip.user_wardrobe["sweater"][item]["climate"] == "moderate" and item["occasion"] == "casual"]
        used_casual_bottoms = casual_shorts[:int(casual_days/3)+1]
        used_casual_bottoms.extend(sport_shorts[:int(sport_days/3)+1])

        if casual_bottoms:
            used_casual_bottoms.append(casual_bottoms[0])
        if sport_bottoms:
            used_casual_bottoms.append(sport_bottoms[0])
        if casual_sweater_m or casual_sweater_w:
            used_casual_sweater = [casual_sweater_w[0] if casual_sweater_w else casual_sweater_m[0]]
        if 'Rain' in weather:
            rain_jackets = [item for item in trip.user_wardrobe["jacket"] if trip.user_wardrobe["jacket"][item]["weather"] == "rain" and trip.user_wardrobe["jacket"][item]["climate"] == "warm"]
            used_casual_jackets = [rain_jackets[0]] if rain_jackets else []

    elif climate == "moderate":
        casual_bottoms = [item for item in trip.user_wardrobe["bottoms"] if trip.user_wardrobe["bottoms"][item]["length"] == "regular" and trip.user_wardrobe["bottoms"][item]["occasion"] == "casual"]
        sport_bottoms = [item for item in trip.user_wardrobe["bottoms"] if trip.user_wardrobe["bottoms"][item]["occasion"] == "sport"]

        used_casual_bottoms = casual_bottoms[:int(casual_days/3)+1]
        used_sport_bottoms = sport_bottoms[:int(sport_days/3)+1]

        casual_sweater = [item for item in trip.user_wardrobe["sweater"] if (trip.user_wardrobe["sweater"][item]["climate"] == "moderate" or trip.user_wardrobe["sweater"][item]["climate"] == "cold") and trip.user_wardrobe["sweater"][item]["occasion"] == "casual"]
        sport_sweater = [item for item in trip.user_wardrobe["sweater"] if (trip.user_wardrobe["sweater"][item]["climate"] == "moderate" or trip.user_wardrobe["sweater"][item]["climate"] == "cold") and trip.user_wardrobe["sweater"][item]["occasion"] == "sport"]
        used_casual_sweater = casual_sweater[:int(casual_days/3)+1]
        if sport_sweater:
            if sport_days<6:
                used_sport_sweater = [sport_sweater[0]]
            else:
                used_sport_sweater = sport_sweater[:2]

        if 'Rain' in weather:
            rain_jackets = [item for item in trip.user_wardrobe["jacket"] if trip.user_wardrobe["jacket"][item]["weather"] == "rain" and trip.user_wardrobe["jacket"][item]["climate"] == "moderate"]
            used_jackets = [rain_jackets[0]] if rain_jackets else []

    elif climate == "cold":
        casual_bottoms = [item for item in trip.user_wardrobe["bottoms"] if trip.user_wardrobe["bottoms"][item]["length"] == "regular" and trip.user_wardrobe["bottoms"][item]["occasion"] == "casual"]
        sport_bottoms = [item for item in trip.user_wardrobe["bottoms"] if trip.user_wardrobe["bottoms"][item]["occasion"] == "sport"]

        used_casual_bottoms = casual_bottoms[:int(casual_days / 3)+1]
        used_sport_bottoms = sport_bottoms[:int(sport_days / 3)+1]

        casual_sweater = [item for item in trip.user_wardrobe["sweater"] if (trip.user_wardrobe["sweater"][item]["climate"] == "moderate" or trip.user_wardrobe["sweater"][item]["climate"] == "cold") and trip.user_wardrobe["sweater"][item]["occasion"] == "casual"]
        sport_sweater = [item for item in trip.user_wardrobe["sweater"] if (trip.user_wardrobe["sweater"][item]["climate"] == "moderate" or trip.user_wardrobe["sweater"][item]["climate"] == "cold") and trip.user_wardrobe["sweater"][item]["occasion"] == "sport"]
        used_casual_sweater = casual_sweater[:int(casual_days / 3)+1]
        if sport_sweater:
            if sport_days < 6:
                used_sport_sweater = [sport_sweater[0]]
            else:
                used_sport_sweater = sport_sweater[:2]

        used_jackets = []
        if 'Snow' in weather:
            print("snow")
            snow_jackets = [item for item in trip.user_wardrobe["jacket"] if (trip.user_wardrobe["jacket"][item]["climate"] == "moderate" or trip.user_wardrobe["jacket"][item]["climate"] == "cold") and trip.user_wardrobe["jacket"][item]["weather"]=="snow" and trip.user_wardrobe["jacket"][item]["occasion"] != "sport"]
            if snow_jackets:
                used_jackets.append(snow_jackets[0])
            else:
                rain_jackets = [item for item in trip.user_wardrobe["jacket"] if (trip.user_wardrobe["jacket"][item]["climate"] == "moderate" or trip.user_wardrobe["jacket"][item]["climate"] == "cold") and trip.user_wardrobe["jacket"][item]["weather"] == "rain" and trip.user_wardrobe["jacket"][item]["occasion"] != "sport"]
                if rain_jackets:
                    used_jackets.append(rain_jackets[0])
                else:
                    jackets = [item for item in trip.user_wardrobe["jacket"] if (trip.user_wardrobe["jacket"][item]["climate"] == "moderate" or trip.user_wardrobe["jacket"][item]["climate"] == "cold") and trip.user_wardrobe["jacket"][item]["occasion"] != "sport"]
                    if jackets:
                        used_jackets.append(jackets[0])
                    else:
                        return None
        elif 'Rain' in weather:
            print("rain")
            rain_jackets = [item for item in trip.user_wardrobe["jacket"] if
                            (trip.user_wardrobe["jacket"][item]["climate"] == "moderate" or
                             trip.user_wardrobe["jacket"][item]["climate"] == "cold") and trip.user_wardrobe["jacket"][item]
                            ["weather"] == "rain" and trip.user_wardrobe["jacket"][item]["occasion"] != "sport"]
            if rain_jackets:
                used_jackets.append(rain_jackets[0])
            else:
                jackets = [item for item in trip.user_wardrobe["jacket"] if
                           (trip.user_wardrobe["jacket"][item]["climate"] == "moderate" or
                            trip.user_wardrobe["jacket"][item]["climate"] == "cold") and trip.user_wardrobe["jacket"][item]
                           ["occasion"] != "sport"]
                if jackets:
                    used_jackets.append(jackets[0])
                else:
                    return None
        else:
            print("this")
            jackets = [item for item in trip.user_wardrobe["jacket"] if (trip.user_wardrobe["jacket"][item]["climate"] == "moderate" or trip.user_wardrobe["jacket"][item]["climate"] == "cold") and trip.user_wardrobe["jacket"][item]["occasion"] != "sport"]
            used_jackets.append(jackets[0])
        print(trip.weather_conditions)
    combined_list = (
            used_casual_shirts +
            used_casual_underwear +
            used_casual_socks +
            used_casual_shoes +
            used_sport_shirts +
            used_sport_underwear +
            used_sport_socks +
            used_sport_shoes +
            used_suits +
            used_formal_socks +
            used_formal_shoes +
            used_jackets +
            used_casual_bottoms +
            used_casual_sweater +
            used_sport_bottoms +
            used_sport_sweater +
            used_formal_shirts
    )
    return combined_list
