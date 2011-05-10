
import urllib2
import os
import time
import datetime

from optparse import OptionParser
from lxml import etree
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker

import daos.cbi.cbi_cache_models as model

cbi_cache_connection_string = 'sqlite:///' + os.path.join(
    os.path.dirname(__file__), 'daos', 'cbi', 'cbi_cache.db')


IOOS_SITE_FILE_URL = 'http://lighthouse.tamucc.edu/ioosobsreg.xml'

CBI_SOS_CAPABILITIES_URL = 'http://lighthouse.tamucc.edu/sos'

GCOOS_ONTOLOGY_FILE_URL = \
    'http://mmisw.org/ont?form=rdf&uri=http://mmisw.org/ont/gcoos/parameter'

local_site_file_path = os.path.join(
    os.path.dirname(__file__), 'daos', 'cbi', 'local_cache_files',
    'cbi_site_file.xml'
)

local_parameter_file_path = os.path.join(
    os.path.dirname(__file__), 'daos', 'cbi', 'local_cache_files',
    'cbi_parameter_file.xml'
)

local_capabilities_file_path = os.path.join(
    os.path.dirname(__file__), 'daos', 'cbi', 'local_cache_files',
    'cbi_sos_capabilities_file.xml'
)

namespaces = {
    'gml': "http://www.opengis.net/gml",
    'xlink': "http://www.w3.org/1999/xlink",
    'xsi': "http://www.w3.org/2001/XMLSchema-instance",
    'ioos': "http://www.csc.noaa.gov/ioos",
    'omvmmi':"http://mmisw.org/ont/mmi/20081020/ontologyMetadata/",
    'rdfs':"http://www.w3.org/2000/01/rdf-schema#",
    'owl':"http://www.w3.org/2002/07/owl#",
    'omv':"http://omv.ontoware.org/2005/05/ontology#",
    'dc':"http://purl.org/dc/elements/1.1/",
    'oost':"http://www.oostethys.org/schemas/0.1.0/oostethys",
    'ows':"http://www.opengis.net/ows/1.1",
    'swe':"http://www.opengis.net/swe/1.0",
    'sos':"http://www.opengis.net/sos/1.0",
    'par_base':"http://mmisw.org/ont/gcoos/parameter/"
}

class Site(object):
    def __init__(self, code, name, latitude, longitude):
        self.code = code
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        
    def __key(self):
        return (self.code, self.name, self.latitude, self.longitude)
        
    def __eq__(self, other):
        return self.__key() == other.__key()

    def __hash__(self):
        return hash(self.__key())


class Unit(object):
    def __init__(self, name, abbreviation):
        self.name = name
        self.abbreviation = abbreviation
    
    def __key(self):
        return (self.name, self.abbreviation)
        
    def __eq__(self, other):
        return self.__key() == other.__key()
        
    def __hash__(self):
        return hash(self.__key())

class Parameter(object):
    def __init__(self, code, name, unit):
        self.code = code
        self.name = name
        self.unit = unit
    
    def __key(self):
        return (self.code, self.name)
        
    def __eq__(self, other):
        return self.__key() == other.__key()
        
    def __hash__(self):
        return hash(self.__key())
    
class Series(object):
    def __init__(self, site_code, var_code, start_time, end_time,
                 time_interval, time_interval_unit, is_current):
        self.site_code = site_code
        self.var_code = var_code
        self.start_time = start_time
        self.end_time = end_time
        self.time_interval = time_interval
        self.time_interval_unit = time_interval_unit
        self.is_current = is_current
    
    def __key(self):
        return (self.site_code, self.var_code, self.start_time, self.end_time,
                self.time_interval, self.time_interval_unit, self.is_current)
        
    def __eq__(self, other):
        return self.__key() == other.__key()
        
    def __hash__(self):
        return hash(self.__key())
    
def nspath(path, ns):
    return '{%s}%s' % (ns, path)

def fetch_ioos_site_file(site_file_url, local_site_file_path):
    response = urllib2.urlopen(site_file_url)
    
    cbi_site_file = open(local_site_file_path, 'w')
    
    cbi_site_file.write(response.read())
    
    cbi_site_file.close()


def parse_site_file(local_site_file_path):
    '''
    Reads an IOOS XML site file and returns a set of sites.
    '''

    site_set = set()
    
    site_file = open(local_site_file_path)
    
    tree = etree.parse(site_file)
    
    site_file.close()
    
    feature_member_list = tree.findall('.//'+nspath('featureMember',
                                                   namespaces['gml']))
    
    for feature in feature_member_list:
        point_obs = feature.find(nspath('InsituPointObs', namespaces['ioos']))
        
        gml_id = point_obs.attrib[nspath('id', namespaces['gml'])]
        param_code = gml_id.split('.')[2]
        
        observation_name = point_obs.find(nspath('observationName',
                                                 namespaces['ioos']))
        
        #Parse Site info
        status = point_obs.find(nspath('status', namespaces['ioos']))
        platform_name = point_obs.find(nspath('platformName',
                                              namespaces['ioos']))
       
        horiz_position = point_obs.find(nspath('horizontalPosition',
                                               namespaces['ioos']))
        pos = horiz_position.find(nspath('Point', namespaces['gml'])+'/'+
                                  nspath('pos', namespaces['gml']))
        latitude = pos.text.split()[0]
        longitude = pos.text.split()[1]
         
        vert_position = point_obs.find(nspath('verticalPosition',
                                              namespaces['ioos']))
        vert_pos_units = vert_position.attrib['uom']
        
        vert_datum = point_obs.find(nspath('verticalDatum',
                                           namespaces['ioos']))
        
        operator = point_obs.find(nspath('operator', namespaces['ioos']))
        start_date = point_obs.find(nspath('startDate', namespaces['ioos']))
        end_date = point_obs.find(nspath('endDate', namespaces['ioos']))
        operator_uri = point_obs.find(nspath('operatorURI',
                                             namespaces['ioos']))
        platform_uri = point_obs.find(nspath('platformURI',
                                             namespaces['ioos']))
        data_uri = point_obs.find(nspath('dataURI', namespaces['ioos']))
        comments = point_obs.find(nspath('comments', namespaces['ioos']))
        
        
        site_code = platform_name.text.split(':')[0]
        site_name = platform_name.text.split(':')[1]
        
        #Create a Site object and add it to the return set
        site = Site(site_code, site_name, latitude, longitude)
        site_set.add(site)
   
    return site_set


def fetch_cbi_capabilities_file(cbi_capabilities_file_url,
                                local_capabilities_file_path):
    
    response = urllib2.urlopen(cbi_capabilities_file_url)
    
    local_capabilities_file = open(local_capabilities_file_path,'w')
    
    local_capabilities_file.write(response.read())
    
    local_capabilities_file.close()
    

def extract_parameters(local_capabilities_file_path):
    capabilities_file = open(local_capabilities_file_path)
    
    tree = etree.parse(capabilities_file)
    
    capabilities_file.close()
    
    #.//ows:Parameter[@name='observedProperty']/ows:AllowedValues/ows:Value
    
    param_name_elements = tree.findall(
        './/'+nspath("Parameter[@name='observedProperty']", namespaces['ows'])
        +'/'+nspath("AllowedValues", namespaces['ows'])
        +'/'+nspath("Value", namespaces['ows'])
    )
    
    return [p.text for p in param_name_elements]


def parse_capabilities_for_series(local_capabilities_file_path):
    capabilities_file = open(local_capabilities_file_path)
    
    tree = etree.parse(capabilities_file)
    
    capabilities_file.close()
    
    obs_offerings = tree.findall('.//'+nspath(
        'ObservationOffering', namespaces['sos']))
    
    series_set = set()
    
    for offering in obs_offerings:
        site_code = offering.findtext(nspath('name', namespaces['gml']))
        
        time_period = offering.find(
            nspath('eventTime', namespaces['sos'])
            +'/'+nspath('TimePeriod', namespaces['gml']))
            
        start_time = time_period.findtext(
            nspath('beginPosition', namespaces['gml']))    

        end_time = time_period.findtext(
            nspath('endPosition', namespaces['gml']))
        
        time_interval_node = time_period.find(
            nspath('timeInterval', namespaces['gml']))
        
        time_interval_unit = time_interval_node.attrib['unit']
        time_interval = time_interval_node.text

        properties = offering.findall(
            nspath('observedProperty', namespaces['sos']))
        
        is_current = not end_time
        
        for prop in properties:
            #TODO: It would be best if the observedProperty elements had
            # the variable names/codes as their inner text, but they don't currently
            prop_link = prop.attrib[(nspath('href', namespaces['xlink']))]
            split_prop_link = prop_link.split('/')
            var_code = split_prop_link[len(split_prop_link)-1]
            
            series = Series(site_code, var_code, start_time, end_time,
                            time_interval, time_interval_unit, is_current)
            
            series_set.add(series)
       
    return series_set

def fetch_gcoos_parameter_file(parameter_file_url, local_parameter_file_path):
    response = urllib2.urlopen(parameter_file_url)
    
    cbi_parameter_file = open(local_parameter_file_path, 'w')
    
    cbi_parameter_file.write(response.read())
    
    cbi_parameter_file.close()


def parse_parameter_file(param_names, local_parameter_file_path):
    """
    Reads a GCOOS XML site file and returns a set of parameters and a set
    of units.
    The list of parameters returned is constrained to those in the input
    param_names list.
    """
    
    param_set = set()
    units_set = set()
    
    param_file = open(local_parameter_file_path)
    
    tree = etree.parse(param_file)
    
    param_file.close()
    
    all_params = tree.findall('.//'+ nspath('Parameters',
                                            namespaces['par_base']))
    
    for p in all_params:
        name = p.findtext(nspath('name', namespaces['par_base']))
        
        
        if name in param_names: #then found one we want
            description = p.findtext(nspath('description',
                                            namespaces['par_base']))
            
            #units are in the description, prefaced by "Unit: " and
            # ending with a semicolon (eg Unit: celsius;)
            start_index = description.find('Unit: ')
            end_index = description.find(';', start_index)
            unit_abbr = description[start_index+6:end_index]
            unit = Unit(unit_abbr, unit_abbr) #TODO: Where to get unit names?
            
            #TODO: Some of these units are not really that good,
            # like "Pa | bar |dbar |atm" for pressure, "ug L-1 (not kg m-3)",
            # "precent"
            # Maybe we need a units dictionary or something since the GCOOS
            # registry is not very good
            
            units_set.add(unit)
            
            param = Parameter(name, name, unit)
            param_set.add(param)
            
    return (param_set, units_set)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-d","--dropall", dest="dropall", default=False,
                  help="Drop all from site cache database before rebuilding.")
    
    (options, args) = parser.parse_args()

    #Attempt to open local site file to see if it exists
    try:
        f = open(local_site_file_path)
        f.close()
    except: #If it doesn't exist, then fetch a new one from the remote location
        print "Fetching IOOS site file from remote location."
        fetch_ioos_site_file(IOOS_SITE_FILE_URL, local_site_file_path)
    
    #Attempt to open local capbilities file to see if it exists
    try:
        f = open(local_capabilities_file_path)
        f.close()
    except:
        print "Fetching CBI SOS Capabilities file from remote location."
        fetch_cbi_capabilities_file(CBI_SOS_CAPABILITIES_URL,
                                    local_capabilities_file_path)
    
    #Attempt to open local parameter file to see if it exists
    try:
        f = open(local_parameter_file_path)
        f.close()
    except: #If it doesn't exist, then fetch a new one from the remote location
        print "Fetching GCOOS parameter file from remote location."
        fetch_gcoos_parameter_file(GCOOS_ONTOLOGY_FILE_URL,
                                   local_parameter_file_path)
    
    
    engine = create_engine(cbi_cache_connection_string,
                           convert_unicode=True)
    if options.dropall:
        print "Dropping existing tables from cache."
        model.clear_model(engine)
    
    model.create_model(engine)
    
    db_session = scoped_session(sessionmaker(
            autocommit=False, autoflush=False, bind=engine))
    
    model.init_model(db_session)

    print "Parsing IOOS site file."
    site_set = parse_site_file(local_site_file_path)
    
        
    cache_sites = [model.Site(s.code, s.name, s.latitude, s.longitude)
                   for s in site_set]
        
    
    
    print "Extracting valid parameters from SOS capabilities file."
    param_names = extract_parameters(local_capabilities_file_path)
    
    
    print "Parsing GCOOS parameter file."
     
    (param_set, units_set) = parse_parameter_file(
        param_names, local_parameter_file_path)
    
    cache_units = [model.Units(u.name, u.abbreviation) for u in units_set]
    
    cache_variables = []
    
    for p in param_set:
        v = model.Variable(p.code, p.name)
        
        #Find the matching unit in the cache_units list
        for cu in cache_units:
            if p.unit.name == cu.UnitsName:
                v.VariableUnits = cu
        
        cache_variables.append(v)
    
    
    print "Parsing SOS Capabilities file for Series Catalog."
    
    series_set = parse_capabilities_for_series(local_capabilities_file_path)
    
    print "Adding %s sites and %s variables to local cache." % (
        len(cache_sites), len(cache_variables))
    
    try:
        db_session.add_all(cache_sites)
        db_session.add_all(cache_units)
        db_session.add_all(cache_variables)
        db_session.commit()
    
        #Now try to add series
        
        print "Adding %s series to local cache." % len(series_set)
        
        cache_series_cats = []
        
        for series in series_set:
            
            #TODO: Not all sites in the SOS Capabilities document are in the
            # IOOS Reg file.  Why?
            
            #Find the site in the cache
            site = model.Site.query.filter(
                model.Site.SiteCode==series.site_code).first()
            
            #Find the variable in the cache
            variable = model.Variable.query.filter(
                model.Variable.VariableCode==series.var_code).first()
        
            if site and variable: #Need to check because of situation mentioned above
                
                series_cat = model.SeriesCatalog()
                
                series_cat.Site = site
                series_cat.SiteID = site.SiteID
                series_cat.SiteCode = site.SiteCode
                series_cat.SiteName = site.SiteName
                
                series_cat.Variable = variable
                series_cat.VariableID = variable.VariableID
                series_cat.VariableCode = variable.VariableCode
                series_cat.VariableName = variable.VariableName
                series_cat.VariableUnitsID = variable.VariableUnits.UnitsID
                series_cat.VariableUnitsName = variable.VariableUnits.UnitsName
                series_cat.SampleMedium = variable.SampleMedium
                series_cat.GeneralCategory = variable.GeneralCategory
                

                time_units = model.Units.query.filter(
                    model.Units.UnitsName==series.time_interval_unit).first()
                
                if not time_units:
                    time_units = model.Units(series.time_interval_unit,
                                             series.time_interval_unit)
                    time_units.UnitsType = "Time"
                    
                    db_session.add(time_units)
                    db_session.commit()
                    
                variable.TimeUnits = time_units
                variable.TimeUnitsID = time_units.UnitsID
                
                #TODO: WaterML1 only supports integers for time interval
                # but the CBI service offerings have 0.5 hour intervals
                #variable.TimeSupport = series.time_interval
                #series_cat.TimeSupport = series.time_interval
                series_cat.TimeUnitsID = time_units.UnitsID
                series_cat.TimeUnitsName = time_units.UnitsName
                
                #TODO: DataType
                
                #TODO: is this the best way to do the datetime conversion?
                st = time.strptime(
                    series.start_time,"%Y-%m-%dT%H:%M:%SZ")
                
                series_cat.BeginDateTimeUTC = \
                    datetime.datetime(st[0], st[1], st[2], st[3], st[4], st[5])
                
                if series.end_time:
                    et = time.strptime(
                        series.end_time,"%Y-%m-%dT%H:%M:%SZ")
                    series_cat.EndDateTimeUTC = datetime.datetime(
                        et[0], et[1], et[2], et[3], et[4], et[5])
                
                series_cat.IsCurrent = series.is_current
                
                cache_series_cats.append(series_cat)
        
        db_session.add_all(cache_series_cats)
        db_session.commit()
        
        print "Finished."
    
    except Exception as inst:
        print "ERROR: %s, %s" % (type(inst), inst)
    
    
    