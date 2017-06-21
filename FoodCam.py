import RPi.GPIO as GPIO
import time
import os
import pycurl
from StringIO import StringIO
from urllib import urlencode
import json
import threading
import settings

#GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(17, GPIO.OUT) #blue
GPIO.setup(18, GPIO.OUT) #red
GPIO.setup(22, GPIO.OUT) #amber
GPIO.setup(23, GPIO.OUT) #green
GPIO.output(17, set) #blue led off
GPIO.output(18, settings.off) #red led off
GPIO.output(22, settings.off) #amber led off

buffer = StringIO()
dropbox = pycurl.Curl()
dropbox.setopt(dropbox.URL,'localhost:8080/0/action/snapshot')
slack = pycurl.Curl()
#slack.setopt(slack.URL,settings.slackUrl)
slack.setopt(slack.URL,settings.slackUrl)#foodcam-test channel url
slack.setopt(slack.HTTPHEADER,['Accept: application/json'])
slack.setopt(slack.POST,1)
slackTest = pycurl.Curl()
slackTest.setopt(slack.URL,settings.slackTestUrl)
slackTest.setopt(slack.HTTPHEADER,['Accept: application/json'])
slackTest.setopt(slack.POST,1)
slackTest.setopt(slackTest.WRITEDATA,buffer)

GPIO.output(23, settings.off) #green led off

network_warning = False


def ping():
    threading.Timer(60.0, ping).start()#300
    timer = time.gmtime()
    slackTest.setopt(slackTest.POSTFIELDS,'{"text":"ping foodcam v1: '+time.strftime('%b %d %Y %H:%M:%S',timer)+'"}')
    slackTest.perform()
    network_warning = (slackTest.getinfo(pycurl.RESPONSE_CODE) != 200)
    if network_warning:
        print("Network issue: "+str(slackTest.getinfo(pycurl.RESPONSE_CODE)))
    print("button ping: "+time.strftime('%b %d %Y %H:%M:%S',timer))

def blink():
    GPIO.output(17, settings.on) #blue led on
    if network_warning:
        GPIO.output(18, settings.on) #red led on
    time.sleep(1)
    GPIO.output(17, settings.off) #blue led off
    if network_warning:
        GPIO.output(18, settings.off) #red led off
    threading.Timer(1.0, blink).start()

def capture(channel):
    if network_warning:
        GPIO.output(18, settings.on) #red led on
        time.sleep(0.1)
        GPIO.output(18, settings.off) #red led off
        time.sleep(0.1)
        GPIO.output(18, settings.on) #red led on
        time.sleep(0.1)
        GPIO.output(18, settings.off) #red led off
        time.sleep(0.1)
        GPIO.output(18, settings.on) #red led on
        time.sleep(0.1)
        GPIO.output(18, settings.off) #red led off
        time.sleep(0.1)
        GPIO.output(18, settings.on) #red led on
        time.sleep(0.1)
        GPIO.output(18, settings.off) #red led off
        time.sleep(0.1)
    else:
        GPIO.output(18, settings.on) #red led on
        print('Button Pressed, channel '+str(channel))
        dropbox.perform()
        time.sleep(1)
        GPIO.output(18, settings.off) #red led off
        GPIO.output(22, settings.on) #amber led on
        os.system('bash /home/pi/FoodCam/dropbox_uploader.sh upload /home/pi/motion/lastsnap.jpg /')
        time.sleep(1)
        filename = os.readlink('/home/pi/motion/lastsnap.jpg')
        print(filename)
        bashIO = os.popen('bash /home/pi/FoodCam/dropbox_uploader.sh share /'+filename).read()
        print(bashIO)
        url = bashIO.split('link: ')[1].replace('dl=0\n','raw=1')
        print("dropbox url: "+str(url))
        data = {'attachments':[{
            'fallback':'Should be an image of tasty surplus food',
            'text':'Hello '+settings.recipient+', there is surplus food available in '+settings.location,
            'image_url':str(url)
        }]}
        print(data)
        js = json.dumps(data)
        slack.setopt(slack.POSTFIELDS,js)
        slack.perform()
        GPIO.output(22, settings.off) #amber led off
        GPIO.output(23, settings.on) #green led on
        print('sent to slack')
        time.sleep(3)
        GPIO.output(23, settings.off) #green led off

GPIO.add_event_detect(4, GPIO.FALLING, callback=capture, bouncetime=20000)

def exit():
    GPIO.cleanup() #Clean up GPIO on CTRL+C exit

