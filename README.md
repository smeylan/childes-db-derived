# Childes-db-derived

This Django-backed framework makes ML and NLP-backed datasets available through the childes-db system.

- We use Django to enforce the database schema, build an object-relational model and then populate the database
- The workflows below involve pushing data to the `childes_db_derived_dev` database, then copying that to named releases that will otherwise remain unchanged. `childes_db_derived_dev` may change at any time and only release versions of the dataset should be expected t be stable

# Format of Derived Datasets

This codebase uses table-defined specifications for 

`derived_datasets.csv`: metadata for the dataset. A unique table name used to store the data will be automatically generated from the `entity_type`, `dataset_name`, `childes_db_version`, and `dataset_version`. These will be joined by hyphens, and the period in the childes_db_version will be replaced with an underscore.
`variables.csv`: names of the variables and their specifications in the ORM (in `data_type`). This gets used to auto-populate the schema and to check if there are previous datasets with the same format  
`data.csv`: the actual data from the annotation / tagging system or the gold-standard dataset. Variable contents must be described in `variables.csv`.

Look at example csv's in `datatasets/`. More details can also be found here: https://docs.google.com/spreadsheets/d/1ohNKEQ3EgK1lq7vQG5QWaYwR1EJad10h-3b1MD8MlsY/edit#gid=0

# Sharing variables across datasets

The database is designed to allow datasets to share coding schemes to make it more clear which annotation systems have the same annotation scheme. The database population code checks if the variables used by a datasets (in variables.csv) are the same as those used by a previous dataset; if they are, then it links against those in the relational database. Because the properties of each variable are tracked separately in `variables.csv`, it is posible for a dataset to have a combination of back-compatible and novel tag formats.

# Replicability of External Models / Codebases

As of April 2024, we don't handle re-running the external models / tools used to derive these datasets, and leave that up to external researchers. However, in the future we would like to handle this in some way so that we can re-run contributed models each time we create a new version of childes-db. For now, we ask that researchers use Python 3.9 and note all of their dependencies following the conventions of `pip` or `conda`.

# Update the Dev Database

If you have not already set up the server, follow the instructions in the following section.

When you want to update the database, you don't need to install anything new (i.e. MySQL or python libraries) -- all you need to do is get to a shell on the appropriate machine, load the appropriate virtual environment so that the system can see the right python libraries, make sure the datasets you mean to add are in the correct place/format, and then invoke the database populating script. In more detail:

1. `cd childes-db-derived` to enter the peekbank folder

1. Activate the virtual environment: `source childes-db-derived-py3.9-env/bin/activate`

1. [if we move derived datasets to OSF] Download the most recent version of all of the files from OSF with the Django command: `python3 manage.py download_osf --data_root ../childes_db_derived_data_osf`

1. `cd scripts` and run `./new_dev_db.sh.` This drops the existing database called `childes_db_derived_dev` (if it exists), and creates a fresh one. Then it iterates through datasets and uses the specification in `variables.csv` for each dataset to augment the schema using the `augment_schema.py` script. Then it uses the augmented dataset to create new migrations, runs them and then iterates through the datasets to add records corresponding to each dataset and populates the `variable_mappings` field.

Unless this errors out, you should be able to see the new data in the `childes_db_drived_dev` database when this process finishes.

# Setting Up a New Server From Scratch

Follow these directions if you are setting up a new server (e.g., a new EC2 box) from scratch. Otherwise, jump down to "Update the Dev Database" for instructions on how to get into an existing installation and update the database with a newer version of the data. We provide the instructions here for setting up a new server because one might want to add this to an existing server (e.g., an image with Shiny on it) because the MySQL requirements are quite simple by comparison.

1. First, SSH onto the server. 
1. Make sure that you have mysql server installed. For a debian based OS, this is most likely as simple as running `sudo apt install mysql-server`. 
However, you will also need to figure out user accounts in the database with appropriate privileges. The `config.json` should give you 
some hints. Modify according to your environment.

1. Clone this repo into the user folder

1. Get the `config.json` file with database credentials and place them in the root of this repo. This includes Django settings and passwords and is not part of the repo because it has passwords etc.

1. Set up a virtual environment; by convention `peekbank-env`: `virtualenv childes-db-derived-py3.9-env -p python3.9`

1. Then activate the venv: `source childes-db-derived-py3.9-env/bin/activate`

1. And you should see the venv name in your shell (childes-db-derived-py3.9-env). Then install the requirements to the venv: `pip3 install -r requirements.txt`

At this step, if you get an error related to missing `mysql_config` file, make sure that you install the package `libmysqlclient-dev` with `sudo apt install libmysqlclient-dev` (or something similar depending on your OS)

This server should be ready to run MySQL, so try updating the dev database as above!
