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

def parse_arguments():
	parser = argparse.ArgumentParser(description='Upload a VCF file to Ingenuity. Assumes API key, API secret, activation code, and emails to share with are stored in conf.json.')
	parser.add_argument('-c', dest='config_file', type=str, help='configuration file in JSON format')
	parser.add_argument('-n', dest='sample_name', type=str, help='sample name')
	parser.add_argument('-i', dest='vcf_file', type=str, help='input VCF file to upload, accepts .vcf or .vcf.gz')
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
        assert(index != None)
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
        assert(index != None)
        col5 = patients_sheet.col(5)
        assert(col5[0].value == 'Patient details')
        description = col5[index].value
        return description, subject_id
    
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
		print('Upload complete. Response from server:')
		print(json.dumps(response_dict,indent='\t'))
	except ValueError:
		print('Could not parse server response as a JSON object. Response follows:')
		print(decoded_body)

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
        temp = '/tmp/'
        # Random filenames for temporary files
        suffix = str(int(random.random()*100000000))
        i_file = temp+'i_'+suffix+'.txt'
        s_a_file = temp+'s_a_'+suffix+'.txt'
        r_file = temp+'r_'+suffix+'.txt'
        z_file = temp+suffix+'.zip'
        vcf_file = args.vcf_file	
        conf = load_json(args.config_file)
        emails = conf['shared_emails']
        code = conf['activation_code']
        xlsx_file = conf['xlsx_file']
        description, subject_name = parse_excel(xlsx_file, args.sample_name)
        create_investigation_file(emails, args.sample_name, i_file, s_a_file)
        print('Created temporary file '+i_file)
        create_study_assay_file(args.sample_name, vcf_file, description, subject_name, code, s_a_file)
        print('Created temporary file '+s_a_file)
        create_request_file(args.sample_name, r_file)
        print('Created temporary file '+r_file)
        create_package(args.vcf_file, s_a_file, i_file, r_file, z_file)
        print('Created temporary file '+z_file)
        token = get_access_token(conf['api_key_id'], conf['api_key_secret'])
        print('Uploading package...')
        response_dict = upload_package(token, z_file)

# 	status_url = response_dict['status-url']
# 	print('{}% complete, {}, {}'.format(response_dict['percentage-complete'], response_dict['status'], response_dict['stage']))
# 	while response_dict['status'] != 'DONE' and response_dict['status'] != 'FAILED':
# 		time.sleep(5) 
# 		response_dict = check_status(status_url,token)
# 		if 'error' in response_dict.keys:
# 			if response_dict['error'] == 'invalid access token':
# 				token = get_access_token(conf['api_key_id'], conf['api_key_secret'])
# 			else:
# 				print(response_dict)
# 		print(response_dict)
# 		print('{}% complete, {}, {}'.format(response_dict['percentage-complete'], response_dict['status'], response_dict['stage']))
# 	if response_dict['status'] == 'DONE':
# 		print('Sample viewable at '+response_dict['results-url'])
# 	else:
# 		print(response_dict)
        os.remove(i_file)
        print('Removed temp file '+i_file)
        os.remove(s_a_file)
        print('Removed temp file '+s_a_file)
        os.remove(r_file)
        print('Removed temp file '+r_file)
        os.remove(z_file)	
        print('Removed temp file '+z_file)

if __name__ == '__main__':
	main()
