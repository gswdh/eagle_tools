import xmltodict
import click
import json
import pandas as pd

def iterdict(d, path, part, paths):
	for k, v in d.items():
		if isinstance(v, dict):
			iterdict(v, path + ',' + str(k), part, paths)
		elif isinstance(v, list):
			path = path + ',' + str(k)
			for i in range(len(v)):
				iterdict(v[i], path + ',' + str(i), part, paths)
		else:
			if k == '@part' and v == part:
				paths.append((path+','+k).split(',')[1:])
	return paths


@click.command()
@click.option('--file', help='Eagle SCH file.')
@click.option('--part_id', help='Part identifier in schematic.')
@click.option('--csv', default='connections.csv', help='Output file name.')
def run(file, part_id, csv):

	# Get the XML of the sch
	with open(file, 'r') as f:
		xml_str = f.read()
	xml = xmltodict.parse(xml_str)

	# Go through the dict to find the paths to the value of part_id
	paths = []
	paths = iterdict(xml, '', part_id, paths)

	# Get all the nets connected to the symbol pins
	part_connections = {}
	for path in paths:
		bit = xml
		for step in path:
			try:
				step = int(step)
			except:
				pass
			# Progress through the dict
			try:
				bit = bit[step]
			except:
				pass
			else:
				# Check for the info we want
				if type(bit) == dict:
					if '@name' in bit.keys():
						pin_name = bit['@name']

					if '@pin' in bit.keys():
						part_connections[bit['@pin']] = pin_name
						break

	# Get the deviceset name
	parts = xml['eagle']['drawing']['schematic']['parts']['part']

	deviceset_name = ''
	for part in parts:
		if part['@name'] == part_id:
			deviceset_name = part['@deviceset']
			print(f"Found deviceset {deviceset_name}")
			break

	# Get the package numbers for the device symbol
	package_connections = {}
	libraries = xml['eagle']['drawing']['schematic']['libraries']['library']

	for library in libraries:
		print(library)
		for deviceset in library['devicesets']['deviceset']:
			if type(deviceset) == dict:
				if deviceset['@name'] == deviceset_name:
					connections = deviceset['devices']['device']['connects']['connect']
					for connection in connections:
						package_connections[connection['@pin']] = connection['@pad']
						print(f"Found connection {connection['@pin']}, {connection['@pad']}")

	# Print all the connections
	df = pd.DataFrame(columns=['connection', 'net', 'pin'])
	for key in package_connections.keys():
		try:
			net = part_connections[key]
		except:
			net = ''
		df.loc[len(df)] = [key, net, package_connections[key]]

	# Output to CSV
	df.to_csv(csv, index=False)
			
if __name__ == '__main__':
	run()


