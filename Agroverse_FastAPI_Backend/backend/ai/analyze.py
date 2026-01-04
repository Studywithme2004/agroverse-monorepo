
def analyze_crop(data):
    health = "Good"
    recommendation = "Maintain irrigation and sunlight"
    if data.soil_moisture < 300:
        health = "Dry soil"
        recommendation = "Increase watering"
    return {
        "health": health,
        "recommendation": recommendation
    }
