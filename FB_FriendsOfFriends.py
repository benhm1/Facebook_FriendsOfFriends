'''
Python script to find the number of friends of friends you have on 
Facebook. Note that this is a conservative estimate, since some friends
will have settings such that you can only see mutual friends and not
all of their friends.

Based on Priyanka Singh's Selenium script, with some modifications.
http://selenium-success-mantra.blogspot.com/2014/03/selenium-printing-names-of-all-facebook.html

Ben M., Spring 2016
'''

import re
import os
import sys
import json
import time
import numpy
import getpass
from selenium import webdriver

TMP_DIR = 'FB_Friends_Tmp'

def getDriver(uid, passwd):

    driver = webdriver.Firefox()
    driver.get("http://facebook.com")
    driver.implicitly_wait(5)
    driver.find_element_by_name("email").send_keys(uid)
    driver.find_element_by_name("pass").send_keys(passwd)
    driver.find_element_by_id("loginbutton").click()
    driver.implicitly_wait(3)
    return driver
    
def getFriendIDsByID( driver, fid, num, totLen ):

    driver.get("http://facebook.com/{0}/friends".format(fid))
    
    numFriends = int(''.join(driver.find_element_by_class_name('_3d0').text.split(',')))
    numTicks = numFriends / 20 + 15
    
    for i in range( numTicks ):
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        time.sleep(1)
        pct = int( (i * 100 / numTicks) / 0.86 )
        if pct >= 100:
            pct = '~100'
        else:
            pct = str(pct)
        print "\r[%4d/%4s] %s -> Scrolling ... ( %3s%% )" % (num, totLen, fid, pct),
        sys.stdout.flush()

    flag=2

    uls_beforeScroll =len(driver.find_elements_by_xpath("//div[@id='pagelet_timeline_app_collection_1155995189:2356318349:2']/ul"))
    while(flag > 0):
        print "\r[%4d/%4s] %s -> Scrolling ... ( ~100%% )" % (num, totLen, fid),
        sys.stdout.flush()
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        time.sleep(1)
        uls_afterScroll = len(driver.find_elements_by_xpath("//div[contains(@id,'pagelet_timeline_app_collection_')]/ul"))    
        if(uls_afterScroll == uls_beforeScroll):
            flag -= 1
        else:
            uls_beforeScroll = uls_afterScroll
            flag = 2
            
    name=""
    no=0
    
    names = driver.find_elements_by_xpath("//div[@class='fsl fwb fcb']")

    sys.stdout.write('\r' + ' ' * 70 )
    sys.stdout.flush()

    ret = set()
    for i, name in enumerate(names):
        if len(names) > 100:
            if i % (len(names) / 50) == 0 :
                sys.stdout.write('\r[%4d/%4s] %s -> Parsing Friends  %d%%.' % (num, totLen, fid,  min( 100, 2 * i / (len(names) / 50)) ) )
                sys.stdout.flush()

        elt = name.find_element_by_tag_name("a")
        link = elt.get_attribute('href')
        if link.endswith('friends_tab'):
            link = link[ len('https://www.facebook.com/') : ]
            uid = link.split('?')[0]
            ret.add(uid)

    with open('{0}/{1}.json'.format(TMP_DIR, fid), 'w') as fd:
        fd.write( json.dumps( list(ret) ) )

    return ret

def parseResults():

    
    files = os.listdir(TMP_DIR)
    files = [ x for x in files if x.endswith('.json') ]
    
    s = set()
    lens = []
    
    for each in files:
        with open( '{0}/{1}'.format(TMP_DIR, each) ) as fd:
            l = json.load( fd )
            lens.append( len(l) )
            s = s.union( set(l) )
    lens.sort()

    print "Total Friends of Friends: ", len(s)
    print "Five Number Summary of Number of Friends, of your friends,"
    print min(lens), lens[ len(lens) / 4 ], lens[ len(lens) / 2], lens[ len(lens) * 3 / 4 ], max(lens)
    print "Mean Number of Friends, of your friends: ", numpy.mean( lens )

def main():

    print '''

Facebook Friend of Friend Counter 1.0

You may know how many friends you have on Facebook, but how many friends of
friends do you have on Facebook? It's probably more than you think!

Note: This takes a while to run (~90 seconds per friend). Intermediate
progress is saved in a temporary folder, so feel free to quit and restart
as needed.

'''


    uid = raw_input("Enter your Facebook ID: ")
    passwd = getpass.getpass("Enter your Facebook password: ")

    d = getDriver(uid, passwd)
    
    # Initialize temporary directory
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)
    
    # Get my own friends
    if os.path.exists( "{0}/{1}.json".format(TMP_DIR, uid) ):
        mine = json.load( open("{0}/{1}.json".format(TMP_DIR, uid) ) )
    else:
        mine = getFriendIDsByID( d, uid, 0, "???" )
        
    # For each friend, get their friends
    for i, each in enumerate(mine):
        if each == 'profile.php':
            continue
        print "\r[%4d/%4d] %s -> Starting" % (i+1, len(mine), each),
        try:
            with open( '{0}/{1}.json'.format(TMP_DIR, each), 'r' ) as fd:
                pass
        except:
            getFriendIDsByID( d, each, i+1, str(len(mine)) )
        print "\r[%4d/%4d] %s -> " % (i+1, len(mine), each), ' ' * 50,
        print "\r[%4d/%4d] %s -> Done" % (i+1, len(mine), each)

    # Display results
    parseResults()

    print "Done. Remove {0} at your convenience.".format( TMP_DIR )


if __name__ == '__main__':
    main()
