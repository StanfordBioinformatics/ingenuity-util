    usage: ingutil [-h] {upload,status} ...

    Upload a VCF file to Ingenuity or check the status of an upload.

    positional arguments:
      {upload,status}
        upload         Upload a VCF file to Ingenuity. API key, API secret,
                       activation code, and shared users are read from a JSON
                       file.
        status         Checks the status of an upload.

    optional arguments:
      -h, --help       show this help message and exit



    usage: ingutil upload [-h] [-c CONFIG_FILE] [-d DISPLAY_NAME] [-t]
                          vcf_file sample_name

    positional arguments:
      vcf_file              input VCF file to upload, accepts .vcf or .vcf.gz
      sample_name           sample name (e.g. case0017)

    optional arguments:
      -h, --help            show this help message and exit
      -c CONFIG_FILE, --config_file CONFIG_FILE
                            configuration file in JSON format (default: conf-
                            nosharing-noactivation.json)
      -d DISPLAY_NAME, --display_name DISPLAY_NAME
                            Barcode and Display Name in Ingenuity (default: same
                            as sample name)
      -t, --test            create metadata files only



    usage: ingutil status [-h] [-c CONFIG_FILE] status_url

    positional arguments:
      status_url            the status URL to check

    optional arguments:
      -h, --help            show this help message and exit
      -c CONFIG_FILE, --config_file CONFIG_FILE
                            configuration file in JSON format (default: conf-
                            nosharing-noactivation.json)

