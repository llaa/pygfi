import requests
import xmltodict
import os
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-t", "--type", type=str, default="remote_worker")
parser.add_option("-p", "--password", type=str, default="default")
parser.add_option("-a", "--apikey", type=str, default="default")

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
    list_sites = {'service': 'list_sites'}
    # Produce a list of tuples containing the folowing:
    # "clientName", "clientID", "siteID", "siteName"
    siteIDlist = []
    clientID = str(clientID)
    urlSiteList = requests.get(gfiAPI + "&clientid=" + clientID, params=list_sites)
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
            print "Failed to get site info for {0}, ID #{1} - {2}".format(clientName, clientID, urlSiteList.url)
            pass
    return siteIDlist

def getSiteInstallationPackage(site, agentType, password):
    clientName = site[0]
    clientID = site[1]
    siteID = site[2]
    siteName = site[3]
    siteName = siteName.replace('/', '')
    password = password

    print "{0} - {1}".format(clientName, siteName)

    # Define parameters necessary installation package request from GFI API
    get_site_installation_package = {'service': 'get_site_installation_package',
                                     'endcustomerid': clientID,
                                     'siteid': siteID,
                                     'password': password,
                                     'type': agentType}

    getSiteInstallationPackageURL = requests.get(gfiAPI, params=get_site_installation_package)

    if getSiteInstallationPackageURL.headers['Content-Type'] == 'application/xml':
        # XML response is only returned on an error, so an XML response is skipped.
        print "SKIPPING XML RESPONSE - " + getSiteInstallationPackageURL.url
    else:
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
        print clientID
        sites = getSites(int(clientID), clientIDdict[clientID])
        clientInfo.append(sites)
    siteInfo = []
    # Create a list of dicts containing site info in the following format:
    # Format of dict is defined by the getSites function
    for client in clientInfo:
        for site in client:
            siteInfo.append(site)
    for site in siteInfo:
        getSiteInstallationPackage(site, agentType, password)

if __name__ == "__main__":
    opts, args = parser.parse_args()
    gfiAPI = "https://www.hound-dog.us/api/?apikey=" + opts.apikey
    getAllSiteInstallationPackages(opts.type, opts.password)
