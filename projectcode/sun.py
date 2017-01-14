
# Calculation taken from
# http://williams.best.vwh.net/sunrise_sunset_algorithm.htm

import math
from datetime import date, timedelta, datetime


def sunrisetoday():
    "Returns sunrise time today"
    today = date.today()
    t = suntime(today.day, today.month, today.year, rise=True)
    thour = int(t)
    tmin =  (t - thour) * 60
    return thour, tmin

def sunsettoday():
    "Returns sunset time today"
    today = date.today()
    t = suntime(today.day, today.month, today.year, rise=False)
    thour = int(t)
    tmin =  (t - thour) * 60
    return thour, tmin

def sunrisetomorrow():
    "Returns sunrise time tomorrow"
    today = date.today()
    tomorrow = today + timedelta(days=1)
    t = suntime(tomorrow.day, tomorrow.month, tomorrow.year, rise=True)
    thour = int(t)
    tmin =  (t - thour) * 60
    return thour, tmin


def suntime(day, month, year, rise=True):
    """Given day month year, if rise is True returns sunrise time, if False return sunset time
          For the todmorden astronomy centre"""
    # latitude, longitude
    # astronomy centre is 53:42:40N 2:09:16W
    latitude = 53.8111
    longitude = -2.1944
    lngHour = longitude/15
    # Taking zenith to be 96 degrees
    zenith = math.radians(96) 
    # first calculate the day of the year
    day = date(year, month, day)
    # N = day of year
    N = day.timetuple().tm_yday
    if rise:
        t = N + ((6 - lngHour) / 24)
    else:
        t = N + ((18 - lngHour) / 24)
    #calculate the Sun's mean anomaly
    M = (0.9856 * t) - 3.289
    Mr = math.radians(M)
    # calculate the Sun's true longitude
    L = M + (1.916 * math.sin(Mr)) + (0.020 * math.sin(2 * Mr)) + 282.634
    while L > 360:
        L = L - 360
    while L < 0:
        L = L + 360
    # calculate the Sun's right ascension
    RA = math.degrees(math.atan(0.91764 * math.tan(math.radians(L))))
    while RA > 360:
        RA = RA - 360
    while RA < 0:
        RA = RA + 360
    # right ascension value needs to be in the same quadrant as L
    Lquadrant  = ( L//90) * 90
    RAquadrant = (RA//90) * 90
    RA = RA + (Lquadrant - RAquadrant)
    # right ascension value needs to be converted into hours
    RA = RA / 15
    # calculate the Sun's declination
    sinDec = 0.39782 * math.sin(math.radians(L))
    cosDec = math.cos(math.asin(sinDec))
    # calculate the Sun's local hour angle
    cosH = (math.cos(zenith) - (sinDec * math.sin(math.radians(latitude)))) / (cosDec * math.cos(math.radians(latitude)))
    if (cosH >  1) and rise:
        # the sun never rises on this location (on the specified date)
        return
    if (cosH < -1) and (not rise):
        # the sun never sets on this location (on the specified date)
        return
    # finish calculating H and convert into hours
    if rise:
        H = 360 - math.degrees(math.acos(cosH))
    else:
        H = math.degrees(math.acos(cosH))
    H = H / 15
    # calculate local mean time of rising/setting
    T = H + RA - (0.06571 * t) - 6.622
    # adjust back to UTC
    UT = T - lngHour
    while UT > 24:
        UT = UT - 24
    while UT < 0:
        UT = UT + 24
    return UT


class Slot(object):

    def __init__(self, startday, sequence):
        self.startday = startday
        self.nextday = startday + timedelta(days=1)
        # The night viewing time
        self.set = int( suntime(startday.day, startday.month, startday.year, rise=False) ) + 1  # +1 to round up
        self.rise = int( suntime(self.nextday.day, self.nextday.month, self.nextday.year, rise=True) ) # auto rounds down
        # sequence 0 is 12 mid day of startday
        # sequence 12 is midnight, or hour zero of nextday
        # sequence 23 is 11 am of nextday
        self.sequence = sequence
        if sequence < 12:
            self.starttime = datetime(startday.year, startday.month, startday.day, hour=sequence+12)
        else:
            self.starttime = datetime(self.nextday.year, self.nextday.month, self.nextday.day, hour=sequence-12)
        if sequence < 11:
            self.endtime = datetime(startday.year, startday.month, startday.day, hour=sequence+13)
        else:
            self.endtime = datetime(self.nextday.year, self.nextday.month, self.nextday.day, hour=sequence-11)

    def __str__(self):
        return str(self.starttime.hour) + ":00 - " + str(self.endtime.hour) + ":00"

    def startday_string(self):
        return self.startday.isoformat()

    def in_daylight(self):
        if (self.starttime.hour > 12) and (self.starttime.hour < self.set):   # evening and earlier than set time
            return True
        if (self.endtime.hour < 12) and (self.endtime.hour > self.rise):      # morning and later than rise time
            return True
        return False




def twoday_slots():
    "Create two lists, equal length, for tonights slots and tomorrow night slots"
    today = date.today()
    tomorrow = today + timedelta(days=1)
    dayafter = today + timedelta(days=2)

    # night one
    one_set = int( suntime(today.day, today.month, today.year, rise=False) )
    one_rise = int( suntime(tomorrow.day, tomorrow.month, tomorrow.year, rise=True) )

    # night two
    two_set = int( suntime(tomorrow.day, tomorrow.month, tomorrow.year, rise=False) )
    two_rise = int( suntime(dayafter.day, dayafter.month, dayafter.year, rise=True) )

    # table start and end hours
    table_start = min(one_set, two_set) + 1  # +1 for observing to start in the hour after sunset
    table_end = max(one_rise, two_rise) - 1  # -1 for observing to end in the hour before sunrise

    night0 = []
    night1 = []

    for seq in range(0, 12):
        if (seq+12) < table_start:
            continue
        night0.append(Slot(today,seq))
        night1.append(Slot(tomorrow,seq))

    for seq in range(12, 24):
        if (seq-12) > table_end:
            continue
        night0.append(Slot(today,seq))
        night1.append(Slot(tomorrow,seq))

    return night0, night1
