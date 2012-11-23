#!/usr/bin/python
# -*- coding: utf-8 -*-
# ACPI script
# Copyright (C) 2008  Salvo "LtWorf" Tomaselli
#
# this is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# author Salvo "LtWorf" Tomaselli <tiposchi@tiscali.it>

import socket,os
import sys,signal

from subprocess import call
from time import sleep

def get_cpus():
    f=open('/sys/devices/system/cpu/present')
    freq=f.read(4096)
    f.close()
    freq=freq.strip().split('-')
    return range(int(freq[0]),int(freq[1])+1)

def get_frequencies(cpu=0):
    '''Returns a list of available frequencies for the selectec CPU. Usually
    it can be assumed that all the CPUs are the same'''
    f=open('/sys/devices/system/cpu/cpu%d/cpufreq/scaling_available_frequencies'%cpu)
    freq=f.read(4096)
    f.close()
    freq=freq.strip().split(' ')
    
    #converting to Mhz integers
    for i in range(len(freq)):
        freq[i]=int(freq[i]) / 1000
    return freq

def get_governors(cpu=0):
    f=open('/sys/devices/system/cpu/cpu%d/cpufreq/scaling_available_governors'%cpu)
    freq=f.read(4096)
    f.close()
    return freq.strip().split(' ')

#/sys/bus/acpi/drivers/ac/ACPI0003\:00/power_supply/ADP1/online 
def is_plugged():
    f=open('/sys/bus/acpi/drivers/ac/ACPI0003:00/power_supply/ADP1/online')
    if f.read(1)=='0':
        res=False
    else:
        res=True

    f.close()
    return res

def daemonize():
    if os.fork()!=0:
        sys.exit(0)
    #For some VERY VERY odd reason, kde will crash on login (resulting in logout) if that sleep is not there
    sleep(30)
    signal.signal(signal.SIGHUP, signal.SIG_IGN)

def main():
    daemonize()

    if is_plugged():
        plugged()
    else:
        unplugged()

    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect("/var/run/acpid.socket")
    print "Connected to acpid"
    while 1:
        #conn, addr = s.accept()
        for event in s.recv(4096).split('\n'):
            event=event.split(' ')
            if len(event)<2: continue
            print event
            if event[0]=='ac_adapter':
                if event[3]=='00000001': #plugged
                    plugged()
                else: #unplugged
                    unplugged()
            elif event[0]=='button/power':
                power_button()
            elif event[0]=='button/lid':
                if event[2]=='open':
                    lid_open()
                elif event[2]=='close':
                    lid_close()
    #['processor', 'LNXCPU:00', '00000081', '00000000']
    #['processor', 'LNXCPU:01', '00000081', '00000000']
    #['battery', 'PNP0C0A:00', '00000080', '00000001']    

def powersave_cpu(handler,minf,maxf,cpu):

    for i in cpu:
        call(('sudo','cpufreq-set','-g%s' % handler,'-c%d' % i))
        print ('sudo','cpufreq-set','-g%s' % handler,'-c%d' % i)
        call(('sudo','cpufreq-set','-u%dMhz' % maxf,'-d%dMhz' % minf,'-c%d' %i))
        print ('sudo','cpufreq-set','-u%dMhz' % maxf,'-d%dMhz' % minf,'-c%d' %i)

def lock_screen():
    call (('qdbus', 'org.freedesktop.ScreenSaver', '/ScreenSaver','Lock'))

def s2ram():
    call(('sudo','s2ram'))

    #Changes in plug status aren't notified, manual check
    if is_plugged():
        print "woke up as plugged"
        plugged()
    else:
        print "woke up as unplugged"
        unplugged()

##############################################################



def plugged():
    freqs=get_frequencies()
    powersave_cpu('ondemand',min(freqs),max(freqs) ,get_cpus())

def unplugged():
    freqs=get_frequencies()
    powersave_cpu('ondemand',min(freqs),min(freqs),get_cpus())

def lid_close():
    lock_screen()
    s2ram()

def lid_open():
    pass

def power_button():
    lock_screen()
    if not is_plugged():
        s2ram()


if __name__=='__main__':
    main()
