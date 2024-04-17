import glob
import os
import json
import django
from django.db.models import Avg, Count, Sum
from django.db import reset_queries
import pandas as pd
import numpy as np
import db.models
import traceback
from django.conf import settings
from collections import defaultdict
from datetime import datetime
import copy
import json

def checkForPath(path):
    if os.path.exists(path):
        print(path+ ' found!')
        return(path)
    else:
        return(None)

def getDictsWithKeyForValue(dict_list, key, value):
    rv = []
    for item in dict_list:
        if item[key] == value:
            rv.append(item)
    return rv

def CSV_to_Django(validate_only, bulk_args, data_folder, schema, dataset_type, offsets, dependencies=None, optional=False, csv_name=None, add_offsets=True):

    if csv_name is None:
        csv_name = dataset_type    

    class_names = dict([(x['table'],x['model_class']) for x in schema])
    table_names = dict([(x['model_class'],x['table']) for x in schema])

    csv_path = checkForPath(os.path.join(data_folder, csv_name+'.csv'))
    if csv_path is None:
        if optional:
            print(os.path.join(data_folder, csv_name+'.csv')+ ' is missing; allowing for now...')
            pass
        else:
            print(os.path.join(data_folder, csv_name+'.csv')+ ' is missing; aborting.')
            raise ValueError(os.path.join(data_folder, csv_name+'.csv')+ ' is missing; aborting.') #FIXME -- need a way to abort further processing for this dataset from inside the function
    else:
        print('Processing '+csv_path+'...')
        df = pd.read_csv(csv_path)        
        df = df.replace({np.nan:None})

        # need to make sure any JSON are cast as such here right here        

        class_def = getDictsWithKeyForValue(schema, "model_class", class_names[dataset_type])[0]
        primary_key = [x for x in class_def['fields'] if 'primary_key' in x['options']][0]['field_name']

        fields_in_csv = df.columns
        fields_required_by_schema = [x['field_name'] for x in class_def['fields']]

        if dataset_type == 'derived_datasets':
            # the table name value is not in the csv but is constructed from the components 
            fields_required_by_schema = [x for x in fields_required_by_schema if x != 'table_name']
    
        missing_fields = set(fields_required_by_schema)  - set(fields_in_csv) 
        
        if len(missing_fields) > 0:
            raise ValueError('Fields are missing from '+csv_path+': '+'; '.join(missing_fields)) 
        
        extra_fields = set(fields_in_csv) - set(fields_required_by_schema)
        if len(extra_fields) > 0:
            raise ValueError('Extra fields found in '+csv_path+': '+'; '.join(extra_fields)) 
        rdict = {}            

        for record in df.to_dict('records'):
            record_default = defaultdict(None,record)

            
            payload = {}

            for field in class_def['fields']:                

                if field['field_class'] == 'ForeignKey':
                    #print('Populating '+dataset_type+'.'+field['field_name']+' as foreign key...')
                    # write the foreign key contents programatically
                    # import pdb
                    # pdb.set_trace()
                    data_model_for_fk = getattr(db.models, field['field_class'])

                    to_pk =  field['options']['to']
                    fk_to_table = table_names[field['options']['to']]
                    fk_field = field['field_name']

                    if dependencies[fk_to_table] is None:
                        # special case when a fk_to table does not exist, e.g. aoi_region_sets
                        payload[fk_field] = None
                    else:
                        if fk_field in ('distractor_id', 'target_id'):
                            # special case where the pk of the destination/to table is different than the local key (trials -> stimulis)
                            fk_remap = "stimulus_id"
                        else:
                            fk_remap = fk_field

                        payload[fk_field] = dependencies[fk_to_table][record_default[fk_field] + offsets[fk_remap]]
                        

                else:                    

                    # cast any aux fields to JSON
                    if 'aux' in field['field_name'] and record_default[field['field_name']] is not None:
                        
                        payload[field['field_name']] = json.loads(record_default[field['field_name']])
                        
                        if dataset_type in ('administrations', 'subjects'):                            
                            validate_aux_data( payload[field['field_name']])                        

                    # in most cases, just propagte the field
                    elif field['field_name'] in record_default:
                        #print('Populating '+dataset_type+'.'+field['field_name']+' normally...')
                        payload[field['field_name']] = record_default[field['field_name']]                    
                    
                    else:                    
                        if dataset_type == 'derived_datasets' and field['field_name'] == 'table_name':
                            pass # special case that the table name is created afterwards
                        else:
                            # if it's in one of the aux's, populate the field with None
                            raise ValueError('No value found for field '+field['field_name']+". Make sure that this field is populated. Aborting processing this dataset.")

            if dataset_type == 'derived_datasets':
                payload['table_name'] = payload['entity_type'] + '-' + payload['dataset_name'] + '-' + str(payload['childes_db_version']).replace('.','_') + '-' + str(payload['dataset_version'])

            # Add the offset to the primary key
            if add_offsets:
                if primary_key != 'table_name':
                    payload[primary_key] += offsets[primary_key]

            data_model = getattr(db.models, class_names[dataset_type])
            rdict[payload[primary_key]] = data_model(**payload)

            

        if not validate_only:
            bulk_args.append((class_names[dataset_type], rdict))
        return(rdict)

def bulk_create_tables(bulk_args):
    for arg in bulk_args:
        getattr(db.models, arg[0]).objects.bulk_create(arg[1].values(), batch_size = 1000)



def create_data_tables(all_dirs, schema, validate_only):

    completion_reports = []

    for data_folder in all_dirs:
        
        completion_report = {} 
        
        completion_report = {'dataset_name': data_folder}            
                
        # pre-compute the offsets for all tables so that the indexing can be consistent
        # offsets: pk for each table -> offset value, dataset_id -> 59
        

        table_names = dict([(x['model_class'],x['table']) for x in schema])
        offsets = {}
        for class_name in table_names.keys():
            class_def = getDictsWithKeyForValue(schema, "model_class", class_name)[0]

            pks = [x for x in class_def['fields'] if 'primary_key' in x['options']]
            if len(pks) == 0:
                raise ValueError('No primary key found for '+class_name)

            primary_key = pks[0]['field_name']
            offset_value = getattr(db.models, class_name).objects.count()
            offsets[primary_key] = offset_value

        bulk_args = []
            
        #try:            
        metadata = CSV_to_Django(validate_only, bulk_args, data_folder, schema, 'derived_datasets', offsets, optional=False)
        completion_report['derived_datasets'] = 'passed'
        if metadata is not None:
            completion_report['num_records_derived_datasets'] = len(metadata)
        else: 
            completion_report['num_records_derived_datasets'] = 0

        #except Exception as e:
        #    completion_report['derived_datasets'] = traceback.format_exc()
        #    completion_report['num_records_derived_datasets'] = 'Cannot evaluate'
        
        # pull out the record programatically                
        table_name = [x for x in metadata.keys()][0]
        data = CSV_to_Django(validate_only, bulk_args, data_folder, schema, table_name, offsets, optional=False, csv_name="data")
        
        
        # populate the variable first
            # should have a variable_name in it as well 
        variables = CSV_to_Django(validate_only, bulk_args, data_folder, schema, 'variables', offsets, optional=False, add_offsets=False)

        rdict = {}
        mapping_id = 0
        for variable in variables:
            # each variable is a separate record
            if '_id' not in variables[variable].variable_name:         
                # check if variable name contains id; if not add it here
                payload = {'mapping_id': mapping_id + offsets['mapping_id'], 'table_name':metadata[table_name], 'variable_name':variables[variable]}                                
                data_model = getattr(db.models, 'VariableMapping')
                rdict[payload['mapping_id']] = data_model(**payload)                
                
        bulk_args.append(('VariableMapping', rdict))

        if not validate_only:
            bulk_create_tables(bulk_args)
            reset_queries()
        else:
            print('Ran in validation mode, nothing written to the database.')

        completion_reports.append(completion_report)

    print('Generating a completion report...')
    completion_df = pd.DataFrame(completion_reports)
    if not os.path.exists('completion_reports'):
        os.makedirs('completion_reports')
    now = datetime.now()
    current_date_time = now.strftime("%Y-%m-%d-_%H_%M_%S")
    completion_df.to_csv(os.path.join('completion_reports','completion_report_'+current_date_time+'.csv'))


def process_childes_db_derived_dirs(data_root, validate_only):
    
    augmented_schema = json.load(open(settings.AUGMENTED_SCHEMA_FILE))
    
    if not os.path.exists(data_root):
        raise ValueError('Path '+data_root+' does not exist. Make sure you are pointing to the correct directory.')

    all_dirs = [x[0] for x in os.walk(data_root)]
    all_dirs = all_dirs[1:len(all_dirs)] # drop the root
        
    if len(all_dirs) == 0:
        import pdb
        pdb.set_trace()
        raise ValueError('No folders with processed data found. Do you have the right path?')    

    
    create_data_tables(all_dirs, augmented_schema, validate_only)
    print('Completed processing!')

