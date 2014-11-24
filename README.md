    usage: ingenuity_upload.py [-h] [-c CONFIG_FILE] [-n SAMPLE_NAME]
                               [-i VCF_FILE]
    
    Upload a VCF file to Ingenuity. Assumes API key, API secret, activation code,
    and emails to share with are stored in conf.json.
    
    optional arguments:
      -h, --help      show this help message and exit
      -c CONFIG_FILE  configuration file in JSON format
      -n SAMPLE_NAME  sample name
      -i VCF_FILE     input VCF file to upload, accepts .vcf or .vcf.gz
    
    
    
    usage: ingenuity_status.py [-h] [-u STATUS_URL] [-c CONFIG_FILE]
    
    Checks the status of an Ingenuity upload. Assumes API key and API secret are
    stored in conf.json.
    
    optional arguments:
      -h, --help      show this help message and exit
      -u STATUS_URL   status url
      -c CONFIG_FILE  configuration file in JSON format
