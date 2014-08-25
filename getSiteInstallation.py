#!/usr/bin/env python

# Provide this script with an API key and primary access key password to
# get a zip file containing an installation file for each site within
# each client.

import requests
import xmltodict
import os
from optparse import OptionParser
import getpass

parser = OptionParser()
parser.add_option("-t", "--type", type=str, default="remote_worker", help="Use remote_worker or group_policy")

def getClients():
    # Produce of dict with keys of clientID and values of client names
    serviceListClients = {'service': 'list_clients'}
    urlClientList = requests.get(gfiAPI, params=serviceListClients)
    objClientList = xmltodict.parse(urlClientList.text)
    clientIDdict = {}
    for i in range(len(objClientList["result"]["items"]["client"])):
        clientID = str(objClientList["result"]["items"]["client"][i]["clientid"])
        clientName = objClientList["result"]["items"]["client"][i]["name"]
        # Set value of clientID key to client name
        clientIDdict[clientID] = clientName
    return clientIDdict

def getSites(clientID, clientName):
    print "{0} - {1}".format(clientID, clientName)
    clientID = str(clientID)
    list_sites = {'clientid': clientID, 'service': 'list_sites'}
    # Produce a list of tuples containing the folowing:
    # "clientName", "clientID", "siteID", "siteName"
    siteIDlist = []
    urlSiteList = requests.get(gfiAPI, params=list_sites)
    objSiteList = xmltodict.parse(urlSiteList.text)

    try:
        # Try to add site info.  This will only work if the client only has one site.
        # If the client has more than one site, or if there is another issue preventing
        # the addition, the code in the 'except' block will be executed.
        singleSiteID = objSiteList["result"]["items"]["site"]["siteid"]
        singleSiteName = objSiteList["result"]["items"]["site"]["name"]
        siteIDlist.append((clientName, clientID, singleSiteID, singleSiteName))

    except:
        try:
            for site in range(len(objSiteList["result"]["items"]["site"])):
                multipleSiteID = objSiteList["result"]["items"]["site"][site]["siteid"]
                multipleSiteName = objSiteList["result"]["items"]["site"][site]["name"]

                siteIDlist.append((clientName, clientID, multipleSiteID, multipleSiteName))
        except:
            print "Failed to get site info for {0}, ID #{1}".format(clientName, clientID)
            pass
    return siteIDlist

def getSiteInstallationPackage(site, agentType, password):
    clientName = site[0]
    clientID = site[1]
    siteID = site[2]
    siteName = site[3]
    siteName = siteName.replace('/', '')
    password = password

    # Define parameters necessary for installation package request from GFI API
    get_site_installation_package = {'service': 'get_site_installation_package',
                                     'endcustomerid': clientID,
                                     'siteid': siteID,
                                     'password': password,
                                     'type': agentType}

    getSiteInstallationPackageURL = requests.get(gfiAPI, params=get_site_installation_package)

    if getSiteInstallationPackageURL.headers['Content-Type'] == 'application/xml':
        # XML response is only returned on an error, so an XML response is skipped.
        print "{0} - {1} - FAILED: SKIPPING XML RESPONSE".format(clientName,siteName)
    else:
        print "{0} - {1}".format(clientName, siteName)
        zipFileName = "{0}-{1}.zip".format(clientName,siteName)
        if os.path.isfile(zipFileName) == True:
            print "*** Removing existing file: {0} ***".format(zipFileName)
            os.remove(zipFileName)
        installFile = open("{0}-{1}.zip".format(clientName,siteName),'w')
        installFile.write(getSiteInstallationPackageURL.content)
        installFile.close()

def getAllSiteInstallationPackages(agentType, password):
    clientIDdict = getClients()
    clientInfo = []
    for clientID in clientIDdict:
        sites = getSites(int(clientID), clientIDdict[clientID])
        clientInfo.append(sites)
    siteInfo = []
    # Create a list of dicts containing site info.
    # Format of dict is defined by the getSites function
    for client in clientInfo:
        for site in client:
            siteInfo.append(site)
    for site in siteInfo:
        getSiteInstallationPackage(site, agentType, password)

if __name__ == "__main__":
    opts, args = parser.parse_args()
    apiKey = getpass.getpass(prompt='API Key: ')
    primaryKeyPassword = getpass.getpass(prompt='Primary Key Password: ')
    gfiAPI = "https://www.hound-dog.us/api/?apikey=" + apiKey
    getAllSiteInstallationPackages(opts.type, primaryKeyPassword)

