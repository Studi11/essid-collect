# essid-collect
Collect Essids of surrounding WLAN Access Points and ones devices around you shout out

## Dependencies
This tool uses airodump-ng to look for wlan traffic.
To put your wireless device in promiscuous mode it uses ifconfig. Ensure you are able to put your wireless card into promisc mode (```sudo ifconfig [device] promisc```, where device is something like wlan0 or wlp3s0, which you can find out with ```ifconfig```)

## Usage
At the moment you only can call ```python collect.py``` and it runs without parameters. To quit hit Ctrl-C, which runs the cleanup process and finishes the script. It temporarely saves the airodump-output in the folder '/usr/share/essid-collect/', where also the permament essids.csv is stored, with information about essids.

## Output
While you run this tool you can see following output on the screen:
```
in the works!!
startmon
Monitor interface: wlp3s0
startdump
collecting

essids

 stopping
stop
stop collecting
unionessids
writeessidsfile
stopdump
stopmon
```
where essids is a updated list of all essids collected.
The file 'essids.csv' looks as follows:
```
essid1,2017-05-31 16:04:37,x,,mac:address,another:mac:address
essid2,2017-05-31 16:04:16,,x,,

```
You best open it in a program like LibreOffice calc, where csv files are shown nicely.

The first column contains all collected essids, the second when it found this essid last.
The third column contains an 'x' when your device saw this essid from an Access Point. The fourth column contains an 'x' if a device shouted out this essid as a know essid.

The rest of the line is filled with mac adresses of access points, which represent this essid.
