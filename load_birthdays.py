import sys
from collections import namedtuple
from icalendar import Calendar, Event


def _name(event):
    return str(event['summary']).replace("'s birthday", "")

def _birthdate(event):
    return event['DTSTART'].dt


def yield_birthdays(ics_filepath):
    """ Returns generator of Birthday tuples from ics file"""
    with open(ics_filepath, 'r+') as f:
        cal = Calendar.from_ical(f.read())
        return ( (_name(e), _birthdate(e))
                for e in cal.walk('vevent') if e['summary'] )

def insert_birthdays(ics_filepath):
    for name, birthday in yield_birthdays(ics_filepath):
        print(name, birthday)

if __name__ == '__main__':
    try:
        _, path = sys.argv
    except IndexError:
        print('Usage: load_birthdays.py <ics_filepath>')
        sys.exit(1)
    insert_birthdays(path)
