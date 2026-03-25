from enum import Enum

class DayOfWeek(str, Enum):
    MONDAY = 'Monday'
    TUESDAY = 'Tuesday'
    WEDNESDAY = 'Wednesday'
    THURSDAY = 'Thursday'
    FRIDAY = 'Friday'
    SATURDAY = 'Saturday'
    SUNDAY = 'Sunday'

class TimePeriod(str, Enum):
    OVERNIGHT = 'Overnight'
    EARLY_MORNING = 'Early Morning'
    AM_PEAK = 'AM Peak'
    MIDDAY = 'Midday'
    EARLY_AFTERNOON = 'Early Afternoon'
    PM_PEAK = 'PM Peak'
    EVENING = 'Evening'
