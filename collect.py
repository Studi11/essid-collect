#!/usr/bin/python

import subprocess
import re
import os
import sys
import signal
import tempfile
from time import sleep
from datetime import datetime

# variables
folder = "/usr/share/essid-collect/"
collecting_file = "collecting"
essids_file = "essids.csv"
essids = {}
# essids["testWlan"]=["01-01-2017","ap","client","macs"]


def signal_handler(signal, frame):
        print('\n stopping')
        stop()
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():

    print("in the works!!")
    monInterface = startmon()
    if monInterface==None:
        stop()
    print("monInterface: ."+monInterface+".")
    ret = makeDir()
    if ret == None:
        stop()
    startdump(monInterface)
    collecting()

def stop():
    print("stop")
    stopcollecting()
    stopdump()
    stopmon()
    sys.exit(1)

def startmon():
    print("startmon")
    #search device
    devs = subprocess.check_output(['ifconfig']).decode("utf-8")
    devs = devs.splitlines()
    monInterface = []
    for line in devs:
        if line.find("mon")>=0 or line.find("wlp")==0 or line.find("wlan")==0:
            if line.find("PROMISC")>=0:
                monInterface.append(re.search(".+?(:|\s)",line).group()[:-1])
                print("1 potential monitor interface: ."+re.search(".+?(:|\s)",line).group()[:-1]+".")
    if len(monInterface)>0:
        for i in monInterface:
            if i.find("mon")>=0:
                return i
        return monInterface[0]

    # start monitor interface
    wlanInterface = ""
    for dev in getDevices():
        if dev.find("wlp")>=0 or dev.find("wlan")>=0:
            wlanInterface = dev
            break
    if wlanInterface == "":
        print("No wlan interface found")
        return None

    needsRoot()
    # p = subprocess.Popen(['ifconfig',wlanInterface,'promisc'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p = subprocess.Popen(['airmon-ng','start',wlanInterface], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate()
    p.wait()
    if p.returncode==1:
        print("ifconfig promisc error")
        return None

    devs = subprocess.check_output(['ifconfig']).decode("utf-8")
    devs = devs.splitlines()
    monInterface = []
    for line in devs:
        if line.find("mon")>=0 or line.find("wlp")==0 or line.find("wlan")==0:
            if line.find("PROMISC")>=0 or True:
                monInterface.append(re.search(".+?(:|\s)",line).group()[:-1])
                print("2 potential monitor interface: ."+re.search(".+?(:|\s)",line).group()[:-1]+".")
    if len(monInterface)>0:
        for i in monInterface:
            if i.find("mon")>=0:
                return i
        return monInterface[0]
    else:
        return None

def makeDir():
    needsRoot()
    p = subprocess.Popen(['mkdir','-p',folder], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate()
    if p.returncode==1:
        print("couldn't create folder "+folder)
        return None

    p = subprocess.Popen(['rm','-rf',folder+"*"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate()
    if p.returncode==1:
        print("couldn't delete files from "+folder)
        return None
    return 0

def startdump(monInterface):
    print("startdump")
    purgeFiles(folder, collecting_file+".*\.csv")
    p = subprocess.Popen(['airodump-ng','-w',os.path.join(folder,collecting_file),'--output-format','csv',monInterface], stdout=tempfile.TemporaryFile(), stderr=subprocess.STDOUT)
    return p

def collecting():
    print("collecting\n")

    while (True):
        sleep(5)
        # print("analyze")
        for f in os.listdir(folder):
            if f.find(collecting_file)<0:
                continue

            fi = open(os.path.join(folder,f),"r")
            r = fi.read().splitlines()
            fi.close()

            mode = "before"
            for line in r:
                if (line.find("BSSID")==0):
                    mode = "AP"
                    continue
                if (line.find("Station")==0):
                    mode = "client"
                    continue
                if (len(line)<3):
                    continue

                line = line.split(",")

                if (mode=="AP" and len(line)>13):
                    addnew(line[13].strip(), True, line[0].strip(), line[2].strip())
                if (mode=="client" and len(line)>6):
                    for i in line[6:]:
                        addnew(i.strip(), False, "", line[2].strip())

def addnew(entry, ap, mac, last):
    entry = str(entry).strip()
    if len(entry)<1:
        return

    if not (entry in essids):
        print(entry)
        essids[entry] = {}
        essids[entry]['mac'] = set()

    essids[entry]['last-time'] = str(last)

    if ap:
        essids[entry]['mac'].add(mac)
        essids[entry]['ap'] = "x"
    else:
        essids[entry]['client'] = "x"

def stopcollecting():
    print("stop collecting")
    unionessids()
    writeessidsfile()

def unionessids():
    print("unionessids")

    for f in os.listdir(folder):
        if f.find(essids_file)<0:
            continue

        fi = open(os.path.join(folder, f),"r")
        r = fi.read().splitlines()
        fi.close()
        # essids["testWlan"]=["01-01-2017","ap","client","macs"]
        for line in r:
            line = line.split(",")
            if not line[0] in essids:
                essids[line[0]] = {}
                essids[line[0]]['mac'] = set()
                essids[line[0]]['last-time'] = str(line[1])
            if line[2].find("x")>=0:
                essids[line[0]]['ap']="x"
            if line[3].find("x")>=0:
                essids[line[0]]['client']="x"
            for i in line[4:]:
                if len(i)>=1:
                    essids[line[0]]['mac'].add(i)

def writeessidsfile():
    print("writeessidsfile")
    fi = open(os.path.join(folder,essids_file),"w")
    for k,v in essids.items():
        fi.write(k+",")
        for e in ["last-time","ap","client","mac"]:
            if e in v:
                if type(v[e]) is set:
                    for el in v[e]:
                        fi.write(el+",")
                else:
                    fi.write(v[e]+",")
            else:
                fi.write(",")
        fi.write("\n")
    fi.close()

def stopdump():
    print("stopdump")
    p = subprocess.Popen(['killall','airodump-ng'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    purgeFiles(folder, collecting_file+".*\.csv")

def getMonInterface():
    print("getMonInterface")
    devs = subprocess.check_output(['ifconfig']).decode("utf-8")
    devs = devs.splitlines()
    monInterface = []

def stopmon():
    print("stopmon")
    # stop monitor interface
    devs = subprocess.check_output(['ifconfig']).decode("utf-8")
    devs = devs.splitlines()
    monInterface = []
    for line in devs:
        if line.find("mon")>=0 or line.find("wlp")==0 or line.find("wlan")==0:
            if line.find("PROMISC")>=0 or True:
                monInterface.append(re.search(".+?(:|\s)",line).group()[:-1])
                print("3 potential monitor interface: ."+re.search(".+?(:|\s)",line).group()[:-1]+".")
    monI = ""
    if len(monInterface)>0:
        for i in monInterface:
            if i.find("mon")>=0:
                monI = i
        monI = monInterface[0]
    else:
        monI = ""

    needsRoot()
    # p = subprocess.Popen(['ifconfig',wlanInterface,'-promisc'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p = subprocess.Popen(['airmon-ng','stop',monI], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate()
    if p.returncode==1:
        print("ifconfig -promisc error")
        return None

    return monI

def getDevices():
    devs = subprocess.check_output(["ls","/sys/class/net/"]).decode("utf-8")
    devs = devs.splitlines()
    return devs

def needsRoot():
    if os.geteuid() !=0:
        click.echo("root privileges needed, run with  sudo essid-collect ...")
        sys.exit(1)

def purgeFiles(dir, pattern):
    for f in os.listdir(dir):
        if re.search(pattern, f):
            os.remove(os.path.join(dir,f))


if __name__ == '__main__':
    main()
