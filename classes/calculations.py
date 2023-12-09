import pytz
from datetime import datetime

class DateTime:
    def __init__(self):
        pass

    def get_current_date():
        est = pytz.timezone('US/Eastern')
        current_time = datetime.now(est)
        formatted_date = current_time.strftime("%m/%d/%Y")

        # Remove leading zero from month
        if formatted_date.startswith("0"):
            formatted_date = formatted_date[1:]

        return formatted_date

    def get_current_time():
        est = pytz.timezone('US/Eastern')
        current_time = datetime.now(est)
        formatted_time = current_time.strftime("%I:%M %p")
        
        # Extract the hour and remove the leading zero if any
        hour, rest_of_time = formatted_time.split(":", 1)
        hour = str(int(hour))
        
        # Reassemble the time string
        formatted_time = f"{hour}:{rest_of_time} (EST)"
        
        return formatted_time