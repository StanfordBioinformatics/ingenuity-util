#!/srv/gs1/software/python/3.2.3/bin/python3.2
import random
import argparse
import time
import json
import pycurl
import zipfile
from urllib.parse import urlencode
from io import BytesIO
from io import StringIO
import os

def parse_arguments():
	parser = argparse.ArgumentParser(description='Checks the status of an Ingenuity upload. Assumes API key and API secret are stored in conf.json.')
	parser.add_argument('-u', dest='status_url', type=str, help='status url')
	parser.add_argument('-c', dest='config_file', type=str, help='configuration file in JSON format')
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

def create_investigation_file(emails, samplename, i_file, s_a_file):
	fp = open(i_file, 'w')
	fp.write('Study Identifier\t'+samplename+'\n')
	fp.write('Study Title\t'+samplename+'\n')
	fp.write('Study File Name\t'+os.path.basename(s_a_file)+'\n')
	fp.write('Study Assay File Name\t'+os.path.basename(s_a_file)+'\n')
	fp.write('Study Person Email')
	for email in emails:
		fp.write('\t'+email)
	fp.write('\n')
	fp.close()

def create_study_assay_file(samplename, vcf_file, code, s_a_file):
	vcf_filename = os.path.basename(vcf_file)
	fp = open(s_a_file,'w')
	fp.write('Sample Name\tDerived Data File\tActivation Code\n')
	fp.write(samplename+'\t'+vcf_filename+'\t'+code+'\n')
	fp.close()

def create_package(vcf_file, s_a_file, i_file, z_file):
	with zipfile.ZipFile(z_file, 'w') as package:
		package.write(s_a_file, os.path.basename(s_a_file))	
		package.write(i_file, os.path.basename(i_file))
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
	response_dict = json.loads(body.decode())
	return response_dict

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

def main():
	args = parse_arguments()
	conf = load_json(args.config_file)
	token = get_access_token(conf['api_key_id'], conf['api_key_secret'])
	response_dict = check_status(args.status_url, token)
	print('Response from server:')
	print(json.dumps(response_dict,indent='\t'))

if __name__ == '__main__':
	main()
