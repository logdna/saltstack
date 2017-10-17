## Salt

The LogDNA Salt deployment integration listens for your salt state events and sends the relevant event information to LogDNA.

### Setup instructions

1. Install the LogDNA salt engine on your salt master with:
```
sudo mkdir -p /var/cache/salt/master/extmods/engines/
sudo wget -O /var/cache/salt/master/extmods/engines/logdna.py https://raw.githubusercontent.com/logdna/saltstack/master/logdna.py
```
2. Add the custom extension modules directory to your salt master configuration:
```
module_dirs:
     - /var/cache/salt/master/extmods
```
3. Specify your LogDNA Ingestion Key inside the engines section of your salt master configuration:
```
engines:
     - logdna:
         ingestion_key: YOUR-INGESTION-KEY-HERE
```
4. Restart salt-master with:
```
sudo service salt-master restart
```

### Viewing salt states

If you select the Salt app inside the All Apps [filter menu](doc:filters), you can see the states applied across all your hosts. Filtering by a specific source, will only show salt states applied to that particular host. As an aside, we do our best to format your salt states to look as pretty as possible.
