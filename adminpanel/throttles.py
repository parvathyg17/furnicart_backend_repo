# adminpanel/throttles.py

from rest_framework.throttling import AnonRateThrottle


class AdminLoginThrottle(AnonRateThrottle):

    rate = "60/min"