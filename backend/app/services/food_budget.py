FOOD_DAILY_ESTIMATES = {
    "Thailand": {
        "Fast food": 15,
        "Budget restaurant": 25,
        "Mid-range restaurant": 45,
        "Mixed": 35,
    },
    "Italy": {
        "Fast food": 12,
        "Budget restaurant": 22,
        "Mid-range restaurant": 45,
        "Mixed": 32,
    },
    "France": {
        "Fast food": 15,
        "Budget restaurant": 25,
        "Mid-range restaurant": 50,
        "Mixed": 35,
    },
    "United Arab Emirates": {
        "Fast food": 20,
        "Budget restaurant": 35,
        "Mid-range restaurant": 65,
        "Mixed": 45,
    },
    "Japan": {
        "Fast food": 10,
        "Budget restaurant": 18,
        "Mid-range restaurant": 40,
        "Mixed": 28,
    },
    "Turkey": {
        "Fast food": 8,
        "Budget restaurant": 15,
        "Mid-range restaurant": 30,
        "Mixed": 22,
    },
}


def get_food_daily_estimate(
    country: str | None,
    food_preference: str,
) -> float:
    country_estimates = FOOD_DAILY_ESTIMATES.get(
        country,
        FOOD_DAILY_ESTIMATES["Italy"],
    )

    return country_estimates.get(
        food_preference,
        country_estimates["Mixed"],
    )