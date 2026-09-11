

LOCAL_TRANSPORT_RIDE_ESTIMATES = {
    "Bangkok": 3,
    "Rome": 2,
    "Paris": 2.5,
    "Dubai": 5,
    "Tokyo": 2,
    "Istanbul": 1.5,
}

RIDES_PER_DAY = 4


def get_local_transport_ride_estimate(
    city: str,
) -> float:
    return LOCAL_TRANSPORT_RIDE_ESTIMATES.get(
        city,
        2,
    )