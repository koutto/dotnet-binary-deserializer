from lib import *
import time
import os
import base64


class RPCServer(object):

	def binary_to_xml(self, binary_data):
		"""
		RPC call .NET Binary --> XML
		"""
		print
		PrintUtils.print_title('Receive RPC call binary_to_xml')
		print
		tmp_filename = 'tmp_binary_{0}.raw'.format(str(time.time())[:-3])
		f = open(tmp_filename, 'w')
		PrintUtils.hexdump(base64.b64decode(binary_data))
		print
		f.write(base64.b64decode(binary_data))
		f.close()	

		#f = 	open(tmp_filename, 'r')
		# print f.read()
		# f.close()

		converter = Converter(tmp_filename)
		res = converter.scan_input_binary()

		os.remove(tmp_filename)

		if res:
			return base64.b64encode(converter.output)
		else:
			return False


	def xml_to_mcnbfs(self, xml_data):
		"""
		RPC call XML --> .NET Binary [MC-NBFS]
		"""
		print
		PrintUtils.print_title('Receive RPC call xml_to_mcnbfs')
		print
		tmp_filename = 'tmp_xml_{0}.raw'.format(str(time.time())[:-3])
		f = open(tmp_filename, 'w')
		print base64.b64decode(xml_data)
		print
		f.write(base64.b64decode(xml_data))
		f.close()

		converter = Converter(tmp_filename)
		res = converter.xml_to_mcnbfs()

		os.remove(tmp_filename)

		if res:
			return base64.b64encode(converter.output)
		else:
			return False


	def xml_to_mcnbfse(self, xml_data, nosizeprefix=False):
		"""
		RPC call XML --> .NET Binary [MC-NBFSE]
		"""
		print
		PrintUtils.print_title('Receive RPC call xml_to_mcnbfse')
		print
		tmp_filename = 'tmp_xml_{0}.raw'.format(str(time.time())[:-3])
		f = open(tmp_filename, 'w')
		base64.b64decode(xml_data)
		print
		f.write(base64.b64decode(xml_data))
		f.close()

		# tmp_filename2 = 'tmp_originalwcf_{0}.raw'.format(str(time.time())[:-3])
		# f = open(tmp_filename2, 'w')
		# f.write(base64.b64decode(original_wcf))
		# f.close()

		converter = Converter(tmp_filename)
		res = converter.xml_to_mcnbfse(nosizeprefix)
		
		os.remove(tmp_filename)
		#os.remove(tmp_filename2)

		if res:
			return base64.b64encode(converter.output)
		else:
			return False
