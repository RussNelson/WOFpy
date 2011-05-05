from lxml import etree

import cbi_models as model

namespaces = {
        'xsi': "http://www.w3.org/2001/XMLSchema-instance",
        'xlink': "http://www.w3.org/1999/xlink",
        'om': "http://www.opengis.net/om/1.0",
        'gml': "http://www.opengis.net/gml",
        'swe': "http://www.opengis.net/swe/1.0.1"
    }

def nspath(path, ns):
    return '{%s}%s' % (ns, path) 

def parse_datavalues_from_get_observation(tree, site_code, var_code):
    """
    input:  lxml.etree tree from etree.parse
            site_code
            var_code
            
    output: list of DataValues
    """
    
    #The data values from the response xml are organized into 'blocks'
    # with each block containing several fields (PlatformName, time,
    # latitude, longitude, depth, observedProperty1).
    # These fields are described in swe:field elements
    
    fields = tree.findall('.//'+nspath('field', namespaces['swe']))
    field_names = [f.attrib['name'] for f in fields]
    
    #Now that we have the fields, we can parse the values appropriately
    
    text_block = tree.find('.//'+nspath('encoding', namespaces['swe'])
                    +'/'+nspath('TextBlock', namespaces['swe']))
    block_sep = text_block.attrib['blockSeparator']
    token_sep = text_block.attrib['tokenSeparator']
    
    values_blocks = tree.findtext('.//'+nspath('values', namespaces['swe']))

    datavalue_list = []
    val_lines_arr = [block.split(token_sep)
                     for block in values_blocks.split(block_sep)]
    
    for val_line in val_lines_arr:
        field_val_dict = dict(zip(field_names, val_line))
        
        dv = model.DataValue(field_val_dict['observedProperty1'], #TODO: Is it always observedProperty1 ?
                             field_val_dict['time'],
                             field_val_dict['depth'],
                             site_code,
                             var_code) #TODO: SiteID and VarID (instead of code)
        
        datavalue_list.append(dv)
        
    return datavalue_list