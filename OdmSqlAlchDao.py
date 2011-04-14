from sqlalchemy.sql import and_

import sqlalch_odm_mappings as map


class OdmSqlAlchDao(object):

    def __init__(self):
        #TODO: anything?
        pass
    
    def get_all_sites(self):
        return map.Site.query.all()
    
    def get_site_by_code(self, site_code):
        return map.Site.query.filter(map.Site.SiteCode == site_code).first()
    
    def get_sites_by_codes(self, site_codes_arr):
        return map.Site.query.filter(map.Site.SiteCode.in_(site_codes_arr)).all()
    
    def get_all_variables(self):
        return map.Variable.query.all()
    
    def get_variable_by_code(self, var_code):
        return map.Variable.query.filter(map.Variable.VariableCode == var_code).first()
    
    def get_variables_by_codes(self, var_codes_arr):
        return map.Variable.query.filter(map.Variable.VariableCode.in_(
            var_codes_arr)).all()
    
    def get_series_by_sitecode(self, site_code):
        return map.SeriesCatalog.query.filter(
            map.SeriesCatalog.SiteCode == site_code).all()
    
    def get_series_by_sitecode_and_varcode(self, site_code, var_code):
        return map.SeriesCatalog.query.filter(and_(
            map.SeriesCatalog.SiteCode == site_code,
            map.SeriesCatalog.VariableCode == var_code)).all()
        
    def get_datavalues(self, site_code, var_code, begin_date_time=None,
                       end_date_time=None):
        
        #first find the site and variable
        siteResult = self.get_site_by_code(site_code)
        varResult = self.get_variable_by_code(var_code)
        
        valueResultArr = None
        
        if (begin_date_time == None or end_date_time == None):
            valueResultArr = map.DataValue.query.filter(
                and_(map.DataValue.SiteID == siteResult.SiteID,
                     map.DataValue.VariableID == varResult.VariableID)
                ).order_by(map.DataValue.LocalDateTime).all()
        else:
            valueResultArr = map.DataValue.query.filter(
                and_(map.DataValue.SiteID == siteResult.SiteID,
                     map.DataValue.VariableID == varResult.VariableID,
                     map.DataValue.LocalDateTime >= begin_date_time,
                     map.DataValue.LocalDateTime <= end_date_time)
                ).order_by(map.DataValue.LocalDateTime).all()
            
        return valueResultArr
    
    def get_method_by_id(self, methodID):
        return map.Method.query.filter(map.Method.MethodID == methodID).first()
        
    def get_methods_by_ids(self, method_id_arr):
        return map.Method.query.filter(
            map.Method.MethodID.in_(method_id_arr)).all()
        
    def get_source_by_id(self, source_id):
        return map.Source.query.filter(map.Source.SourceID == source_id).first()
        
    def get_sources_by_ids(self, source_id_arr):
        return map.Source.query.filter(
            map.Source.SourceID.in_(source_id_arr)).all()
    
    def get_qualifier_by_id(self, qualifier_id):
        return map.Qualifier.query.filter(
            map.Qualifier.QualifierID == qualifier_id).first()
    
    def get_qualifiers_by_ids(self, qualifier_id_arr):
        return map.Qualifier.query.filter(map.Qualifier.QualifierID.in_(
            qualifier_id_arr)).all()
    
    def get_qualcontrollvl_by_id(self, qual_control_lvl_id):
        return map.QualityControlLevel.query.filter(
                map.QualityControlLevel.QualityControlLevelID ==
                qual_control_lvl_id).first()
    
    def get_qualcontrollvls_by_ids(self, qual_control_lvl_id_arr):
        return map.QualityControlLevel.query.filter(
               map.QualityControlLevel.QualityControlLevelID.in_(
                    qual_control_lvl_id_arr)).all()
    
    def get_offsettype_by_id(self, offset_type_id):
        return map.OffsetType.query.filter(
            map.OffsetType.OffsetTypeID == offset_type_id).first()
    
    def get_offsettypes_by_ids(self, offset_type_id_arr):
        return map.OffsetType.query.filter(map.OffsetType.OffsetTypeID.in_(
            offset_type_id_arr)).all()
        