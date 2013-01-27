'''
Created on Dec 6, 2012

@author: David I. Urbina
'''
from construct import Adapter
from time import mktime
from datetime import datetime, timedelta

class NullStringAdapter(Adapter):
    '''
    NullStringAdapter class.
    '''

    def _encode(self, obj, ctx):
        return obj

    def _decode(self, obj, ctx):
        return obj.split('\x00')[0]


class TimeDateAdapter(Adapter):
    '''
    TimeDateAdapter class.
    '''

    def _encode(self, obj, ctx):
        return int(mktime(datetime.timetuple()))

    def _decode(self, obj, ctx):
        return datetime.fromtimestamp(obj)


class TimeDeltaAdapter(Adapter):
    '''
    TimeDeltaAdapter class.
    '''

    def _encode(self, obj, ctx):
        seconds = (obj.days * 86400) + obj.seconds
        return seconds

    def _decode(self, obj, ctx):
        return timedelta(seconds=obj)


class WindowsTimeDateAdapter(Adapter):
    '''
    WindowsTimeDateAdapter class.
    '''
    def _encode(self, obj, ctx):
        unix_time = int(mktime(datetime.timetuple()))
        if unix_time == 0:
            return unix_time

        windows_time = unix_time + 11644473600
        windows_time = windows_time * 10000000
        return windows_time


    def _decode(self, obj, ctx):
        unix_time = obj / 10000000

        if unix_time == 0:
            return datetime.fromtimestamp(obj)

        unix_time = unix_time - 11644473600

        if unix_time < 0:
            unix_time = 0

        return datetime.fromtimestamp(unix_time)


class WindowsTimeDeltaAdapter(Adapter):
    '''
    WindowsTimeDeltaAdapter class.
    '''
    def _encode(self, obj, ctx):
        seconds = (obj.days * 86400) + obj.seconds
        return (seconds * 10000000) + (obj.microseconds * 10)

    def _decode(self, obj, ctx):
        seconds = (obj / 10000000)
        microseconds = (obj % 10000000) / 10
        return timedelta(seconds=seconds, microseconds=microseconds)
