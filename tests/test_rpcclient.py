import xmlrpclib
import base64
from lib import PrintUtils

WCFBIN_MCNBFS_RAW = 'TODEFINE'
WCFBIN_MCNBFSE_RAW = 'TODEFINE'
DESERIALIZED_DATA_MCNBF = 'TODEFINE'
DESERIALIZED_DATA_MCNBFSE = 'TODEFINE'

s = xmlrpclib.ServerProxy('http://localhost:8000')

print s.system.listMethods()

print
PrintUtils.print_title('Test .NET binary [MC-NBFS] --> XML')
f = open(WCFBIN_MCNBFS_RAW, 'r')
netbin_data = f.read()
f.close()

output = s.binary_to_xml(base64.b64encode(netbin_data))

if not output:
	PrintUtils.print_error('Conversion failed')
else:
	PrintUtils.print_success('Conversion OK')
	print base64.b64decode(output)
	#print 
	#PrintUtils.hexdump(output)


# =============================================================================

print
PrintUtils.print_title('Test .NET binary [MC-NBFSE] --> XML')
f = open(WCFBIN_MCNBFSE_RAW, 'r')
netbin_data = f.read()
f.close()

output = s.binary_to_xml(base64.b64encode(netbin_data))

if not output:
	PrintUtils.print_error('Conversion failed')
else:
	PrintUtils.print_success('Conversion OK')
	print base64.b64decode(output)
	#print 
	#PrintUtils.hexdump(output)


# =============================================================================	


print
PrintUtils.print_title('Test XML --> .NET Binary [MC-NBFS]')
f = open(DESERIALIZED_DATA_MCNBFS, 'r')
xml_data = f.read()
f.close()

output = s.xml_to_mcnbfs(base64.b64encode(xml_data))

if not output:
	PrintUtils.print_error('Conversion failed')
else:
	PrintUtils.print_success('Conversion OK')
	PrintUtils.hexdump(base64.b64decode(output))


# =============================================================================	


print
PrintUtils.print_title('Test XML --> .NET Binary [MC-NBFSE] #1')
f = open(DESERIALIZED_DATA_MCNBFSE, 'r')
xml_data = f.read()
f.close()

output = s.xml_to_mcnbfse(base64.b64encode(xml_data))

if not output:
	PrintUtils.print_error('Conversion failed')
else:
	PrintUtils.print_success('Conversion OK')
	PrintUtils.hexdump(base64.b64decode(output))



