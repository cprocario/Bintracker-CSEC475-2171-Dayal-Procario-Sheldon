######
# md5-ify.py
#
# this script replies on the bintracker.py shell
# this script takes the files extracted from Bro, and 
# gets the MD5 hash of the CONTENT of the file, not the filename
# and pushes it to VirusTotal.
#
# the filename, hash, and scan_id of the file are then pushed to a CSV file
######

import os
import csv
from os import listdir
from os.path import isfile, join
import hashlib
import requests
import json
import sys
import time

md5hash_dict = {}
directory = "./extract_files/"

print "\nHashing extracted binaries"

myCsv = open('bintracker_results.csv', 'w')
if os.path.exists("./extract_files"):
	# for each file in the directory
	for f in listdir(directory):
		#if exists ./extract_files/<filename>
		if isfile(join(directory, f)):
			#concatenate the directory + filename
			file_name = join(directory, f)
			
			#get the hash of the file content, not filename
			#file content doesn't change, names can.
			hashed_file = hashlib.md5(open(file_name,'rb').read()).hexdigest()
			
			md5hash_dict[file_name] = hashed_file
			csvRow = f + ',' + hashed_file + '\n'
			myCsv.write(csvRow)

else:
	myCsv.close()
	print "Error loading extract_files directory. Verify bro script creates it, and is properly named"
	sys.exit(1)

myCsv.close()

#create a linked list with new scan_id attribute for CSV
all = []

#get api key from bintracker shell
api_key = sys.argv[1]

print "\nQuerying Virustotal's API, please be patient\n"

with open('bintracker_results.csv', 'r') as csvInput:
#	with open('bintracker_results.csv', 'w') as csvOutput:

		csvReader = csv.reader(csvInput)

		for row in csvReader:
			hashname = row[1]
			
			#create a virustotal API request
			params = {'apikey': api_key, 'resource': hashname}
			headers = {
				"Accept-Encoding": "gzip, deflate",
				"User-Agent" : "gzip,  My Python requests library example client or username"
			}
			response = requests.post('https://www.virustotal.com/vtapi/v2/file/rescan',params=params)
			# if success status code is returned
			if response.status_code == 200:
				json_response = response.json()
				# if a scan_id is returned
				if 'scan_id' in json_response:
					# if the scan_id isn't null
					if json_response['scan_id'] is not None:
						#put the scan_id in a new column
						scan_id = json_response['scan_id']
						row.append(scan_id)
						all.append(row)

					# otherwise put null in the column
					else:
						row.append('NULL')
						all.append(row)
				else:
					row.append('NULL')
					all.append(row)
			else:
				row.append('NULL')
				all.append(row)	

			#sleep to allow VirusTotal API to accept multiple files
			time.sleep(2)

# write the CSV 
with open('bintracker_results.csv', 'w') as csvOutput:
		csvWriter = csv.writer(csvOutput, lineterminator='\n')	
		csvWriter.writerows(all)
