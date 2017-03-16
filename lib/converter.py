import os
import re
import regex
import traceback
import collections
from colorama import *
from lib import *
from lib.dictionary import *


class Converter(object):

	def __init__(self, filename, begin_offset=0):
		self.filename = filename.strip()
		self.length = os.stat(filename).st_size
		self.begin_offset = begin_offset
		self.input  = open(self.filename, 'r').read()[self.begin_offset:]
		self.output = ''


	def scan_input_binary(self):
		"""
		Scan input (file) for .NET Binary data to decode.
		Basically, try to decode by calling self.binary_to_xml() at each offset of the input till it succeeds.
		"""
		#with open(self.filename, 'r') as f:
		#	if f.read().find('\x56\x02\x0B') < 0:
		#		PrintUtils.print_error('No start tag <s:Envelope> found (56 02 0B)')
		#		return False

		for i in range(self.length):
			# Try WCF binary decoding from the current offset
			if self.binary_to_xml(i):
				return True
		PrintUtils.print_error('Unable to find valid WCF binary into input')
		return False


	def binary_to_xml(self, offset):
		"""
		Decode .NET Binary data to XML
		Support for [MC-NBFX],[MC-NBFS] and [MC-NBFSE] formats
		"""
		fp = open(self.filename, 'r')
		fp.read(self.begin_offset+offset)
		data = fp.read()
		fp.close()


		start_envelope = data.find('\x56\x02\x0B')
		if start_envelope > 0:
			# In that case, should follow [MC-NBFSE] specs, i.e. uses StringTable (in-band dictionary)
			# In that case, packets are built as follow:
			# [size of in-band elements (7bit-int)][in-band elements][56 02 0B .... .NET Binary content]
			(size_marked, l) = Net7BitInteger.decode7bit(data)
			if size_marked+l != start_envelope:
				# If here it means that in-band elements are not prefixed by its size
				l = 0
				PrintUtils.print_info('In-band dictionary not prefixed by its size')
			# Extraction of in-band elements
			inband_elements = self.extract_inband_elements(data[l:start_envelope])
		else:
			# [MC-NBFS] if start_envelope == 0
			# [MC-NBFX] if start_envelope == -1 (pattern not found)
			start_envelope = 0

		try:
			# Decoding
			fp = open(self.filename, 'r')
			fp.read(self.begin_offset+offset+start_envelope)
			records = Record.parse(fp)
			fp.close()
			output = ['']
			print_records(records, output=output, fp_enabled=False)
			self.output = output[0]

			# Format [MC-NBFSE]
			if start_envelope > 0:
				if len(inband_elements) > 0:
					# Build partial StringTable and replace [[VALUE_0x..] in decoded message when possible
					partial_stringtable = self.build_partial_stringtable(inband_elements)
					self.replace_reference_stringtable(partial_stringtable)


				PrintUtils.print_success('.NET Binary data - Format [MC-NBFSE] (with in-band dictionary) - '
					'decoded with success from offset 0x{0:X}'.format(self.begin_offset+offset))
				PrintUtils.print_info('In-band dictionary (partial StringTable):')
				PrintUtils.print_info('.   offsets= 0x{0:X}-0x{1:X} | len= 0x{2:X} bytes'.format(self.begin_offset+offset, 
					self.begin_offset+offset+start_envelope, start_envelope))
				for i in partial_stringtable:
					PrintUtils.print_info('.   [0x{0:02X}] {1}'.format(i, partial_stringtable[i]))
			# Format [MC-NBFS]
			else:
				PrintUtils.print_success('.NET Binary data - Format [MC-NBFS] - decoded with success '
					'from offset 0x{0:X}'.format(self.begin_offset+offset))
			print

			# Print decoded data
			PrintUtils.print_delimiter()

			print self.output
			#PrintUtils.print_xml_highlighted(self.emphasize_stringtable_elements(self.output))
			PrintUtils.print_delimiter()
			print

			# Legend
			PrintUtils.print_info('References to StringTable elements:')
			PrintUtils.print_info('.   [[VALUE_0xXX]]    refers to unknown value in StringTable')
			PrintUtils.print_info('.   [[XXXXX|ST_0xXX]] refers to known value in StringTable (extracted from in-band elements)')
			print 
			PrintUtils.print_info('Output length = {0} chars'.format(len(self.output)))

			return True		
		except Exception as e:
			#traceback.print_exc()
			return False


	def xml_to_mcnbfs(self, display=True):
		"""
		Encode XML into .NET Binary in standard format [MC-NBFS]
		"""
		try:
			r = XMLParser.parse(self.input)
			data = dump_records(r)
			self.output = data
			if display:
				PrintUtils.print_success('XML converted into .NET Binary in format [MC-NBFS] with success')
				PrintUtils.print_delimiter()
				PrintUtils.hexdump(data)
				PrintUtils.print_delimiter()
				PrintUtils.print_info('Output length = {0} bytes'.format(len(self.output)))
			return True
		except Exception as e:
			traceback.print_exc()
			if display:
				PrintUtils.print_error('An error occured during conversion. Probably invalid XML data.')
			return False


	def xml_to_mcnbfse(self, nosizeprefix):
		"""
		Encode XML into .NET Binary in format [MC-NBFSE]
		"""

		# Extract in-band dictionary from xml and produce binary 
		inband_dictionary = self.extract_inband_dictionary_from_xml()
		binary_inband = self.inband_dictionary_to_binary_format(inband_dictionary, nosizeprefix)
		#print inband_dictionary
		#print binary_inband
		PrintUtils.print_success('In-band dictionary extracted from XML (partial StringTable):')
		for index in inband_dictionary:
			PrintUtils.print_info('.   [0x{0:02X}] {1}'.format(index, inband_dictionary[index]))
		print
		PrintUtils.print_info('In-band dictionary (partial StringTable) Hexdump:')
		if not nosizeprefix:
			PrintUtils.print_info('Note: It is prefixed by its size in 7-Bit Integer format (default)')
		else:
			PrintUtils.print_info('Note: It is NOT prefixed by its size')
		print
		PrintUtils.hexdump(binary_inband)	
		print

		# Convert XML to .NET Binary
		if not self.xml_to_mcnbfs(False):
		 	PrintUtils.print_error('An error occured during conversion. Probably invalid XML data.')
		 	return False

		# Concatenate in-band dictionary + .NET Binary standard [MC-NBFS] => .NET Binary [MC-NBFSE]
		self.output = binary_inband + self.output

		PrintUtils.print_success('XML converted into .NET Binary with success')
		PrintUtils.print_delimiter()
		PrintUtils.hexdump(self.output)
		PrintUtils.print_delimiter()
		PrintUtils.print_info('Output length = {0} bytes'.format(len(self.output)))

		# Extract StringTable from original packet
		# f = open(original_packet, 'r')
		# data_original_packet = f.read()
		# f.close()

		# start_envelope = data_original_packet.find('\x56\x02\x0B')
		# if start_envelope < 0:
		# 	PrintUtils.print_error('No start tag <s:Envelope> found (56 02 0B) in original packet.')
		# 	return False
		# elif start_envelope == 0:
		# 	PrintUtils.print_error('Start tag <s:Envelope> (56 02 0B) found at offset 0. Indicates that original ' \
		# 		'packet does not contain in-band dictionary')
		# 	return False

		# string_table = data_original_packet[0:start_envelope]
		# PrintUtils.print_info('In-band dictionary extracted from original packet: offsets= 0x{0:X}-0x{1:X} ' \
		# 	'| len= 0x{2:X} bytes'.format(0, start_envelope, start_envelope))
		# PrintUtils.print_info('In-band dictionary (partial StringTable) Hexdump:')
		# print
		# PrintUtils.hexdump(string_table)	
		# print

		# # Convert XML to .NET Binary
		# # Trick used: xxxVALUE_0xNNxxx are added into the dictionary, for odd index
		# if not self.xml_to_mcnbfs(False):
		# 	PrintUtils.print_error('An error occured during conversion. Probably invalid XML data.')
		# 	return False

		# # Concatenate StringTable + WCF binary standard => WCF binary with in-band dictionary
		# self.output = string_table + self.output

		# PrintUtils.print_success('XML converted into WCF binary with success')
		# PrintUtils.print_delimiter()
		# PrintUtils.hexdump(self.output)
		# PrintUtils.print_delimiter()
		return True



	def extract_inband_elements(self, data):
		"""
		Extract in-band elements transmitted into the packet.
		Those elements are used to update the StringTable kept in memory at client and server sides.
		"""
		i = 0
		elements = []
		while i < len(data):
			next_len = int(data[i].encode('hex'), 16)
			elements.append(data[i+1:i+1+next_len])
			i = i+1+next_len

		return elements


	def build_partial_stringtable(self, inband_elements):
		"""
		Use extracted in-band elements to populate partial StringTable with correct index
		"""
		# Find reference max index into decoded data
		max_index = 1
		regex = re.compile(r'\[\[VALUE_0x([0-9a-fA-F]+)\]\]')
		for match in regex.finditer(self.output):
			if int(match.group(1), 16) > max_index:
				max_index = int(match.group(1), 16)

		# Compute beginning index of partial StringTable
		begin_index = max_index - (len(inband_elements)-1)*2

		# Build partial StringTable
		partial_stringtable = collections.OrderedDict()
		for i in range(begin_index, max_index+1, 2):
			partial_stringtable[i] = inband_elements.pop(0)

		return partial_stringtable


	def replace_reference_stringtable(self, partial_stringtable):
		"""
		Replace reference to elements in StringTable when it is known.
		Format : [[xxxx|ST_0xxx]]
		"""
		for index in partial_stringtable.keys():
			self.output = self.output.replace('[[VALUE_0x%02x]]' % index, '[[%s|ST_0x%02x]]' % (partial_stringtable[index], index))
		return


	def emphasize_stringtable_elements(self, xml):
		"""
		Put reference to StringTable elements into XML in strong
		"""
		regex 	= re.compile(r'\[\[VALUE_0x(?P<number>[0-9A-Fa-f]+)\]\]')
		xml 	= re.sub(regex, Style.BRIGHT + '[[VALUE_0x\g<number>]]' + Style.RESET_ALL, xml)
		regex 	= re.compile(r'ST_0x(?P<number>[0-9A-Fa-f]+)\]\]')
		xml 	= re.sub(regex, Style.BRIGHT + 'ST_0x\g<number>' + Style.RESET_ALL + ']]', xml)
		return xml


	def extract_inband_dictionary_from_xml(self):
		"""
		Extract known elements from StringTable that are inside the XML
		They must respect the syntax [[VALUE|ST_0xXX]]
		Those elements are aimed at being converted in binary
		"""
		inband_dictionary = {}

		# Find all reference to in-band dictionary into xml
		regex = re.compile(r'\[\[(.*?)\|ST_0x([0-9a-fA-F]+)\]\]')
		for match in regex.finditer(self.input):
			inband_dictionary[int(match.group(2), 16)] = match.group(1)

		# Replace [[VALUE|ST_0xXX]] by [[VALUE_0xXX]] into xml
		regex = re.compile(r'\[\[(?P<value>.)*?\|ST_0x(?P<number>[0-9a-fA-F]+)\]\]')
		self.input = re.sub(regex, '[[VALUE_0x\g<number>]]', self.input)

		#print self.input
		return inband_dictionary


	def inband_dictionary_to_binary_format(self, inband_dictionary, nosizeprefix):
		"""
		Convert in-band dictionary (previously extracted from XML) in binary format.
		Resulting binary data is aimed at being prefixed to .NET Binary data
		"""
		length = 0
		for index in inband_dictionary.keys():
			length += 1+len(inband_dictionary[index])

		binary = bytearray(length)
		i = 0
		list_index = inband_dictionary.keys()
		list_index.sort()
		for index in list_index:
			binary[i] = len(inband_dictionary[index])
			i += 1
			for c in inband_dictionary[index]:
				binary[i] = c
				i += 1

		# Prefix in-band dictionary with its size in 7-Bit Integer format,
		# unless nosizeprefix == True
		if not nosizeprefix:
			binary = Net7BitInteger.encode7bit(length) + binary

		return binary