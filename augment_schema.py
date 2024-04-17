import os
import argparse
import json
import copy
import pandas as pd

#This isn't a true management command because that would require initializing the data model through models.py, which can't be done until the schema is updated.

def augment_schema(original_schema, all_dirs):
    print('build up the schema by iterating over the datasets')
    augmented_schema = copy.copy(original_schema)
    for data_dir in all_dirs:
        data_dir = all_dirs[0]

        metadata_df = pd.read_csv(os.path.join(data_dir, 'derived_datasets.csv'))
        variables_df = pd.read_csv(os.path.join(data_dir, 'variables.csv'))

        fields = [json.loads(x) for x in variables_df['data_type'].tolist()]
        for i in range(len(fields)):
            fields[i]['field_name'] = variables_df['variable_name'].tolist()[i]

        metadata_df['table_name'] = metadata_df['entity_type'].map(str) + '-' + metadata_df['dataset_name'].map(str) + '-' + metadata_df['childes_db_version'].astype(str).str.replace('.', '_', regex=False) + '-' + metadata_df['dataset_version'].map(str)

        new_dataset_schema = {
            "model_class": metadata_df.iloc[0].table_name+'_record',
            "table": metadata_df.iloc[0].table_name,
            "fields": fields
        }

        augmented_schema.append(copy.copy(new_dataset_schema))
    
    return(augmented_schema)    


parser = argparse.ArgumentParser(description='Add all information to the schema from the `variables` and `derived_datasets` table from each derived dataset in data_root')
parser.add_argument('--data_root', help='path to the derived dataset')
args = parser.parse_args()

SCHEMA_FILE = "static/childes_db_derived-schema.json"
AUGMENTED_SCHEMA_FILE = "static/childes_db_derived-schema-augmented.json"


print('Called augment schema with data_root '+args.data_root)
        
data_root = args.data_root
if not os.path.exists(data_root):
    raise ValueError('Path '+data_root+' does not exist. Make sure you are pointing to the correct directory.')

all_dirs = [x[0] for x in os.walk(data_root)]
all_dirs = all_dirs[1:len(all_dirs)] # drop the root

if len(all_dirs) == 0:
    import pdb
    pdb.set_trace()
    raise ValueError('No folders with processed data found. Do you have the right path?')    

original_schema = json.load(open(SCHEMA_FILE))        
augmented_schema  = augment_schema(original_schema, all_dirs)


with open(AUGMENTED_SCHEMA_FILE, 'w') as json_file:
    json.dump(augmented_schema, json_file, indent=4)

print('Wrote out augmented schema to '+AUGMENTED_SCHEMA_FILE)


