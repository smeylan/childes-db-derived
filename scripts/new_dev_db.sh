source ~/.profile
echo "Creating new database..."
cat new_dev_db.sql | mysql -uroot -p"$ROOT_PASS"
echo "Enforcing schema..."
cd ../
python3 augment_schema.py --data_root datasets
python3 manage.py makemigrations db
python3 manage.py migrate db
#echo "Populating....."
python3 -m pdb -c c manage.py populate_db --data_root datasets
