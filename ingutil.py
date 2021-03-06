#!/srv/gs1/software/python/3.4/bin/python3.4
import random
import argparse
import time
import json
import pycurl
import zipfile
import xlrd
from urllib.parse import urlencode
from io import BytesIO
from io import StringIO
import os
import logging

def parse_arguments():
    parser = argparse.ArgumentParser(description='Upload a VCF file to Ingenuity or check the status of an upload.') 
    subparsers = parser.add_subparsers()

    upload_parser = subparsers.add_parser('upload', help='Upload a VCF file to Ingenuity. API key, API secret, activation code, and shared users are read from a JSON file.')
    upload_parser.add_argument('vcf_file', type=str, help='input VCF file to upload, accepts .vcf or .vcf.gz')
    upload_parser.add_argument('sample_name', type=str, help='sample name (e.g. case0017)')
    upload_parser.add_argument('-c', '--config_file', type=str, help='configuration file in JSON format (default: conf-nosharing-noactivation.json)', default=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'conf-nosharing-noactivation.json'))
    upload_parser.add_argument('-d', '--display_name', type=str, help='Barcode and Display Name in Ingenuity (default: same as sample name)')
    upload_parser.add_argument('-n', '--no_description', action="store_true", help='do not try to read subject name and description from Excel file and just leave blank')
    upload_parser.add_argument('-t', '--test', action="store_true", help='create metadata files only')
    upload_parser.set_defaults(func=upload_subcommand)
        
    status_parser = subparsers.add_parser('status', help='Checks the status of an upload.')
    status_parser.add_argument('status_url', type=str, help='the status URL to check')
    status_parser.add_argument('-c', '--config_file', type=str, help='configuration file in JSON format (default: conf-nosharing-noactivation.json)', default=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'conf-nosharing-noactivation.json'))
    status_parser.set_defaults(func=status_subcommand)

    args = parser.parse_args()
    return args

def create_study_file(study_filename, Display_Name, Description, Subject_ID, Gender, Age, Ethnicity, Phenotype):
    pass

def create_assay_file(assay_filename, Subject_ID, vcf_filename):
    pass

def load_json(filename):
    fp = open(filename)
    loaded_json = json.load(fp)
    return loaded_json

def get_access_token(id, secret):
    c = pycurl.Curl()
    c.setopt(c.URL, 'https://api.ingenuity.com/v1/oauth/access_token')
    post_data={'grant_type':'client_credentials','client_id':id,'client_secret':secret}
    postfields=urlencode(post_data)
    buffer = BytesIO()
    c.setopt(c.POSTFIELDS, postfields)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    body = buffer.getvalue()
    token_json = json.loads(body.decode())
    return token_json['access_token']

def parse_excel(filename, samplename):
        """Return the patient description from a given .xlsx file for a given case number."""
        book = xlrd.open_workbook(filename)
        # Find subject ID from sample ID 
        status_sheet = book.sheet_by_name('Status')
        col0 = status_sheet.col(0)
        index = None
        for i in range(len(col0)):
            if col0[i].value == samplename:
                index = i
                break
        if index == None:
            raise Exception("Sample name {} not found in Excel file.".format(samplename))
            #return '', samplename
        col1 = status_sheet.col(1)
        subject_id = col1[index].value
        # Find description from subject ID
        patients_sheet = book.sheet_by_name('Patients')
        col0 = patients_sheet.col(0)
        index = None
        for i in range(len(col0)):
            if col0[i].value == subject_id:
                index = i
                break
        if index == None:
            raise Exception("Subject ID {} not found in Excel file.".format(subject_id))
            return '', subject_id
        col5 = patients_sheet.col(5)
        assert(col5[0].value == 'Patient details')
        description = col5[index].value
        return description, subject_id
    
def create_investigation_file(users, samplename, i_file, s_a_file):
        fp = open(i_file, 'w')
        fp.write('Study Identifier\t'+samplename+'\n')
        fp.write('Study Title\t'+samplename+'\n')
        fp.write('Study File Name\t'+os.path.basename(s_a_file)+'\n')
        fp.write('Study Assay File Name\t'+os.path.basename(s_a_file)+'\n')
        fp.write('Study Person Email')
        for user in users:
                fp.write('\t'+user['email'])
        fp.write('\n')
        fp.write('Study Person First Name')
        for user in users:
                fp.write('\t'+user['fname'])
        fp.write('\n')
        fp.write('Study Person Last Name')
        for user in users:
                fp.write('\t'+user['lname'])
        fp.write('\n')
        fp.write('Study Person Affiliation')
        for user in users:
                fp.write('\t'+user['affil'])
        fp.write('\n')
        fp.write('Study Person Roles')
        for user in users:
                fp.write('\t'+user['role'])
        fp.write('\n')
        fp.close()

def create_study_assay_file(sample_name, vcf_file, description, subject_name, code, s_a_file):
    vcf_filename = os.path.basename(vcf_file)
    fp = open(s_a_file,'w')
    fp.write('Sample Name\tDerived Data File\tSample Description\tSubject Name\tActivation Code\n')
    fp.write(sample_name+'\t'+vcf_filename+'\t'+description+'\t'+subject_name+'\t'+code+'\n')
    fp.close()

def create_request_file(samplename, r_file):
    fp = open(r_file,'w')
    fp.write('Analysis Title\t'+samplename+'\n')
    fp.write('Analysis Pipeline Name\tMedGap\n')
    fp.write('Processor Email\t\n')
    fp.write('Activation Code\t\n')
    fp.close()

def create_package(vcf_file, s_a_file, i_file, r_file, z_file):
    with zipfile.ZipFile(z_file, 'w') as package:
        package.write(s_a_file, os.path.basename(s_a_file))    
        package.write(i_file, os.path.basename(i_file))
        # Uploading request files doesn't seem to be working, but not needed
        #package.write(r_file, os.path.basename(r_file))
        package.write(vcf_file, os.path.basename(vcf_file))

def upload_package(token, z_file):
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, 'https://api.ingenuity.com/v1/datapackages/')
    c.setopt(c.POST, 1)
    c.setopt(c.HTTPHEADER, ['Content-Type: multipart/form-data'])
    c.setopt(c.HTTPHEADER, ['Authorization: Bearer '+token])
    c.setopt(c.HTTPPOST, [('file', (c.FORM_FILE, z_file))])    
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    body = buffer.getvalue()
    decoded_body = body.decode()
    try:    
        response_dict = json.loads(decoded_body)
        logger.info('Upload complete. Response from server:')
        logger.info(json.dumps(response_dict,indent='\t'))
    except ValueError:
        logger.info('Could not parse server response as a JSON object. Response follows:')
        logger.info(decoded_body)

def check_status(status_url, token):
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, status_url)
    c.setopt(c.HTTPHEADER, ['Content-Type: multipart/form-data'])
    c.setopt(c.HTTPHEADER, ['Authorization: Bearer '+token])
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    body = buffer.getvalue()
    response_dict = json.loads(body.decode())
    return response_dict

def print_file(filename, logger):
    with open(filename) as f:
        logger.info(f.read())    

def setup_loggers():
    logger = logging.getLogger('ingutil')
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(os.path.join(os.path.dirname(__file__),'ingutil.log'))
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    # add the handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger

def upload_subcommand(args, logger):
    temp = '/tmp/'
    # Random filenames for temporary files
    suffix = str(int(random.random()*100000000))
    i_file = temp+'i_'+suffix+'.txt'
    s_a_file = temp+'s_a_'+suffix+'.txt'
    r_file = temp+'r_'+suffix+'.txt'
    z_file = temp+suffix+'.zip'
    vcf_file = args.vcf_file    
    conf = load_json(args.config_file)
    shared_users = conf['shared_users']
    code = conf['activation_code']
    display_name = args.sample_name
    if args.display_name != None:
        display_name = args.display_name
    if not args.no_description and 'xlsx_file' in conf:
        xlsx_file = os.path.join(os.path.dirname(args.config_file), conf['xlsx_file'])
        description, subject_name = parse_excel(xlsx_file, args.sample_name)
    else:
        description, subject_name = '',''
    create_investigation_file(shared_users, display_name, i_file, s_a_file)
    logger.info('Created temporary file '+i_file+':')
    print_file(i_file, logger)
    create_study_assay_file(display_name, vcf_file, description, subject_name, code, s_a_file)
    logger.info('Created temporary file '+s_a_file+':')
    print_file(s_a_file, logger)
    create_request_file(display_name, r_file)
    logger.info('Created temporary file '+r_file+':')
    print_file(r_file, logger)
    if not args.test:
        logger.info('Creating package '+z_file+'...')
        create_package(args.vcf_file, s_a_file, i_file, r_file, z_file)
        logger.info('Created temporary file '+z_file)
        token = get_access_token(conf['api_key_id'], conf['api_key_secret'])
        logger.info('Uploading package...')
        response_dict = upload_package(token, z_file)
        os.remove(z_file)    
        logger.info('Removed temp file '+z_file)
    os.remove(i_file)
    logger.info('Removed temp file '+i_file)
    os.remove(s_a_file)
    logger.info('Removed temp file '+s_a_file)
    os.remove(r_file)
    logger.info('Removed temp file '+r_file)

def status_subcommand(args, logger):
    conf = load_json(args.config_file)
    token = get_access_token(conf['api_key_id'], conf['api_key_secret'])
    response_dict = check_status(args.status_url, token)
    print('Response from server:')
    print(json.dumps(response_dict,indent='\t'))

if __name__ == '__main__':
    logger = setup_loggers()
    args = parse_arguments()
    args.func(args, logger)
