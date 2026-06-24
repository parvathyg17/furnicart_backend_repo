from django.conf import settings

import razorpay


def get_razorpay_client():

    return razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET,
        ),
    )
